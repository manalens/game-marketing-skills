#!/usr/bin/env python3
"""Check the press and creator outreach tracker written by the press-outreach skill.

Reads marketing/outreach/contacts.csv (or the path you give). Never sends anything.

Fails (exit 1) when:
  - a required column is missing: name, outlet, contact, audience, similar_games, status,
    sent_date, follow_up_date, key_sent, coverage_url, utm_content;
  - a contact is not a valid email address or an https link (a contact form or Twitch page);
  - the same contact, or the same name at the same outlet, appears twice;
  - utm_content is empty, not a lower-case name with underscores (or a YYYY-MM-DD-... post ID),
    or used twice (except --shared values);
  - a status is unknown, a date is not YYYY-MM-DD, a sent row has no sent_date, or the follow-up
    is not after the sent date;
  - a key went to a contact with no contact_source (where the business email was verified), or a
    real-looking Steam key is pasted into the sheet;
  - a link column value does not carry its own utm_content, utm_source and utm_campaign, has a
    tag value that is not lower case, or a utm_medium other than social, video, email or paid;
  - with --coverage: a coverage row names a utm_content not in the tracker, or has no URL.

Prints, without failing (unless --strict):
  - follow-ups due today or overdue (status sent, follow_up_date <= today);
  - keys sent more than --key-days days ago with no coverage URL yet.
"""
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REQUIRED = ["name", "outlet", "contact", "audience", "similar_games", "status", "sent_date",
            "follow_up_date", "key_sent", "coverage_url", "utm_content"]
RECOMMENDED = ["type", "contact_source", "key_batch", "link"]
STATUSES = {"todo", "drafted", "sent", "followed-up", "replied", "declined", "covered", "no-reply"}
SENT = {"sent", "followed-up", "replied", "declined", "covered", "no-reply"}
DONE = {"replied", "declined", "covered"}
EMAIL = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
# docs/LINKS.md: names use underscores; a post ID keeps its hyphens.
SLUG = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$|^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$")
MEDIUMS = {"social", "video", "email", "paid"}
STEAM_KEY = re.compile(r"\b[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}\b")
FREE_MAIL = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com",
             "proton.me", "protonmail.com", "mail.ru", "yandex.ru", "aol.com", "gmx.com"}


def date(value):
    value = (value or "").strip()
    if not value:
        return None
    return dt.date.fromisoformat(value)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tracker", type=Path, nargs="?", default=Path("marketing/outreach/contacts.csv"))
    p.add_argument("--today", help="YYYY-MM-DD, default: today")
    p.add_argument("--key-days", type=int, default=14,
                   help="days after a key with no coverage before it is listed (default 14)")
    p.add_argument("--shared", default="creators_small",
                   help="comma-separated utm_content values allowed on several rows (default creators_small)")
    p.add_argument("--coverage", type=Path, help="coverage log CSV to check against the tracker")
    p.add_argument("--strict", action="store_true", help="also fail when follow-ups or key checks are due")
    args = p.parse_args()

    if not args.tracker.exists():
        sys.exit(f"{args.tracker}: not found")
    today = date(args.today) if args.today else dt.date.today()
    shared = {s.strip() for s in args.shared.split(",") if s.strip()}

    with args.tracker.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = [c.strip() for c in (reader.fieldnames or [])]
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]

    errors, warnings, due, stale = [], [], [], []
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        sys.exit(f"{args.tracker}: missing column(s) {', '.join(missing)}")
    for c in RECOMMENDED:
        if c not in cols:
            warnings.append(f"no '{c}' column (recommended)")

    seen_contact, seen_name, seen_utm = {}, {}, {}
    for n, r in enumerate(rows, 2):
        where = f"row {n} ({r['name'] or '?'})"
        if not r["name"]:
            errors.append(f"{where}: no name")
        contact = r["contact"]
        is_email = "@" in contact and not contact.startswith("http")
        if not contact:
            errors.append(f"{where}: no contact")
        elif is_email and not EMAIL.match(contact):
            errors.append(f"{where}: '{contact}' does not look like an email address")
        elif not is_email and not contact.startswith("https://"):
            errors.append(f"{where}: contact must be an email or an https link, got '{contact}'")

        key = contact.lower()
        if key and key in seen_contact:
            errors.append(f"{where}: same contact as row {seen_contact[key]}")
        seen_contact.setdefault(key, n)
        nk = (r["name"].lower(), r["outlet"].lower())
        if r["name"] and nk in seen_name:
            errors.append(f"{where}: same name and outlet as row {seen_name[nk]}")
        seen_name.setdefault(nk, n)

        utm = r["utm_content"]
        if not utm:
            errors.append(f"{where}: no utm_content")
        elif not SLUG.match(utm):
            errors.append(f"{where}: utm_content '{utm}' must be lower case with underscores, such as cozy_weekly_sam")
        elif utm in seen_utm and utm not in shared:
            errors.append(f"{where}: utm_content '{utm}' already used on row {seen_utm[utm]}")
        seen_utm.setdefault(utm, n)

        status = r["status"].lower()
        if status not in STATUSES:
            errors.append(f"{where}: status '{r['status']}' is not one of {', '.join(sorted(STATUSES))}")
        parsed = {}
        for col in ("sent_date", "follow_up_date", "key_sent"):
            val = r[col]
            if col == "key_sent" and val.lower() in ("", "no"):
                val = ""
            try:
                parsed[col] = date(val)
            except ValueError:
                errors.append(f"{where}: {col} '{r[col]}' is not a date; use YYYY-MM-DD")
                parsed[col] = None
        sent, follow, key_date = parsed["sent_date"], parsed["follow_up_date"], parsed["key_sent"]
        if status in SENT and not sent:
            errors.append(f"{where}: status '{status}' but no sent_date")
        if sent and follow and follow <= sent:
            errors.append(f"{where}: follow_up_date {follow} is not after sent_date {sent}")
        if status == "sent" and follow and follow <= today:
            late = (today - follow).days
            due.append(f"{r['name']} ({r['outlet']}): follow-up {'due today' if late == 0 else f'{late} day(s) overdue'}")

        for col, val in r.items():
            if STEAM_KEY.search(val or ""):
                errors.append(f"{where}: column '{col}' looks like a Steam key; log the batch name, not the key")
        if key_date:
            if not r.get("contact_source"):
                errors.append(f"{where}: key sent but no contact_source; send keys only to the business "
                              "email published on the channel or outlet page, and note where it was")
            if is_email and contact.split("@")[-1].lower() in FREE_MAIL:
                warnings.append(f"{where}: key sent to a free mail address; check it is the one on the channel page")
            age = (today - key_date).days
            if age >= args.key_days and not r["coverage_url"] and status not in ("declined", "covered"):
                stale.append(f"{r['name']} ({r['outlet']}): key sent {age} day(s) ago, no coverage yet")

        if r["coverage_url"] and not r["coverage_url"].startswith("http"):
            errors.append(f"{where}: coverage_url is not a link")
        link = r.get("link", "")
        if link:
            q = parse_qs(urlparse(link).query)
            if q.get("utm_content", [""])[0] != utm:
                errors.append(f"{where}: link utm_content is '{q.get('utm_content', [''])[0]}', expected '{utm}'")
            for k in ("utm_source", "utm_campaign"):
                if not q.get(k):
                    errors.append(f"{where}: link has no {k}")
            for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content"):
                v = q.get(k, [""])[0]
                if v != v.lower():
                    errors.append(f"{where}: link {k} '{v}' must be lower case")
            medium = q.get("utm_medium", [""])[0]
            if "utm_medium" in q and medium not in MEDIUMS:
                errors.append(f"{where}: link utm_medium '{medium}' must be one of {', '.join(sorted(MEDIUMS))}")

    if args.coverage:
        if not args.coverage.exists():
            errors.append(f"{args.coverage}: not found")
        else:
            with args.coverage.open(newline="", encoding="utf-8") as f:
                cov = list(csv.DictReader(f))
            for n, r in enumerate(cov, 2):
                u = (r.get("utm_content") or "").strip()
                if u not in seen_utm:
                    errors.append(f"{args.coverage.name} row {n}: utm_content '{u}' is not in the tracker")
                if not (r.get("url") or "").startswith("http"):
                    errors.append(f"{args.coverage.name} row {n}: no URL")

    for w in warnings:
        print(f"warning: {w}")
    if due:
        print(f"\nFollow-ups due ({today}):")
        for d in due:
            print(f"  - {d}")
    if stale:
        print(f"\nKeys with no coverage after {args.key_days} days:")
        for s in stale:
            print(f"  - {s}")
    for e in errors:
        print(f"error: {e}")
    if errors or (args.strict and (due or stale)):
        print(f"\n{len(errors)} error(s), {len(due)} follow-up(s) due, {len(stale)} key(s) without coverage")
        sys.exit(1)
    print(f"\nok: {len(rows)} contacts, {len(due)} follow-up(s) due, {len(stale)} key(s) without coverage")


if __name__ == "__main__":
    main()
