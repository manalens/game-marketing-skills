#!/usr/bin/env python3
"""Find festivals, showcases, Steam events and sales a game can enter, from references/events.csv.

Commands:
  find       filter by game status, tags, studio region, team, cost and a date window, rank the
             matches and write <out-dir>/events.md and <out-dir>/events.csv.
  deadlines  list submission and registration deadlines in the next N days (same filters, all
             optional).
  validate   check the bundled table (every row has a source and a checked date, dates are real)
             or, with --output, a written events.csv. Exits 1 on any problem.

Examples:
  events.py find --status demo --tags "Cozy,Farming Sim,Life Sim" --region eu --launch 2027-09-15
  events.py deadlines --days 45 --status unreleased
  events.py validate
  events.py validate --output launch/events.csv

Matching follows the Manalens fest finder: a themed event needs one of your tags to match its
theme tags; region and team rules must fit; release rules (unreleased, demo, released) must fit.
Valve rules: Next Fest once per game, and the game must not release before it ends; a seasonal
sale discount needs release at least 30 days before the start. Dates are ISO (YYYY-MM-DD).
"""
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

TABLE = Path(__file__).resolve().parent.parent / "references" / "events.csv"
COLS = ["id", "name", "organizer", "type", "start", "end", "usual_month", "deadline", "deadline_basis",
        "release_rule", "tags", "theme", "regions", "region_note", "identity", "cost", "cost_note", "apply",
        "prepare", "source", "checked", "notes"]
OUT_COLS = ["rank", "group", "name", "organizer", "type", "start", "end", "deadline", "deadline_basis", "days_left",
            "matched_tags", "entry", "cost", "prepare", "why", "apply", "source", "checked"]
REGIONS = ["global", "na", "eu", "apac", "mena-africa", "latam"]
IDENTITIES = ["poc", "black", "latinx", "women", "lgbtq", "disabled", "asian", "indigenous"]
POC = {"poc", "black", "latinx", "asian", "indigenous"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
RELEASE_TEXT = {"unreleased": "unreleased games only", "demo": "playable demo or build required",
                "released": "released games only", "any": "released or unreleased",
                "unreleased-demo": "unreleased, public demo at the start, once per game", "": "release rule not stated"}


def iso(text):
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        sys.exit(f"error: '{text}' is not a date in YYYY-MM-DD form")


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in ("start", "end", "deadline"):
            r[k + "_d"] = dt.date.fromisoformat(r[k]) if r.get(k) else None
    return rows


def tag_matches(fest_tags, tags):
    keys = [t.strip().lower() for t in fest_tags.split(";") if t.strip()]
    return [t for t in tags if any(re.search(r"(^|[^a-z])" + re.escape(k), t.lower()) for k in keys)]


def blocker(r, a):
    """Why the game cannot enter, or None."""
    if r["regions"]:
        allowed = r["regions"].split(";")
        if a.region not in allowed:
            return f"for studios in {r['region_note'] or ', '.join(allowed)}"
    if r["identity"]:
        team = set(a.team)
        if not (r["identity"] in team or (r["identity"] == "poc" and team & POC)):
            return f"for {r['identity']}-led teams"
    rule, st = r["release_rule"], a.status
    if rule == "unreleased" and st == "released":
        return "unreleased games only"
    if rule == "released" and st != "released" and r["type"] != "Valve seasonal sale":
        return "released games only"
    if rule == "demo" and st == "unreleased":
        return "needs a playable demo or build"
    if a.free_only and r["cost"] == "paid":
        return "costs money to enter" + (f" ({r['cost_note']})" if r["cost_note"] else "")
    if a.online_only and r["type"] == "In-person":
        return "in-person event"
    return None


def evaluate(r, a, today):
    """Return (row dict for output) or (None, reason)."""
    why, score = [], 0.0
    if a.status:
        b = blocker(r, a)
        if b:
            return None, b
    matched = tag_matches(r["tags"], a.tags) if r["tags"] else []
    if r["tags"] and not matched:
        return None, f"theme: {r['theme'] or r['tags']}; none of your tags match"
    if matched:
        score += 2 * len(matched)
        why.append(f"tags {', '.join(matched)} match the theme ({r['theme'] or r['tags'].replace(';', ', ')})")
    if r["regions"]:
        if r["region_note"]:
            # The note names a narrower area than the region code (one country, one sub-region):
            # an "apac" studio is not always eligible, so no rank boost; ask the user to check.
            why.append(f"region rule: {r['region_note']} (check that your studio qualifies)")
        else:
            score += 2
            why.append(f"region fits: {r['regions']}")
    if r["identity"]:
        score += 2
        why.append(f"team fits: {r['identity']}-led")
    if r["cost"] == "free":
        score += 0.5
    launch = a.launch
    kind = r["type"]
    if kind == "Valve Next Fest":
        if a.status == "released" or a.in_next_fest_before:
            return None, "Next Fest is for unreleased games, once per game"
        if launch and r["end_d"] and r["end_d"] >= launch:
            return None, f"ends {r['end']}, on or after your launch; the game must not release before it ends"
        if a.status == "unreleased":
            why.append("needs a public demo when the fest starts")
        why.append("one Next Fest per game: pick one edition")
    if kind == "Valve seasonal sale":
        last = r["deadline_d"]
        if a.status == "released":
            if launch and last and launch > last:
                return None, f"you release after {r['deadline']}, inside the 30-day cooldown: full price only"
            why.append("released game: enter a discount in Discount Management, no registration")
        elif launch and last:
            if launch > last:
                return None, f"launch {launch} is after {r['deadline']}: no discount in this sale"
            why.append(f"fits if you release on or before {r['deadline']}")
        elif r["start_d"]:
            why.append(f"only if you release on or before {r['deadline']}")
    if kind == "Valve themed fest" and launch and r["start_d"]:
        if r["end_d"] < launch:
            why.append("before your launch: join as Coming Soon, brings wishlists not sales")
        elif (r["start_d"] - launch).days < 30:
            why.append("within 30 days of launch: full price only (Valve cooldown)")
    # window
    ref = r["start_d"] or r["deadline_d"]
    if ref and not (a.date_from <= ref <= a.date_to) and not (r["deadline_d"] and a.date_from <= r["deadline_d"] <= a.date_to):
        return None, "outside your date window"
    if not ref and r["usual_month"]:
        why.append(f"usually runs in {MONTHS[int(r['usual_month']) - 1]}; next date not published")
    elif not ref:
        why.append("no date published; watch the source page")
    over = (r["deadline_d"] and r["deadline_d"] < today) or (r["end_d"] and r["end_d"] < today)
    if r["deadline_d"] and not over:
        days_left = (r["deadline_d"] - today).days
    else:
        days_left = None
    too_late = not r["deadline_d"] and r["start_d"] and (r["start_d"] - today).days < 21
    if over:
        group = "closed"
        why.append("this edition's deadline or dates have passed; watch for the next one")
    elif too_late:
        group = "closed"
        why.append("starts in under 3 weeks with no open deadline: too late for this edition (our rule of thumb)")
    elif not ref:
        group = "strong-watch" if score >= 2 else "watch"
    else:
        group = "strong" if score >= 2 else "open"
    if r["notes"]:
        why.append(r["notes"])
    entry = "; ".join(x for x in [RELEASE_TEXT.get(r["release_rule"], r["release_rule"]),
                                  f"region: {r['region_note'] or r['regions']}" if r["regions"] else "",
                                  f"{r['identity']}-led teams" if r["identity"] else ""] if x)
    cost = {"free": "free", "paid": "paid" + (f": {r['cost_note']}" if r["cost_note"] else "")}.get(r["cost"], "cost not stated")
    return {"group": group, "score": score, "row": r, "days_left": days_left, "matched": matched, "why": why,
            "entry": entry, "cost": cost}, None


def rank_key(m, today):
    r = m["row"]
    soon = m["days_left"] if m["days_left"] is not None else (400 + (r["start_d"] - today).days if r["start_d"] and r["start_d"] >= today else 9999)
    order = {"strong": 0, "strong-watch": 1, "open": 2, "watch": 3, "closed": 4}[m["group"]]
    return (order, -m["score"], soon, r["name"])


def run_filters(a, today):
    rows = load(a.table)
    kept, left = [], []
    for r in rows:
        m, reason = evaluate(r, a, today)
        if m:
            kept.append(m)
        else:
            left.append((r["name"], reason))
    kept.sort(key=lambda m: rank_key(m, today))
    # Our pick: the last Next Fest that fits before launch.
    nfs = [m for m in kept if m["row"]["type"] == "Valve Next Fest" and m["group"] != "closed" and m["row"]["start_d"]]
    if nfs:
        pick = max(nfs, key=lambda m: m["row"]["start_d"])
        pick["why"].insert(0, "our pick for Next Fest: the last edition that fits before launch")
        pick["score"] += 1
        kept.sort(key=lambda m: rank_key(m, today))
    return kept, left


def write_outputs(kept, left, a, today):
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "events.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(OUT_COLS)
        for i, m in enumerate(kept, 1):
            r = m["row"]
            w.writerow([i, m["group"], r["name"], r["organizer"], r["type"], r["start"], r["end"], r["deadline"] or "not published",
                        r["deadline_basis"], "" if m["days_left"] is None else m["days_left"], "; ".join(m["matched"]), m["entry"],
                        m["cost"], r["prepare"], " ".join(w_.rstrip(".") + "." for w_ in m["why"]), r["apply"], r["source"], r["checked"]])
    lines = [f"# Events shortlist ({today.isoformat()})", "",
             f"- Game status: {a.status}. Tags: {', '.join(a.tags) or 'none given'}. Region: {a.region}. Team: {', '.join(a.team) or 'not given'}.",
             f"- Window: {a.date_from} to {a.date_to}." + (f" Launch: {a.launch}." if a.launch else ""),
             "- Deadline basis: 'valve date' and 'organizer date' are published dates; 'estimate' is our arithmetic. Re-check the source before you submit.",
             "- Prepare column is our practice, not an organizer rule.", ""]
    short = [m for m in kept if m["group"] in ("strong", "strong-watch", "open")][: a.limit]
    lines += ["## Shortlist", "", "| # | Event | Type | Dates | Deadline | Days left | Entry | Cost | Why |", "|---|---|---|---|---|---|---|---|---|"]
    for i, m in enumerate(short, 1):
        r = m["row"]
        dates = f"{r['start']} to {r['end']}" if r["start"] else "not published"
        dl = (r["deadline"] + (" (estimate)" if r["deadline_basis"].startswith("estimate") else "")) if r["deadline"] else "not published"
        lines.append(f"| {i} | [{r['name']}]({r['source']}) | {r['type']} | {dates} | {dl} | {'' if m['days_left'] is None else m['days_left']} | {m['entry']} | {m['cost']} | {'; '.join(m['why'][:2])} |")
    lines += ["", "## What to prepare, by deadline", ""]
    for m in [m for m in short if m["days_left"] is not None][:8]:
        r = m["row"]
        lines.append(f"- **{r['name']}** (deadline {r['deadline']}, {m['days_left']} days): {r['prepare']}.")
    watch = [m for m in kept if m["group"] == "watch"]
    if watch:
        lines += ["", "## Watch (no date published)", ""] + [f"- [{m['row']['name']}]({m['row']['source']}): {'; '.join(m['why'][:2])}" for m in watch[:20]]
    closed = [m for m in kept if m["group"] == "closed"]
    if closed:
        lines += ["", "## Closed for now", ""] + [f"- {m['row']['name']}: {m['why'][-2] if m['row']['notes'] else m['why'][-1]}" for m in closed[:20]]
    lines += ["", f"Left out: {len(left)} events (wrong theme, region, team, status or dates). Full list in events.csv.", ""]
    (out / "events.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'events.md'} and {out / 'events.csv'}: {len(short)} shortlisted, {len(kept)} kept, {len(left)} left out")


def validate_table(path):
    errs = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != COLS:
            errs.append(f"columns must be {','.join(COLS)}")
            return errs
        ids = set()
        for n, r in enumerate(reader, 2):
            tag = f"line {n} ({r['id']})"
            if r["id"] in ids:
                errs.append(f"{tag}: duplicate id")
            ids.add(r["id"])
            if not r["source"].startswith("http"):
                errs.append(f"{tag}: no source URL")
            for k in ("start", "end", "deadline", "checked"):
                if r[k]:
                    try:
                        dt.date.fromisoformat(r[k])
                    except ValueError:
                        errs.append(f"{tag}: {k} '{r[k]}' is not YYYY-MM-DD")
            if not r["checked"]:
                errs.append(f"{tag}: no checked date")
            if r["start"] and r["end"] and r["end"] < r["start"]:
                errs.append(f"{tag}: ends before it starts")
            if r["deadline"] and not r["deadline_basis"]:
                errs.append(f"{tag}: deadline without a basis")
            if r["usual_month"] and not (r["usual_month"].isdigit() and 1 <= int(r["usual_month"]) <= 12):
                errs.append(f"{tag}: usual_month must be 1 to 12")
    return errs


def validate_output(path):
    errs = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != OUT_COLS:
            return [f"columns must be {','.join(OUT_COLS)}"]
        rows = list(reader)
    if not rows:
        errs.append("no events in the file")
    for r in rows:
        if not r["source"].startswith("http"):
            errs.append(f"rank {r['rank']} ({r['name']}): no source URL")
        if r["deadline"] != "not published" and not r["deadline_basis"]:
            errs.append(f"rank {r['rank']} ({r['name']}): deadline without a basis")
    md = Path(path).with_name("events.md")
    if not md.exists():
        errs.append(f"{md} is missing")
    return errs


def add_filters(p, need_status):
    p.add_argument("--status", choices=["unreleased", "demo", "released"], required=need_status,
                   help="unreleased (no demo), demo (unreleased with a demo), released")
    p.add_argument("--tags", default="", help="comma-separated Steam tags, e.g. 'Cozy,Farming Sim'")
    p.add_argument("--region", choices=REGIONS, default="global", help="where the studio is based (default global)")
    p.add_argument("--team", default="", help=f"comma-separated team identities: {','.join(IDENTITIES)}")
    p.add_argument("--launch", help="release date (planned or past), for Next Fest and sale rules")
    p.add_argument("--from", dest="date_from", help="window start (default today)")
    p.add_argument("--to", dest="date_to", help="window end (default today + 365 days)")
    p.add_argument("--free-only", action="store_true", help="drop paid entries")
    p.add_argument("--online-only", action="store_true", help="drop in-person events")
    p.add_argument("--in-next-fest-before", action="store_true", help="the game was already in a Next Fest")
    p.add_argument("--today", help="today's date (default: system date)")
    p.add_argument("--table", default=str(TABLE), help="events table (default: references/events.csv)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find", help="rank events for one game and write events.md and events.csv")
    add_filters(f, True)
    f.add_argument("--out-dir", default="launch", help="output folder (default: launch)")
    f.add_argument("--limit", type=int, default=15, help="shortlist length (default 15)")
    d = sub.add_parser("deadlines", help="list deadlines in the next N days")
    add_filters(d, False)
    d.add_argument("--days", type=int, default=60, help="how far ahead (default 60)")
    v = sub.add_parser("validate", help="check the bundled table, or a written events.csv with --output")
    v.add_argument("--table", default=str(TABLE))
    v.add_argument("--output", help="path to a written events.csv to check instead")
    a = p.parse_args()

    if a.cmd == "validate":
        errs = validate_output(a.output) if a.output else validate_table(a.table)
        for e in errs:
            print(f"PROBLEM: {e}")
        if errs:
            sys.exit(1)
        print(f"ok: {a.output or a.table}")
        return

    today = iso(a.today) if a.today else dt.date.today()
    a.tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    a.team = [t.strip() for t in a.team.split(",") if t.strip()]
    for t in a.team:
        if t not in IDENTITIES:
            sys.exit(f"error: unknown team identity '{t}' (use {','.join(IDENTITIES)})")
    a.launch = iso(a.launch) if a.launch else None
    a.date_from = iso(a.date_from) if a.date_from else today
    a.date_to = iso(a.date_to) if a.date_to else today + dt.timedelta(days=365)
    if a.date_to < a.date_from:
        sys.exit("error: --to is before --from")

    if a.cmd == "find":
        kept, left = run_filters(a, today)
        write_outputs(kept, left, a, today)
        return

    # deadlines
    end = today + dt.timedelta(days=a.days)
    a.date_from, a.date_to = today, end + dt.timedelta(days=400)
    kept, _ = run_filters(a, today) if a.status else ([{"row": r, "days_left": None} for r in load(a.table)], [])
    rows = sorted({m["row"]["id"]: m["row"] for m in kept}.values(), key=lambda r: r["deadline_d"] or dt.date.max)
    hits = [r for r in rows if r["deadline_d"] and today <= r["deadline_d"] <= end]
    if not hits:
        print(f"No published deadlines between {today} and {end}.")
        return
    print(f"Deadlines {today} to {end}:")
    for r in hits:
        basis = "estimate" if r["deadline_basis"].startswith("estimate") else r["deadline_basis"].split(":")[0]
        print(f"{r['deadline']}  ({(r['deadline_d'] - today).days:>3} days)  {r['name']}  [{r['type']}; {basis}]  {r['apply'] or r['source']}")


if __name__ == "__main__":
    main()
