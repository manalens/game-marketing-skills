#!/usr/bin/env python3
"""Read a Steamworks wishlist report CSV and write a Markdown wishlist analysis.

Assumed columns (matched by name, case and punctuation ignored, first match wins):
  date        DateLocal, Date, Day, DateUTC, Datetime            (required)
  adds        Adds, Wishlist Adds, Additions, Added              (required)
  deletes     Deletes, Deletions, Removes, Removed
  purchases   PurchasesAndActivations, Purchases, Wishlist Purchases
  activations Activations (only when it is its own column)
  gifts       Gifts, Gifted
  outstanding Outstanding, Balance, Total Wishlists, Outstanding Wishlists
  game        Game, App, App Name, Game Name
Lines above the header (a report title) are skipped. Several rows for one day (per country or
per game) are added up. With a Game column and no --game, the game with the most adds is kept.
Unknown columns such as MonthCohort are listed and left out.

Stdlib only. Exit codes: 0 ok, 2 bad input.
"""
import argparse
import csv
import io
import math
import re
import statistics
import sys
from datetime import date, datetime, timedelta

ALIASES = {
    "date": ["datelocal", "date", "day", "dateutc", "datetime", "dategmt"],
    "adds": ["adds", "wishlistadds", "additions", "added", "add"],
    "deletes": ["deletes", "wishlistdeletes", "deletions", "removes", "removed", "removals"],
    "purchases": ["purchasesandactivations", "purchasesactivations", "purchases",
                  "wishlistpurchases", "purchasesfromwishlist", "purchased"],
    "activations": ["activations", "wishlistactivations", "activated"],
    "gifts": ["gifts", "gifted", "wishlistgifts"],
    "outstanding": ["outstanding", "outstandingwishlists", "balance", "wishlistbalance",
                    "totalwishlists", "totaloutstanding", "currentwishlists"],
    "game": ["game", "app", "appname", "gamename", "title", "product"],
}

# Benchmarks shown next to the conversion number. Ranges with sources, never a forecast.
BENCHMARKS = [
    "Wishlist purchases only, one game: Danchi Days bought about 2.2% of ~55,000 outstanding "
    "wishlists in launch week; monthly cohorts ranged 1.0% to 7.4% (Melos Han-Tani, 8 Nov 2026).",
    "All week-one sales per launch wishlist (includes buyers who never wishlisted, so higher than "
    "the wishlist-only rate): GameDiscoverCo median 0.15 for 25k+ wishlist launches, 0.10 above $10, "
    "year to Aug 2025 (GameDiscoverCo, 17 Oct 2025); spread between games is 10x to 20x.",
    "First-month sales per wishlist: about 0.22 for 2023 to 2025 games vs 0.45 for 2020 to 2022 "
    "(claim, 160 games; How To Market A Game, 13 Oct 2026). Total wishlists still predict sales.",
]


class InputError(Exception):
    pass


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def classify(cell):
    key = norm(cell)
    if not key:
        return None
    for kind, names in ALIASES.items():
        if key in names:
            return kind
    return None


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_date(text):
    t = text.strip().strip('"')
    if not t:
        return None
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?:[ T].*)?$", t)
    try:
        if m:
            return date(int(m[1]), int(m[2]), int(m[3]))
        m = re.match(r"^(\d{8})$", t)
        if m:
            return datetime.strptime(t, "%Y%m%d").date()
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", t)
        if m:  # Steamworks shows US order; a first number above 12 means day/month
            a, b, y = int(m[1]), int(m[2]), int(m[3])
            return date(y, b, a) if a > 12 else date(y, a, b)
        m = re.match(r"^([A-Za-z]{3})[a-z]*\.? (\d{1,2}),? (\d{4})$", t)
        if m and m[1].lower() in MONTHS:
            return date(int(m[3]), MONTHS[m[1].lower()], int(m[2]))
        m = re.match(r"^(\d{1,2}) ([A-Za-z]{3})[a-z]*\.?,? (\d{4})$", t)
        if m and m[2].lower() in MONTHS:
            return date(int(m[3]), MONTHS[m[2].lower()], int(m[1]))
    except ValueError:
        return None
    return None


def parse_count(text):
    t = (text or "").strip().replace(",", "").replace(" ", "").replace(" ", "")
    if t in ("", "-"):
        return 0
    return int(round(float(t)))


def sniff_rows(text):
    lines = text.splitlines()
    sample = "\n".join(lines[:20])
    delim = max([",", ";", "\t"], key=lambda d: sample.count(d))
    return list(csv.reader(io.StringIO(text), delimiter=delim))


def read_wishlists(path, game_wanted):
    try:
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError as e:
        raise InputError(f"{path}: cannot read ({e})")
    rows = sniff_rows(text)
    hi = None
    for i, row in enumerate(rows):
        kinds = [classify(c) for c in row]
        if "date" in kinds and "adds" in kinds:
            hi = i
            break
    if hi is None:
        raise InputError(f"{path}: no header row with a date column (such as DateLocal) and an "
                         "adds column (such as Adds)")
    header = rows[hi]
    idx, ignored = {}, []
    for pos, cell in enumerate(header):
        kind = classify(cell)
        if kind and kind not in idx:
            idx[kind] = pos
        elif cell.strip():
            ignored.append(cell.strip())
    data = rows[hi + 1:]

    def game_of(row):
        return row[idx["game"]].strip() if "game" in idx and idx["game"] < len(row) else ""

    games = {}
    if "game" in idx:
        for row in data:
            if row and len(row) > idx["date"] and parse_date(row[idx["date"]]):
                try:
                    games[game_of(row)] = games.get(game_of(row), 0) + parse_count(row[idx["adds"]])
                except (ValueError, IndexError):
                    pass
    game = None
    if games:
        if game_wanted:
            if game_wanted not in games:
                raise InputError(f"{path}: game '{game_wanted}' not found; games: "
                                 + ", ".join(sorted(games)))
            game = game_wanted
        else:
            game = max(games, key=lambda g: games[g])
    days, skipped = {}, 0
    keys = ["adds", "deletes", "purchases", "activations", "gifts", "outstanding"]
    for n, row in enumerate(data, start=hi + 2):
        if not row or not any(c.strip() for c in row):
            continue
        if game is not None and game_of(row) != game:
            continue
        cell = row[idx["date"]] if idx["date"] < len(row) else ""
        d = parse_date(cell)
        if d is None:
            if norm(cell) in ("total", "totals", "sum", "") or norm(" ".join(row)).startswith("total"):
                continue
            raise InputError(f"{path}: line {n}: cannot read date '{cell}'")
        rec = days.setdefault(d, {k: 0 for k in keys} | {"has_out": False})
        for k in keys:
            if k not in idx:
                continue
            try:
                v = parse_count(row[idx[k]] if idx[k] < len(row) else "")
            except ValueError:
                raise InputError(f"{path}: line {n}: '{row[idx[k]]}' in column "
                                 f"'{header[idx[k]]}' is not a number")
            if k == "outstanding":
                if row[idx[k]].strip():
                    rec["outstanding"] += v
                    rec["has_out"] = True
            else:
                if v < 0:
                    raise InputError(f"{path}: line {n}: negative {k} ({v})")
                rec[k] += v
    if not days:
        raise InputError(f"{path}: header found but no rows with a readable date")
    cols = {k: header[i].strip() for k, i in idx.items()}
    return days, cols, ignored, game, sorted(games)


def read_dated(path, kind):
    """posts.csv (post_id,date,platform,format,title) or events (date,name[,end_date][,kind])."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = {norm(h): h for h in (reader.fieldnames or [])}
            if "date" not in fields and "startdate" not in fields and "start" not in fields:
                raise InputError(f"{path}: needs a 'date' column")
            dcol = fields.get("date") or fields.get("startdate") or fields.get("start")
            ecol = fields.get("enddate") or fields.get("end")
            out = []
            for n, row in enumerate(reader, start=2):
                d = parse_date(row.get(dcol) or "")
                if d is None:
                    raise InputError(f"{path}: line {n}: cannot read date '{row.get(dcol)}'")
                end = parse_date(row.get(ecol) or "") if ecol else None
                if end and end < d:
                    raise InputError(f"{path}: line {n}: end date before start date")
                if kind == "post":
                    label = " ".join(x for x in [row.get(fields.get("postid", ""), ""),
                                                 "(" + (row.get(fields.get("format", ""), "") or "?") + ")"]
                                     if x)
                else:
                    label = (row.get(fields.get("name", ""), "") or row.get(fields.get("event", ""), "")
                             or row.get(fields.get("title", ""), "") or "event").strip()
                out.append({"start": d, "end": end or d, "label": label.strip()})
            return out
    except OSError as e:
        raise InputError(f"{path}: cannot read ({e})")


def mad(values, med):
    return statistics.median([abs(v - med) for v in values])


def quantile(values, q):
    s = sorted(values)
    if not s:
        return 0.0
    pos = (len(s) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def fmt(n, digits=0):
    if n is None:
        return "-"
    return f"{n:,.{digits}f}"


def iso(d):
    return d.isoformat()


def parse_arg_date(text, name):
    d = parse_date(text)
    if d is None:
        raise InputError(f"{name}: cannot read date '{text}' (use YYYY-MM-DD)")
    return d


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Analyse a Steamworks wishlist CSV: weekly summary, spike days joined to "
                    "posts and events, baseline, conversion after a launch or sale, and a "
                    "cautious outlook. Writes Markdown.",
        epilog="Example: wishlists.py --wishlists wl.csv --posts marketing/posts.csv "
               "--events events.csv --outstanding 4210 --target-date 2027-03-04")
    p.add_argument("--wishlists", required=True, help="Steamworks wishlist report CSV (daily rows)")
    p.add_argument("--posts", help="marketing/posts.csv (needs a date column)")
    p.add_argument("--events", help="CSV with date,name and optional end_date (Next Fest, a "
                                    "festival, a creator video, a sale)")
    p.add_argument("--game", help="game name to keep when the file lists several")
    p.add_argument("--outstanding", type=int,
                   help="outstanding wishlists from the Steamworks wishlist page, to anchor the "
                        "running total (default: a column in the file, else 0 at file start)")
    p.add_argument("--outstanding-date", help="the day --outstanding was read (default: last day "
                                              "in the file)")
    p.add_argument("--launch", help="launch or sale start date, YYYY-MM-DD, for conversion")
    p.add_argument("--window", type=int, default=7, help="days after --launch to count (default 7)")
    p.add_argument("--target-date", help="date for the outlook, YYYY-MM-DD")
    p.add_argument("--factor", type=float, default=3.0,
                   help="spike if adds >= factor x trailing 28-day median (default 3)")
    p.add_argument("--mads", type=float, default=3.0,
                   help="or adds > median + this many scaled MADs (default 3)")
    p.add_argument("--min-adds", type=int, default=10,
                   help="never call a day with fewer adds a spike (default 10)")
    p.add_argument("--near", type=int, default=2, help="days around a spike to look for posts "
                                                      "and events (default 2)")
    p.add_argument("--out", help="write Markdown here instead of stdout")
    a = p.parse_args(argv)

    try:
        return run(a)
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def run(a):
    if a.window < 1 or a.factor <= 1 or a.mads <= 0 or a.near < 0:
        raise InputError("--window must be >= 1, --factor > 1, --mads > 0, --near >= 0")
    days, cols, ignored, game, games = read_wishlists(a.wishlists, a.game)
    posts = read_dated(a.posts, "post") if a.posts else []
    events = read_dated(a.events, "event") if a.events else []
    launch = parse_arg_date(a.launch, "--launch") if a.launch else None
    target = parse_arg_date(a.target_date, "--target-date") if a.target_date else None

    first, last = min(days), max(days)
    span = (last - first).days + 1
    warnings = []
    missing = span - len(days)
    if missing:
        warnings.append(f"{missing} days between {iso(first)} and {iso(last)} have no row; "
                        "they count as 0 adds. Check the export range.")
    series = []
    for i in range(span):
        d = first + timedelta(days=i)
        r = days.get(d, {"adds": 0, "deletes": 0, "purchases": 0, "activations": 0, "gifts": 0,
                         "outstanding": 0, "has_out": False})
        out_change = r["adds"] - r["deletes"] - r["purchases"] - r["activations"] - r["gifts"]
        series.append({"date": d, **r, "net": r["adds"] - r["deletes"], "change": out_change,
                       "bought": r["purchases"] + r["activations"]})

    # Running outstanding: anchor on --outstanding, else a column, else 0 at file start.
    anchor_note = ""
    cum, run_total = [], 0
    for s in series:
        run_total += s["change"]
        cum.append(run_total)
    if a.outstanding is not None:
        adate = parse_arg_date(a.outstanding_date, "--outstanding-date") if a.outstanding_date else last
        if not first <= adate <= last:
            raise InputError("--outstanding-date must be inside the file's date range")
        offset = a.outstanding - cum[(adate - first).days]
        anchor_note = f"anchored on {fmt(a.outstanding)} outstanding on {iso(adate)} (--outstanding)"
    elif any(s["has_out"] for s in series):
        ref = next(i for i in range(len(series) - 1, -1, -1) if series[i]["has_out"])
        offset = series[ref]["outstanding"] - cum[ref]
        anchor_note = f"anchored on the '{cols['outstanding']}' column on {iso(series[ref]['date'])}"
    else:
        offset = 0
        anchor_note = ("not anchored: no outstanding number was given, so it is the change since "
                       f"{iso(first)}. Pass --outstanding from the Steamworks wishlist page, or "
                       "export all history")
        warnings.append("Outstanding is " + anchor_note + ".")
    for s, c in zip(series, cum):
        s["out"] = c + offset
    if min(s["out"] for s in series) < 0:
        warnings.append("The running outstanding goes below 0, so the anchor or the file range "
                        "is off.")

    # Spikes: adds vs the trailing 28-day median of the days before (at least 7 days of history).
    for i, s in enumerate(series):
        prior = [x["adds"] for x in series[max(0, i - 28):i]]
        s["spike"] = False
        s["med"] = None
        if len(prior) < 7:
            continue
        med = statistics.median(prior)
        dev = mad(prior, med) * 1.4826
        s["med"] = med
        by_factor = s["adds"] >= a.factor * med if med > 0 else False
        by_mad = dev > 0 and s["adds"] > med + a.mads * dev
        s["spike"] = s["adds"] >= a.min_adds and s["adds"] > med and (by_factor or by_mad)
        s["why"] = ", ".join(x for x, ok in [(f">= {a.factor:g}x median", by_factor),
                                              (f"> median + {a.mads:g} MAD", by_mad)] if ok)
    if span < 8:
        warnings.append("Fewer than 8 days: no spike test is possible.")

    # Days that sit inside a launch or sale window are not baseline either.
    def in_launch(d):
        return launch is not None and launch <= d < launch + timedelta(days=a.window)

    lines = []
    w = lines.append
    w(f"# Wishlist analysis{': ' + game if game else ''}")
    w("")
    w(f"File: `{a.wishlists}`, {iso(first)} to {iso(last)} ({span} days). Columns read: "
      + ", ".join(f"{v} ({k})" for k, v in cols.items()) + ".")
    if ignored:
        w(f"Left out: {', '.join(ignored)}.")
    if len(games) > 1:
        w(f"Games in the file: {', '.join(games)}. Kept: {game}. Use --game to pick another.")
    w("Steam export days are usually Pacific time (DateLocal); the Financial API uses GMT days.")
    w("")

    tot = {k: sum(s[k] for s in series) for k in ("adds", "deletes", "purchases", "activations",
                                                     "gifts", "net", "change")}
    w("## Totals")
    w("")
    w("| Adds | Deletes | Net adds | Delete rate | Purchases + activations | Gifts | Outstanding at end |")
    w("|---:|---:|---:|---:|---:|---:|---:|")
    rate = f"{100 * tot['deletes'] / tot['adds']:.1f}%" if tot["adds"] else "-"
    w(f"| {fmt(tot['adds'])} | {fmt(tot['deletes'])} | {fmt(tot['net'])} | {rate} | "
      f"{fmt(tot['purchases'] + tot['activations'])} | {fmt(tot['gifts'])} | {fmt(series[-1]['out'])} |")
    w("")
    w(f"Outstanding is {anchor_note}. Outstanding change = adds - deletes - purchases - "
      "activations - gifts.")
    w("")

    w("## Weekly summary")
    w("")
    w("Weeks start on Monday. A first or last week with fewer than 7 days is marked.")
    w("")
    w("| Week of | Days | Adds | Deletes | Net | Purchases + act. | Gifts | Outstanding at week end | Net per day |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    weeks = {}
    for s in series:
        wk = s["date"] - timedelta(days=s["date"].weekday())
        weeks.setdefault(wk, []).append(s)
    for wk, ss in weeks.items():
        n = len(ss)
        net = sum(x["net"] for x in ss)
        w(f"| {iso(wk)}{'' if n == 7 else ' (part)'} | {n} | {fmt(sum(x['adds'] for x in ss))} | "
          f"{fmt(sum(x['deletes'] for x in ss))} | {fmt(net)} | {fmt(sum(x['bought'] for x in ss))} | "
          f"{fmt(sum(x['gifts'] for x in ss))} | {fmt(ss[-1]['out'])} | {fmt(net / n, 1)} |")
    w("")

    w("## Spike days")
    w("")
    w(f"A spike: at least {a.min_adds} adds and either {a.factor:g}x the median of the 28 days "
      f"before, or more than that median plus {a.mads:g} scaled MADs. Posts and events within "
      f"{a.near} days are listed. Being near a post does not prove the post caused it.")
    w("")
    spikes = [s for s in series if s["spike"]]
    if not spikes:
        w("No spike days found.")
    else:
        w("| Date | Weekday | Adds | 28-day median | x median | Rule | Near (posts, events) |")
        w("|---|---|---:|---:|---:|---|---|")
        for s in spikes:
            d = s["date"]
            near = []
            for e in events:
                if e["start"] - timedelta(days=a.near) <= d <= e["end"] + timedelta(days=a.near):
                    near.append(f"event: {e['label']} ({iso(e['start'])}"
                                + (f" to {iso(e['end'])}" if e["end"] != e["start"] else "") + ")")
            for po in posts:
                if abs((po["start"] - d).days) <= a.near:
                    near.append(f"post {iso(po['start'])}: {po['label']}")
            ratio = f"{s['adds'] / s['med']:.1f}" if s["med"] else "-"
            w(f"| {iso(d)} | {d.strftime('%a')} | {fmt(s['adds'])} | {fmt(s['med'], 1)} | {ratio} | "
              f"{s['why']} | {'; '.join(near) if near else 'nothing logged: ask what happened'} |")
    w("")

    # Baseline: non-spike, non-launch days in the last 28 days (fallback: all non-spike days).
    base_days = [s for s in series if not s["spike"] and not in_launch(s["date"])]
    recent = [s for s in base_days if s["date"] > last - timedelta(days=28)]
    pool = recent if len(recent) >= 7 else base_days
    if not pool:
        raise InputError("no non-spike days to compute a baseline")
    base_adds = statistics.median([s["adds"] for s in pool])
    base_net = statistics.median([s["net"] for s in pool])
    if events:
        w("## Events")
        w("")
        w("Adds during each event (plus the day after) against a local baseline: the median adds "
          "of the non-spike days in the 28 days before the event. Extra = adds - baseline x days. "
          "Anything else that happened in the window counts too.")
        w("")
        w("| Event | Days | Adds | Baseline adds | Extra adds | Net adds |")
        w("|---|---:|---:|---:|---:|---:|")
        for e in events:
            ss = [s for s in series if e["start"] <= s["date"] <= e["end"] + timedelta(days=1)]
            if not ss:
                w(f"| {e['label']} ({iso(e['start'])}) | 0 | - | - | - | outside the file |")
                continue
            before = [s["adds"] for s in base_days
                      if e["start"] - timedelta(days=28) <= s["date"] < e["start"]]
            adds = sum(s["adds"] for s in ss)
            if len(before) < 7:
                w(f"| {e['label']} ({iso(e['start'])}) | {len(ss)} | {fmt(adds)} | - | - | "
                  f"{fmt(sum(s['net'] for s in ss))} |")
                continue
            local = statistics.median(before) * len(ss)
            w(f"| {e['label']} ({iso(e['start'])}) | {len(ss)} | {fmt(adds)} | "
              f"{fmt(local)} | {fmt(adds - local)} | {fmt(sum(s['net'] for s in ss))} |")
        w("")

    w("## Baseline")
    w("")
    w(f"Median of {len(pool)} days ({'last 28 days' if pool is recent else 'whole file'}) "
      "without spikes and outside the launch window:")
    w("")
    w(f"- Adds per day: **{fmt(base_adds, 1)}**")
    w(f"- Net adds per day (after deletes): **{fmt(base_net, 1)}**")
    spike_adds = sum(s["adds"] for s in spikes)
    if tot["adds"]:
        w(f"- Spike days: {len(spikes)} days, {fmt(spike_adds)} adds, "
          f"{100 * spike_adds / tot['adds']:.0f}% of all adds in the file.")
    w("")

    w("## Conversion")
    w("")
    if not launch:
        w("No --launch date given. Pass the launch day or a sale's first day to see wishlist "
          "purchases against outstanding wishlists.")
    elif not first < launch <= last:
        w(f"--launch {iso(launch)} needs at least one day of the file before it and must be "
          f"inside {iso(first)} to {iso(last)}.")
    else:
        before = series[(launch - first).days - 1]["out"]
        win = [s for s in series if launch <= s["date"] < launch + timedelta(days=a.window)]
        bought = sum(s["bought"] for s in win)
        w(f"Outstanding at the start of {iso(launch)}: {fmt(before)}. Purchases and activations "
          f"from wishlists in {len(win)} days: {fmt(bought)}.")
        w("")
        if before > 0:
            w(f"**Wishlist conversion: {100 * bought / before:.1f}%** of outstanding wishlists in "
              f"{len(win)} days" + (" (window not finished yet)" if len(win) < a.window else "") + ".")
        else:
            w("Outstanding at launch is 0 or unknown, so no rate. Pass --outstanding.")
        w("")
        w("Context (ranges with sources, not promises):")
        w("")
        for b in BENCHMARKS:
            w(f"- {b}")
        w("")
        w("This rate counts only purchases from the wishlist. Total sales are higher. "
          "Gifts and deletes after launch are not in it.")
    w("")

    w("## Outlook")
    w("")
    if not target:
        w("No --target-date given.")
    elif target <= last:
        w(f"--target-date {iso(target)} is not after the last day in the file ({iso(last)}).")
    else:
        n = (target - last).days
        hist = [s["change"] for s in pool]
        mid_rate = statistics.median(hist)
        # Range: the slowest and fastest week (non-spike days only) of the last 8 weeks.
        blocks = []
        for k in range(8):
            hi_d, lo_d = last - timedelta(days=7 * k), last - timedelta(days=7 * k + 7)
            wk = [s["change"] for s in base_days if lo_d < s["date"] <= hi_d]
            if len(wk) >= 4:
                blocks.append(sum(wk) / len(wk))
        lo_rate = min(blocks + [mid_rate])
        hi_rate = max(blocks + [mid_rate])
        now = series[-1]["out"]
        w(f"From {fmt(now)} outstanding on {iso(last)}, {n} days to {iso(target)}. Baseline: the "
          f"median daily change (adds - deletes - purchases - activations - gifts) of {len(hist)} "
          f"baseline days. Range: the slowest and fastest of the last {len(blocks)} weeks, "
          "spike days left out.")
        w("")
        w("| Case | Change per day | Outstanding on target date |")
        w("|---|---:|---:|")
        w(f"| Low (slowest recent week) | {fmt(lo_rate, 1)} | {fmt(now + lo_rate * n)} |")
        w(f"| Baseline (median day) | {fmt(mid_rate, 1)} | {fmt(now + mid_rate * n)} |")
        w(f"| High (fastest recent week) | {fmt(hi_rate, 1)} | {fmt(now + hi_rate * n)} |")
        w("")
        w("This assumes no spikes. Festivals, creator videos, a demo, the Personal Calendar near "
          "launch and the launch-day wishlist email all add on top, and nobody can schedule a "
          "viral post. Read it as \"where you land if nothing changes\", not a forecast.")
        if len(hist) < 14:
            warnings.append(f"The outlook rests on {len(hist)} baseline days; under 14 is thin.")
    w("")

    w("## Read with care")
    w("")
    w("- A spike next to a post or event is a date match, not proof of cause.")
    w("- Steam finalizes recent days later; the last few days may still move.")
    if tot["adds"] and tot["adds"] < 500:
        w(f"- Small sample: {fmt(tot['adds'])} adds in total. Day-to-day noise is large; read weeks, "
          "not days.")
    for x in warnings:
        w(f"- {x}")
    w("")

    md = "\n".join(lines)
    if a.out:
        try:
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(md)
        except OSError as e:
            raise InputError(f"{a.out}: cannot write ({e})")
        print(f"wrote {a.out}: {len(spikes)} spike days, baseline {base_adds:g} adds/day")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
