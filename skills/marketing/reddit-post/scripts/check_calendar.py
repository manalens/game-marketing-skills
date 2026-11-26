#!/usr/bin/env python3
"""Check a Reddit posting calendar (marketing/reddit/tracker.csv).

Columns: date,slot,subreddit,post_id,clip,title,flair,status,url,notes
(date is YYYY-MM-DD; slot is A, B or C; C rows are comments only and are not counted as posts).

Fails (exit 1) when:
  - a subreddit gets two posts closer than its gap (from --subs, else 14 days; --gap r/sub=14 overrides)
  - a post falls on a weekday the subreddit does not allow (allowed_days in --subs)
  - a post goes to a subreddit whose promo_allowed is "no" or "threads-only"
  - one clip is used in two subreddits on the same day
  - a day has more than --max-per-day posts (default 2)
  - an A or B row has no post_id, or its post_id is not a Reddit post ID (YYYY-MM-DD-rd-slug)
Rows with status "skipped" or "removed" are ignored for spacing. Rows with status "posted" are
history: they count for spacing, but a problem among posted rows alone is printed as a note, not
an error, since it cannot be changed any more.
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

DEFAULT_SUBS = Path(__file__).resolve().parent.parent / "references" / "subreddits.csv"
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
POST_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-rd-[a-z0-9-]+$")


def parse_gap(s):
    sub, _, days = s.partition("=")
    if not sub or not days.isdigit():
        raise argparse.ArgumentTypeError("use r/sub=DAYS")
    return sub.lower(), int(days)


def load_subs(path):
    subs = {}
    if path and path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row.get("subreddit", "").strip().lower()
                if name:
                    subs[name if name.startswith("r/") else "r/" + name] = row
    return subs


def weekdays(text):
    t = (text or "").strip().lower()
    if not t or t == "any":
        return None
    out = {i for part in t.replace(";", ",").split(",") if part.strip()
           for i, d in enumerate(DAYS) if d.startswith(part.strip()[:3])}
    return out or None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tracker", type=Path)
    p.add_argument("--default-gap", type=int, default=14)
    p.add_argument("--gap", type=parse_gap, action="append", default=[], help="r/sub=DAYS (repeat)")
    p.add_argument("--max-per-day", type=int, default=2)
    p.add_argument("--subs", type=Path, default=DEFAULT_SUBS, help="subreddit list CSV (default: references/subreddits.csv)")
    args = p.parse_args()

    if not args.tracker.exists():
        sys.exit(f"{args.tracker}: not found")
    subs = load_subs(args.subs)
    gaps = {k: int(v["gap_days"]) for k, v in subs.items() if (v.get("gap_days") or "").strip().isdigit()}
    gaps.update(dict(args.gap))

    errors = []
    notes = []
    posts = []
    with args.tracker.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = {"date", "slot", "subreddit", "post_id", "clip", "status"} - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"{args.tracker}: missing columns {sorted(missing)}")
        for n, row in enumerate(reader, start=2):
            if row["slot"].strip().upper() == "C":
                continue
            if row["status"].strip().lower() in {"skipped", "removed"}:
                continue
            try:
                d = date.fromisoformat(row["date"].strip())
            except ValueError:
                errors.append(f"line {n}: bad date '{row['date']}'")
                continue
            sub = row["subreddit"].strip().lower()
            if not sub.startswith("r/"):
                sub = "r/" + sub
            pid = row["post_id"].strip()
            done = row["status"].strip().lower() == "posted"
            if done:
                posts.append((d, sub, row["clip"].strip(), n, done))
                continue
            if not POST_ID.match(pid):
                errors.append(f"line {n}: post_id '{pid}' is not YYYY-MM-DD-rd-slug (docs/LINKS.md)")
            info = subs.get(sub, {})
            promo = (info.get("promo_allowed") or "").strip().lower()
            if promo in {"no", "threads-only"}:
                errors.append(f"line {n}: {sub} promo_allowed is '{promo}'; use its weekly thread (slot C) instead")
            allowed = weekdays(info.get("allowed_days"))
            if allowed is not None and d.weekday() not in allowed:
                errors.append(f"line {n}: {sub} allows posts on {info['allowed_days']} only, not {DAYS[d.weekday()].title()}")
            posts.append((d, sub, row["clip"].strip(), n, done))

    by_sub = defaultdict(list)
    by_day = defaultdict(list)
    for d, sub, clip, n, done in posts:
        by_sub[sub].append((d, n, done))
        by_day[d].append((sub, clip, n, done))

    for sub, items in by_sub.items():
        items.sort()
        gap = gaps.get(sub, args.default_gap)
        for (d1, n1, done1), (d2, n2, done2) in zip(items, items[1:]):
            if (d2 - d1).days < gap:
                (notes if done1 and done2 else errors).append(
                    f"{sub}: lines {n1} and {n2} are {(d2 - d1).days} days apart, gap is {gap}")

    for d, items in sorted(by_day.items()):
        history = all(done for *_, done in items)
        if len(items) > args.max_per_day:
            (notes if history else errors).append(f"{d}: {len(items)} posts, max {args.max_per_day}")
        clips = defaultdict(set)
        for sub, clip, n, done in items:
            if clip:
                clips[clip].add(sub)
        for clip, subs in clips.items():
            if len(subs) > 1:
                (notes if history else errors).append(f"{d}: clip {clip} in {len(subs)} subreddits ({', '.join(sorted(subs))})")

    for e in notes:
        print(f"{args.tracker}: note (posted already): {e}")
    for e in errors:
        print(f"{args.tracker}: {e}")
    if errors:
        sys.exit(1)
    print(f"{args.tracker}: ok ({len(posts)} posts, {len(by_sub)} subreddits)")


if __name__ == "__main__":
    main()
