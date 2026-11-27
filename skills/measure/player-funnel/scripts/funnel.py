#!/usr/bin/env python3
"""Player funnel, cohort retention, playtime and quit points from a raw events CSV.

Reads one row per event with these columns (names matched loosely):
  user_id and/or anonymous_id   who did it (user_id wins; an anonymous_id seen with a
                                user_id on any row is merged into that user)
  event                         the event name
  timestamp                     ISO 8601, "YYYY-MM-DD HH:MM:SS", or Unix s / ms / us (UTC)
  properties                    optional JSON object (used by step filters and duration_s)
  source                        optional, or any column you name with --by

Reports (Markdown on stdout, or --out FILE):
  --steps a,b,c     ordered funnel: users per step, step and overall conversion,
                    drop-off and median time from the previous step
  --retention       cohorts by first-seen week (Monday, UTC): day 1, 7 and 30 returning share
  --playtime        total playtime per player in buckets
  --quits           last event before churn (no event in the last --churn-days days)
  --by COLUMN       split every report by a column (first value seen per player);
                    use properties.<key> for an event property

Step syntax: an event name, alternatives with |, and property filters in brackets:
  game_open|demo_open    level_complete[level=3]    session_end[duration_s>=600]
Filter operators: = != >= <= > <

Python 3 standard library only. Exit codes: 0 ok, 2 bad input.
"""

import argparse
import csv
import datetime as dt
import json
import re
import statistics
import sys
from collections import Counter, defaultdict

ALIASES = {
    "user_id": ["userid", "user", "playerid", "player", "distinctid", "customerid"],
    "anonymous_id": ["anonymousid", "anonid", "userpseudoid", "deviceid", "installid", "visitorid", "clientid"],
    "event": ["event", "eventname", "name", "eventtype", "action"],
    "timestamp": ["timestamp", "time", "ts", "eventtime", "eventtimestamp", "originaltimestamp", "receivedat",
                  "datetime", "createdat", "date"],
    "properties": ["properties", "props", "eventproperties", "params", "data"],
}
STEP_RE = re.compile(r"^\s*([^\[\]]+?)\s*(?:\[(.*)\])?\s*$")
FILTER_RE = re.compile(r"^\s*([A-Za-z0-9_.$-]+)\s*(>=|<=|!=|=|>|<)\s*(.*?)\s*$")
RET_DAYS = (1, 7, 30)
DETAIL_KEYS = ("level", "step", "stage", "wave", "chapter")
PLAY_BUCKETS = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 120), (120, 300), (300, None)]


class InputError(Exception):
    pass


def norm(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").replace("﻿", "").lower())


def parse_time(raw):
    s = (raw or "").strip()
    if not s:
        raise ValueError("empty timestamp")
    if re.fullmatch(r"\d{9,16}(\.\d+)?", s):
        v = float(s)
        if v > 1e14:
            v /= 1e6  # microseconds (Firebase event_timestamp)
        elif v > 1e11:
            v /= 1000.0
        return dt.datetime.fromtimestamp(v, dt.timezone.utc).replace(tzinfo=None)
    s = s.replace("Z", "+00:00").replace(" UTC", "+00:00")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        s += "T00:00:00"
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)  # nanoseconds to microseconds
    t = dt.datetime.fromisoformat(s)
    if t.tzinfo is not None:
        t = t.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return t


def parse_step(text):
    m = STEP_RE.match(text)
    if not m or not m.group(1).strip():
        raise InputError(f"bad step '{text}'")
    names = {n.strip() for n in m.group(1).split("|") if n.strip()}
    filters = []
    if m.group(2):
        for part in m.group(2).split(","):
            fm = FILTER_RE.match(part)
            if not fm:
                raise InputError(f"bad filter '{part}' in step '{text}' (use key=value, key>=10)")
            filters.append(fm.groups())
    return {"label": text.strip(), "names": names, "filters": filters}


def prop_matches(props, key, op, want):
    if key not in props:
        return False
    have = props[key]
    if op in ("=", "!="):
        same = str(have).lower() == want.lower()
        try:
            same = same or float(have) == float(want)
        except (TypeError, ValueError):
            pass
        return same if op == "=" else not same
    try:
        h, w = float(have), float(want)
    except (TypeError, ValueError):
        return False
    return {">=": h >= w, "<=": h <= w, ">": h > w, "<": h < w}[op]


def step_matches(step, ev):
    if ev["event"] not in step["names"]:
        return False
    return all(prop_matches(ev["props"], k, op, v) for k, op, v in step["filters"])


def load(path, by):
    try:
        fh = open(path, newline="", encoding="utf-8-sig")
    except OSError as e:
        raise InputError(f"{path}: {e.strerror}")
    with fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise InputError(f"{path}: empty file or no header")
        cols = {}
        normed = {norm(h): h for h in reader.fieldnames}
        for key, names in ALIASES.items():
            for n in [norm(key)] + names:
                if n in normed:
                    cols[key] = normed[n]
                    break
        if "user_id" not in cols and "anonymous_id" not in cols:
            raise InputError(f"{path}: needs a user_id or anonymous_id column (found {reader.fieldnames})")
        for need in ("event", "timestamp"):
            if need not in cols:
                raise InputError(f"{path}: needs a {need} column (found {reader.fieldnames})")
        by_col = None
        if by and not by.startswith("properties."):
            by_col = normed.get(norm(by)) or (normed.get("utmsource") if norm(by) == "source" else None)
            if not by_col:
                raise InputError(f"{path}: --by column '{by}' not found (found {reader.fieldnames})")
        rows, links = [], {}
        for line, r in enumerate(reader, start=2):
            uid = (r.get(cols.get("user_id"), "") or "").strip() if "user_id" in cols else ""
            aid = (r.get(cols.get("anonymous_id"), "") or "").strip() if "anonymous_id" in cols else ""
            if not uid and not aid:
                continue  # rows before consent or server rows without an ID
            if uid and aid:
                links.setdefault(aid, uid)
            name = (r.get(cols["event"]) or "").strip()
            if not name:
                raise InputError(f"{path}:{line}: empty event name")
            try:
                ts = parse_time(r.get(cols["timestamp"]))
            except ValueError as e:
                raise InputError(f"{path}:{line}: bad timestamp '{r.get(cols['timestamp'])}' ({e})")
            props = {}
            raw = (r.get(cols["properties"]) or "").strip() if "properties" in cols else ""
            if raw:
                try:
                    props = json.loads(raw)
                except json.JSONDecodeError:
                    raise InputError(f"{path}:{line}: properties is not JSON: {raw[:60]}")
                if not isinstance(props, dict):
                    props = {}
            if by and by.startswith("properties."):
                seg = props.get(by.split(".", 1)[1])
            else:
                seg = r.get(by_col) if by_col else None
            seg = str(seg).strip() if seg not in (None, "") else ""
            rows.append({"uid": uid, "aid": aid, "event": name, "ts": ts, "props": props, "seg": seg})
    if not rows:
        raise InputError(f"{path}: no event rows with a user ID")
    players = defaultdict(list)
    for r in rows:
        players[r["uid"] or links.get(r["aid"], "anon:" + r["aid"])].append(r)
    for evs in players.values():
        evs.sort(key=lambda e: e["ts"])
    return players, len(rows)


def segment_of(evs):
    for e in evs:
        if e["seg"]:
            return e["seg"]
    return "(none)"


def groups(players, by):
    out = {"All players": list(players)}
    if by:
        split = defaultdict(list)
        for p, evs in players.items():
            split[segment_of(evs)].append(p)
        for k in sorted(split, key=lambda k: (-len(split[k]), k)):
            out[f"{by} = {k}"] = split[k]
    return out


def pct(n, d):
    return "-" if not d else f"{100.0 * n / d:.1f}%"


def human(seconds):
    if seconds is None:
        return "-"
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.1f}m"
    if seconds < 172800:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def walk(evs, steps, window):
    """Deepest ordered path for one player. Tries every start, keeps the deepest (then earliest)."""
    best = (0, [])
    for i, e in enumerate(evs):
        if not step_matches(steps[0], e):
            continue
        times, k = [e["ts"]], 1
        for e2 in evs[i + 1:]:
            if k == len(steps):
                break
            if window and e2["ts"] - times[0] > window:
                break
            if step_matches(steps[k], e2):
                times.append(e2["ts"])
                k += 1
        if k > best[0]:
            best = (k, times)
        if k == len(steps):
            break
    return best


def funnel_table(players, ids, steps, window, min_n):
    reached = [0] * len(steps)
    gaps = [[] for _ in steps]
    for p in ids:
        depth, times = walk(players[p], steps, window)
        for k in range(depth):
            reached[k] += 1
            if k:
                gaps[k].append((times[k] - times[k - 1]).total_seconds())
    lines = ["| # | Step | Players | Dropped off | Step conv. | Overall conv. | Median time from previous |",
             "|---|---|---|---|---|---|---|"]
    worst = None
    for k, s in enumerate(steps):
        prev = reached[k - 1] if k else reached[0]
        drop = prev - reached[k] if k else 0
        if k and prev and (worst is None or drop / prev > worst[1]):
            worst = (k, drop / prev)
        med = statistics.median(gaps[k]) if gaps[k] else None
        lines.append(f"| {k + 1} | `{s['label']}` | {reached[k]} | {drop if k else '-'} | "
                     f"{pct(reached[k], prev) if k else '-'} | {pct(reached[k], reached[0])} | "
                     f"{human(med) if k else '-'} |")
    notes = []
    if reached[0] < min_n:
        notes.append(f"Too small: {reached[0]} players entered (under {min_n}). Do not compare rates yet.")
    elif worst:
        k = worst[0]
        notes.append(f"Biggest drop: {reached[k - 1] - reached[k]} of {reached[k - 1]} players "
                     f"({worst[1] * 100:.1f}%) who reached step {k} `{steps[k - 1]['label']}` "
                     f"never reached step {k + 1} `{steps[k]['label']}`.")
    return lines, notes, reached


def retention_table(players, ids, data_end, rolling, entry, ret, min_n):
    cohorts = defaultdict(list)
    for p in ids:
        evs = players[p]
        first = next((e for e in evs if entry is None or step_matches(entry, e)), None)
        if first is None:
            continue
        day0 = first["ts"].date()
        days = {(e["ts"].date() - day0).days for e in evs
                if e["ts"] >= first["ts"] and (ret is None or step_matches(ret, e))}
        week = day0 - dt.timedelta(days=day0.weekday())
        cohorts[week].append((day0, days))
    head = "| Cohort (week of) | Players | " + " | ".join(f"Day {n}" for n in RET_DAYS) + " | Note |"
    lines = [head, "|---|---|" + "---|" * len(RET_DAYS) + "---|"]
    totals = {n: [0, 0] for n in RET_DAYS}
    for week in sorted(cohorts):
        members = cohorts[week]
        cells, partial = [], False
        for n in RET_DAYS:
            elig = [d for d0, d in members if d0 + dt.timedelta(days=n) <= data_end]
            if not elig:
                cells.append("-")
                continue
            back = sum(1 for d in elig if (max(d) >= n if rolling else n in d))
            totals[n][0] += back
            totals[n][1] += len(elig)
            partial = partial or len(elig) < len(members)
            cells.append(pct(back, len(elig)) + (f" (of {len(elig)})" if len(elig) < len(members) else ""))
        note = []
        if len(members) < min_n:
            note.append(f"too small (under {min_n})")
        if partial:
            note.append("partial: later days not reached yet")
        lines.append(f"| {week.isoformat()} | {len(members)} | " + " | ".join(cells) + f" | {'; '.join(note)} |")
    n_all = sum(len(m) for m in cohorts.values())
    lines.append(f"| **All (weighted)** | {n_all} | " +
                 " | ".join(pct(*totals[n]) for n in RET_DAYS) + " | |")
    return lines, totals, n_all


def sessions_minutes(evs, gap_min, played):
    """Playtime in minutes: sum of session_end duration_s when present, else event spans
    from the first game event on. None when the player never played."""
    first = next((i for i, e in enumerate(evs) if e["event"] in played), None)
    if first is None:
        return None, False
    evs = evs[first:]
    ends = [e["props"].get("duration_s") for e in evs if e["event"] == "session_end"]
    ends = [float(x) for x in ends if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace(".", "", 1).isdigit())]
    if ends:
        return sum(ends) / 60.0, True
    total, start, last = 0.0, None, None
    for e in evs:
        if last is None or (e["ts"] - last).total_seconds() > gap_min * 60:
            if start is not None:
                total += (last - start).total_seconds()
            start = e["ts"]
        last = e["ts"]
    if start is not None:
        total += (last - start).total_seconds()
    return total / 60.0, False


def playtime_table(players, ids, gap_min, played):
    mins, from_end = [], 0
    for p in ids:
        m, used = sessions_minutes(players[p], gap_min, played)
        if m is None:
            continue
        mins.append(m)
        from_end += used
    lines = ["| Total playtime | Players | Share |", "|---|---|---|"]
    for lo, hi in PLAY_BUCKETS:
        n = sum(1 for m in mins if m >= lo and (hi is None or m < hi))
        label = f"{lo} to {hi} min" if hi else f"{lo} min or more"
        lines.append(f"| {label} | {n} | {pct(n, len(mins))} |")
    med = statistics.median(mins) if mins else 0
    q = statistics.quantiles(mins, n=4) if len(mins) >= 4 else [med, med, med]
    if not mins:
        return lines, f"No player sent any of {', '.join(sorted(played))}. Set --played to your game events."
    note = (f"{len(mins)} players who played. Median {med:.1f} min, P25 {q[0]:.1f}, P75 {q[2]:.1f}. "
            f"{from_end} of them had `session_end` `duration_s`; the rest use first to last event "
            f"with a {gap_min}-minute gap rule, which undercounts the last minutes of each session.")
    return lines, note


def quits_table(players, ids, data_end_ts, churn_days, top, ignore, after):
    cut = data_end_ts - dt.timedelta(days=churn_days)
    last = Counter()
    eligible = churned = 0
    for p in ids:
        evs = players[p]
        if after and not any(step_matches(after, e) for e in evs):
            continue
        if evs[0]["ts"] > cut:
            continue  # too new to call churned
        eligible += 1
        if evs[-1]["ts"] <= cut:
            churned += 1
            e = next((x for x in reversed(evs) if x["event"] not in ignore), evs[-1])
            detail = ", ".join(f"{k} {e['props'][k]}" for k in DETAIL_KEYS if e["props"].get(k) not in (None, ""))
            last[e["event"] + (f" ({detail})" if detail else "")] += 1
    lines = ["| Last event before churn | Players | Share of churned |", "|---|---|---|"]
    for name, n in last.most_common(top):
        lines.append(f"| `{name}` | {n} | {pct(n, churned)} |")
    who = f"players who did `{after['label']}`" if after else "players"
    note = (f"{churned} of {eligible} {who} churned (no event in the last {churn_days} days of the data; "
            f"players first seen in those days are left out). Skipped as last event: {', '.join(sorted(ignore))}.")
    return lines, note


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--events", required=True, help="events CSV (one row per event)")
    ap.add_argument("--steps", help="ordered funnel steps, comma separated (2 to 10)")
    ap.add_argument("--window", type=float, help="hours from the first step to finish all steps (default: no limit)")
    ap.add_argument("--retention", action="store_true", help="cohort table of day 1/7/30 returning share")
    ap.add_argument("--entry-event", help="event that starts a cohort (default: any event), e.g. game_open")
    ap.add_argument("--return-event", help="event that counts as a return (default: any event), e.g. session_start")
    ap.add_argument("--rolling", action="store_true", help="day N counts a return on day N or later (default: exactly day N)")
    ap.add_argument("--playtime", action="store_true", help="total playtime per player, in buckets")
    ap.add_argument("--played", default="game_open,session_start,session_end",
                    help="events that mean a player played (default game_open,session_start,session_end)")
    ap.add_argument("--session-gap", type=int, default=30, help="minutes of no events that end a session (default 30)")
    ap.add_argument("--quits", action="store_true", help="last event before churn")
    ap.add_argument("--churn-days", type=int, default=7, help="days with no event that count as churned (default 7)")
    ap.add_argument("--quits-after", help="only players who did this step, e.g. game_open")
    ap.add_argument("--ignore", default="session_start,session_end,heartbeat,app_crash",
                    help="events skipped when finding the last real event (default session_start,session_end,heartbeat,app_crash)")
    ap.add_argument("--top", type=int, default=10, help="rows in the quits table (default 10)")
    ap.add_argument("--by", help="split by this column (first value per player), or properties.<key>")
    ap.add_argument("--min-players", type=int, default=30, help="flag funnels and cohorts under this size (default 30)")
    ap.add_argument("--out", help="write the Markdown report here instead of stdout")
    a = ap.parse_args()

    try:
        if not (a.steps or a.retention or a.playtime or a.quits):
            raise InputError("choose at least one report: --steps, --retention, --playtime or --quits")
        steps = []
        if a.steps:
            steps = [parse_step(s) for s in re.split(r",(?![^\[]*\])", a.steps) if s.strip()]
            if not 2 <= len(steps) <= 10:
                raise InputError(f"--steps needs 2 to 10 steps (got {len(steps)})")
        if a.window is not None and a.window <= 0:
            raise InputError("--window must be a positive number of hours")
        entry = parse_step(a.entry_event) if a.entry_event else None
        ret = parse_step(a.return_event) if a.return_event else None
        after = parse_step(a.quits_after) if a.quits_after else None
        played = {x.strip() for x in a.played.split(",") if x.strip()}
        ignore = {x.strip() for x in a.ignore.split(",") if x.strip()}
        players, n_rows = load(a.events, a.by)
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    all_ts = [e["ts"] for evs in players.values() for e in evs]
    t0, t1 = min(all_ts), max(all_ts)
    seen = {e["event"] for evs in players.values() for e in evs}
    out = [f"# Player funnel report", "",
           f"Source: `{a.events}`. {n_rows} events, {len(players)} players, "
           f"{t0.date().isoformat()} to {t1.date().isoformat()} (UTC).", ""]
    warns = []
    for s in steps + [x for x in (entry, ret, after) if x]:
        missing = s["names"] - seen
        if missing:
            warns.append(f"No `{'`, `'.join(sorted(missing))}` events in the file (step `{s['label']}`). Check the name.")
    window = dt.timedelta(hours=a.window) if a.window else None
    grp = groups(players, a.by)

    if steps:
        out += ["## Funnel", "",
                f"Ordered steps, other events allowed between them. Window: "
                f"{f'{a.window:g} hours from the first step' if a.window else 'none'}. "
                "Counts players, not events.", ""]
        for name, ids in grp.items():
            lines, notes, _ = funnel_table(players, ids, steps, window, a.min_players)
            out += [f"### {name}", ""] + lines + [""] + [f"- {n}" for n in notes] + [""]

    if a.retention:
        kind = "rolling (day N or later)" if a.rolling else "exact day (returned on day N)"
        first_what = f"`{entry['label']}`" if entry else "event"
        return_what = f"`{ret['label']}`" if ret else "any event"
        out += ["## Retention", "",
                f"Cohort = week (Monday, UTC) of the first {first_what}. "
                f"Return = {return_what}, "
                f"{kind}. Day N is counted only for players whose day N is inside the data "
                f"(data ends {t1.date().isoformat()}).", ""]
        for name, ids in grp.items():
            lines, _, n_all = retention_table(players, ids, t1.date(), a.rolling, entry, ret, a.min_players)
            out += [f"### {name}", ""] + lines + [""]
            if n_all < a.min_players:
                out += [f"- Too small: {n_all} players in all cohorts (under {a.min_players}).", ""]

    if a.playtime:
        out += ["## Playtime", ""]
        for name, ids in grp.items():
            lines, note = playtime_table(players, ids, a.session_gap, played)
            out += [f"### {name}", ""] + lines + ["", f"- {note}", ""]

    if a.quits:
        out += ["## Where players quit", ""]
        for name, ids in grp.items():
            lines, note = quits_table(players, ids, t1, a.churn_days, a.top, ignore, after)
            out += [f"### {name}", ""] + lines + ["", f"- {note}", ""]

    out += ["## Read with care", "",
            f"- Groups under {a.min_players} players are flagged. Two rates that differ by a few points "
            "on a few hundred players can be noise.",
            "- This shows what goes with what, not why. A source with low retention may bring a "
            "different audience, not a worse one.",
            "- Players on two devices with no shared user_id count twice."]
    out += [f"- {w}" for w in warns] + [""]
    text = "\n".join(out)
    if a.out:
        try:
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as e:
            print(f"error: {a.out}: {e.strerror}", file=sys.stderr)
            return 2
        print(f"wrote {a.out}")
    else:
        print(text)
    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
