#!/usr/bin/env python3
"""Turn the Reddit tracker into a per-subreddit scoreboard and a "next allowed post" list.

Reads:
  tracker   marketing/reddit/tracker.csv. Columns used: date, slot, subreddit, post_id, status,
            and any of the result columns upvotes, comments, views, visits, wishlists.
            status is planned, posted, removed or skipped. C-slot rows (comments only) are ignored.
  --subs    the subreddit list (default: this skill's references/subreddits.csv). Columns used:
            subreddit, allowed_days, gap_days, promo_allowed, confidence.

Writes a Markdown report (stdout or --out) with:
  1. Scoreboard: posts, removals, median upvotes, comments, views, visits and wishlists per
     subreddit, ranked by wishlists then visits then upvotes. Flags subs with removals.
  2. Next allowed date per subreddit from its gap and allowed days, counted from your last post.
  3. Suggestions: subs to post in again, subs to drop (2 or more posts with no visits and low
     upvotes, or any removal), and listed subs never tried.
"""
import argparse
import csv
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
RESULTS = ["upvotes", "comments", "views", "visits", "wishlists"]
DEFAULT_SUBS = Path(__file__).resolve().parent.parent / "references" / "subreddits.csv"


def norm(sub):
    s = sub.strip().lower()
    return s if s.startswith("r/") else "r/" + s


def num(v):
    v = (v or "").replace(",", "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def allowed_weekdays(text):
    t = (text or "").strip().lower()
    if not t or t == "any":
        return set(range(7))
    out = set()
    for part in t.replace(";", ",").split(","):
        p = part.strip()[:3]
        for i, d in enumerate(DAYS):
            if d.startswith(p) and p:
                out.add(i)
    return out or set(range(7))


def next_allowed(last, gap, weekdays, today):
    d = max(today, last + timedelta(days=gap)) if last else today
    for _ in range(14):
        if d.weekday() in weekdays:
            return d
        d += timedelta(days=1)
    return d


def load_subs(path):
    subs = {}
    if not path.exists():
        return subs
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("subreddit"):
                subs[norm(row["subreddit"])] = row
    return subs


def fmt(v):
    if v is None:
        return "-"
    return f"{v:,.0f}" if v >= 10 or v == int(v) else f"{v:.1f}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tracker", type=Path)
    p.add_argument("--subs", type=Path, default=DEFAULT_SUBS)
    p.add_argument("--default-gap", type=int, default=14)
    p.add_argument("--today", type=date.fromisoformat, default=date.today())
    p.add_argument("--out", type=Path)
    args = p.parse_args()

    if not args.tracker.exists():
        sys.exit(f"{args.tracker}: not found")
    subs = load_subs(args.subs)

    posts = defaultdict(list)
    with args.tracker.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        need = {"date", "slot", "subreddit", "status"}
        if not need <= set(reader.fieldnames or []):
            sys.exit(f"{args.tracker}: needs columns {sorted(need)}")
        for n, row in enumerate(reader, start=2):
            if row["slot"].strip().upper() == "C":
                continue
            status = row["status"].strip().lower()
            if status not in {"posted", "removed"}:
                continue
            try:
                d = date.fromisoformat(row["date"].strip())
            except ValueError:
                sys.exit(f"{args.tracker}: line {n}: bad date '{row['date']}'")
            posts[norm(row["subreddit"])].append({"date": d, "status": status,
                                                   **{k: num(row.get(k)) for k in RESULTS}})

    rows = []
    for sub, ps in posts.items():
        r = {"sub": sub, "posts": len(ps), "removed": sum(p["status"] == "removed" for p in ps),
             "last": max(p["date"] for p in ps)}
        for k in RESULTS:
            vals = [p[k] for p in ps if p[k] is not None]
            r[k] = statistics.median(vals) if vals else None
            r[k + "_sum"] = sum(vals) if vals else None
        rows.append(r)
    rows.sort(key=lambda r: (-(r["wishlists_sum"] or 0), -(r["visits_sum"] or 0), -(r["upvotes"] or 0)))

    out = [f"# Reddit scoreboard, {args.today}", ""]
    out.append(f"From `{args.tracker}`: {sum(r['posts'] for r in rows)} posts in {len(rows)} subreddits. "
               "Medians per post, except visits and wishlists, which are totals.")
    out += ["", "## Scoreboard", "",
            "| Subreddit | Posts | Removed | Upvotes | Comments | Views | Visits | Wishlists |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        out.append(f"| {r['sub']} | {r['posts']} | {r['removed']} | {fmt(r['upvotes'])} | {fmt(r['comments'])} | "
                   f"{fmt(r['views'])} | {fmt(r['visits_sum'])} | {fmt(r['wishlists_sum'])} |")
    if not rows:
        out.append("| (no posted rows yet) | | | | | | | |")

    out += ["", "## Next allowed post", "",
            "Earliest day you may post again, from the gap and allowed days in the subreddit list. "
            "Check the sidebar: rules change.", "",
            "| Subreddit | Last post | Gap (days) | Allowed days | Next allowed | Rule confidence |",
            "|---|---|---:|---|---|---|"]
    names = sorted(set(subs) | set(posts))
    for sub in names:
        info = subs.get(sub, {})
        if (info.get("promo_allowed") or "").strip().lower() == "no":
            continue
        gap = int(num(info.get("gap_days")) or args.default_gap)
        wd = allowed_weekdays(info.get("allowed_days"))
        last = max((p["date"] for p in posts.get(sub, [])), default=None)
        nxt = next_allowed(last, gap, wd, args.today)
        days = info.get("allowed_days") or "any"
        out.append(f"| {sub} | {last or 'never'} | {gap} | {days} | {nxt} ({DAYS[nxt.weekday()][:3].title()}) | "
                   f"{info.get('confidence') or 'unlisted'} |")

    keep = [r["sub"] for r in rows if (r["wishlists_sum"] or 0) > 0 or (r["visits_sum"] or 0) > 0]
    drop = [r["sub"] for r in rows if r["removed"] > 0 or
            (r["posts"] >= 2 and not (r["visits_sum"] or 0) and (r["upvotes"] or 0) < 10)]
    untried = [s for s in subs if s not in posts and (subs[s].get("promo_allowed") or "").lower() != "no"]
    out += ["", "## Suggestions", ""]
    out.append(f"- **Post again:** {', '.join(keep) if keep else 'none yet (no tagged visits recorded)'}.")
    out.append(f"- **Drop or fix first:** {', '.join(drop) if drop else 'none'}. A removal means read the rules "
               "and message the moderators before you post there again.")
    out.append(f"- **Not tried yet:** {', '.join(untried[:12]) if untried else 'none'}"
               f"{' and more' if len(untried) > 12 else ''}.")
    out.append("- Small numbers swing a lot. Judge a subreddit after 2 or 3 posts, not 1.")

    text = "\n".join(out) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
