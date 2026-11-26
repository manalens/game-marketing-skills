#!/usr/bin/env python3
"""Attribution report: which sources, campaigns and posts get credit for wishlists and sales.

Reads Steam UTM Analytics CSV exports and/or Manalens get_attribution results saved as JSON,
plus optional spend and sales CSVs. Writes a Markdown report:

- Steam UTM by group: visits, wishlists, purchases, activations, revenue (from --sales),
  rates, share of total, cost per wishlist and per purchase (from --costs), and a read of
  each group with the 2 x sqrt(n) rule.
- Manalens credit by group for each model file, and a side-by-side of credit share by model
  when two or three model files are given.

Python 3 standard library only. Exit codes: 0 ok, 2 bad input.
"""

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import unicodedata

TOTAL_RE = re.compile(r"^(grand )?totals?:?$", re.I)
NONE = "(none)"


class InputError(Exception):
    pass


def norm(name):
    """Header to lowercase letters and digits only, as Manalens normalizeHeader does."""
    text = unicodedata.normalize("NFKC", (name or "").replace("﻿", "")).lower()
    return re.sub(r"[^a-z0-9]", "", text)


# Steam UTM Analytics headers, matched by normalized name. Same aliases as the Manalens parser
# (packages/shared/src/steam-utm.ts). Valve does not document the exact header text.
STEAM_ALIASES = {
    "day": ["date", "day", "visitdate", "reportdate", "datepst", "dateutc"],
    "app_id": ["appid", "app", "steamappid", "applicationid"],
    "utm_source": ["utmsource", "source"],
    "utm_medium": ["utmmedium", "medium"],
    "utm_campaign": ["utmcampaign", "campaign"],
    "utm_content": ["utmcontent", "content"],
    "utm_term": ["utmterm", "term"],
    "total_visits": ["totalvisits", "visits", "totalvisit"],
    "trusted_visits": ["trustedvisits", "trustedvisit"],
    "tracked_visits": ["trackedvisits", "trackedvisit"],
    "wishlists": ["wishlists", "wishlist", "wishlistadds", "wishlistadditions", "wishlisted"],
    "purchases": ["purchases", "purchase", "sales", "purchased"],
    "activations": ["activations", "activation", "activated"],
}
STEAM_METRICS = ["total_visits", "trusted_visits", "tracked_visits", "wishlists", "purchases", "activations"]

# Key columns for --costs and --sales, per dimension. "group" style names work for any dimension.
KEY_ALIASES = {
    "source": ["utmsource", "source", "channel", "platform"],
    "medium": ["utmmedium", "medium"],
    "campaign": ["utmcampaign", "campaign", "beat"],
    "content": ["utmcontent", "content", "postid", "post", "creator", "video"],
}
GENERIC_KEYS = ["group", "name", "key", "dimension"]
SPEND_ALIASES = ["spend", "cost", "costs", "amount", "budget", "fee", "fees", "spendusd", "costusd", "amountspent"]
REVENUE_ALIASES = ["revenue", "netrevenue", "netsales", "sales", "grosssales", "revenueusd", "netsalesusd", "amount"]
UNITS_ALIASES = ["units", "netunits", "copies", "purchases"]

DIMENSIONS = {
    "source": ["utm_source"],
    "medium": ["utm_medium"],
    "campaign": ["utm_campaign"],
    "content": ["utm_content"],
    "source+campaign": ["utm_source", "utm_campaign"],
}


# ---------------------------------------------------------------- reading

def read_csv(path, hint):
    """Read a CSV with comma, semicolon or tab separators, a BOM and title lines above the header.

    hint: normalized header names; the header is the first of the first 6 lines that has one.
    Returns (headers, rows as dicts, first data line number).
    """
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            text = fh.read()
    except OSError as err:
        raise InputError(f"{path}: cannot read ({err.strerror})")
    if not text.strip():
        raise InputError(f"{path}: file is empty")
    lines = [ln for ln in text[:8192].splitlines() if ln.strip()][:6]
    delim = max([",", ";", "\t"], key=lambda d: max(ln.count(d) for ln in lines))
    records = [r for r in csv.reader(io.StringIO(text), delimiter=delim) if any(c.strip() for c in r)]
    idx = None
    for i, rec in enumerate(records[:6]):
        if any(norm(c) in hint for c in rec):
            idx = i
            break
    if idx is None:
        raise InputError(f"{path}: no header row found in the first lines")
    headers = [c.strip() for c in records[idx]]
    rows = [{h: (rec[i].strip() if i < len(rec) else "") for i, h in enumerate(headers)}
            for rec in records[idx + 1:]]
    return headers, rows, idx + 2


def find_col(headers, names, used=()):
    for h in headers:
        if h not in used and norm(h) in names:
            return h
    return None


def to_num(value, path, line, col):
    v = (value or "").strip().replace(" ", "").replace(" ", "")
    v = re.sub(r"^[$€£]|(usd|eur|gbp)$", "", v, flags=re.I)
    if v in ("", "-", "n/a", "N/A"):
        return 0.0
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", v):
        v = v.replace(",", "")
    elif re.fullmatch(r"-?\d+,\d{1,2}", v):
        v = v.replace(",", ".")
    try:
        return float(v)
    except ValueError:
        raise InputError(f"{path} line {line}: '{value}' in column '{col}' is not a number")


def clean_key(value):
    v = (value or "").strip().lower()
    return v if v else NONE


def load_steam(paths, by, warnings):
    """Sum Steam UTM rows per group. Returns ({group: metrics}, metric names present)."""
    hint = {"utmsource", "source", "utmcampaign", "campaign", "totalvisits", "visits"}
    groups, present, seen, variants, dups = {}, set(), {}, {}, {}
    dims = DIMENSIONS[by]
    for path in paths:
        headers, rows, first = read_csv(path, hint)
        mp, used = {}, set()
        for field, names in STEAM_ALIASES.items():
            col = find_col(headers, names, used)
            if col:
                mp[field] = col
                used.add(col)
        missing = [d for d in dims if d not in mp]
        if missing:
            raise InputError(f"{path}: no {' or '.join(missing)} column to group by '{by}' "
                             f"(headers: {', '.join(headers)}). Export with that column, or pick another --by.")
        metrics = [m for m in STEAM_METRICS if m in mp]
        if not metrics:
            raise InputError(f"{path}: no visits, wishlists or purchases column (headers: {', '.join(headers)})")
        present.update(metrics)
        tag_dims = [d for d in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term") if d in mp]
        if by != "content" and "utm_content" in mp:
            warnings.append(f"`{os.path.basename(path)}` has a UTM Content column. Steam hides small "
                            "combinations, so grouping per-post rows by a wider tag can undercount. "
                            "An export without UTM Content gives fuller totals for source and campaign.")
        for n, row in enumerate(rows, start=first):
            cells = [row.get(mp[d], "") for d in tag_dims + (["day"] if "day" in mp else [])]
            if any(TOTAL_RE.match(c.strip()) for c in cells if c):
                continue
            if not any(row.get(mp[d], "").strip() for d in tag_dims):
                continue
            key = " / ".join(clean_key(row.get(mp[d])) for d in dims)
            raw = " / ".join((row.get(mp[d]) or "").strip() for d in dims)
            variants.setdefault(key, set()).add(raw)
            day = row.get(mp["day"], "").strip() if "day" in mp else ""
            dkey = (day,) + tuple(row.get(mp[d], "").strip().lower() for d in tag_dims)
            if day and dkey in seen and seen[dkey] != path:
                pair = (os.path.basename(seen[dkey]), os.path.basename(path))
                dups[pair] = dups.get(pair, 0) + 1
            seen.setdefault(dkey, path)
            acc = groups.setdefault(key, {m: 0.0 for m in STEAM_METRICS})
            for m in metrics:
                acc[m] += to_num(row.get(mp[m]), path, n, mp[m])
    for (a, b), n in dups.items():
        warnings.append(f"Steam: {n} rows (same day and tags) are in both {a} and {b}. They are counted "
                        "twice; drop the older export and run again.")
    for key, raws in variants.items():
        if len(raws) > 1:
            warnings.append(f"Steam: {', '.join(sorted(repr(r) for r in raws))} differ only in case and are "
                            f"added up as `{key}`. Use one spelling in your links.")
    if not groups:
        raise InputError("Steam: no data rows with UTM values in " + ", ".join(paths))
    return groups, present


def load_keyed(path, by, value_aliases, what):
    """Read a costs or sales CSV: a key column for the dimension and value column(s)."""
    dims = by.split("+")
    hint = set(GENERIC_KEYS)
    for names in value_aliases.values():
        hint.update(names)
    for d in dims:
        hint.update(KEY_ALIASES[d])
    headers, rows, first = read_csv(path, hint)
    key_cols = []
    if len(dims) > 1:
        key_cols = [find_col(headers, KEY_ALIASES[d]) for d in dims]
        if None in key_cols:
            key_cols = []
    if not key_cols:
        col = find_col(headers, KEY_ALIASES[dims[0]] + GENERIC_KEYS) if len(dims) == 1 else find_col(headers, GENERIC_KEYS)
        if not col:
            raise InputError(f"{path}: no key column for '{by}'. Name it {dims[0]} (or group); "
                             f"headers: {', '.join(headers)}")
        key_cols = [col]
    out = {}
    for field, names in value_aliases.items():
        col = find_col(headers, names, key_cols)
        if col:
            out[field] = col
    if not out:
        raise InputError(f"{path}: no {what} column (headers: {', '.join(headers)})")
    data = {}
    for n, row in enumerate(rows, start=first):
        if len(key_cols) == 1:
            raw = row.get(key_cols[0], "").strip()
            if not raw or TOTAL_RE.match(raw):
                continue
            key = " / ".join(clean_key(p) for p in raw.split("/")) if len(dims) > 1 else clean_key(raw)
        else:
            parts = [row.get(c, "") for c in key_cols]
            if not any(p.strip() for p in parts) or any(TOTAL_RE.match(p.strip()) for p in parts):
                continue
            key = " / ".join(clean_key(p) for p in parts)
        acc = data.setdefault(key, {f: 0.0 for f in out})
        for field, col in out.items():
            acc[field] += to_num(row.get(col), path, n, col)
    return data


def load_manalens(path):
    """Read a get_attribution result. Accepts the MCP structured result {filters, rows}, the MCP
    envelope {content: [{type: text, text}]}, the REST response {model, group_by, rows}, or a list."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except OSError as err:
        raise InputError(f"{path}: cannot read ({err.strerror})")
    except json.JSONDecodeError as err:
        raise InputError(f"{path}: not valid JSON (line {err.lineno}: {err.msg})")
    if isinstance(data, dict) and "structuredContent" in data:
        data = data["structuredContent"]
    elif isinstance(data, dict) and "content" in data and "rows" not in data:
        texts = [c.get("text", "") for c in data.get("content", []) if isinstance(c, dict)]
        try:
            data = json.loads(texts[0])
        except (IndexError, json.JSONDecodeError):
            msg = (texts[0][:120] if texts else "").strip()
            raise InputError(f"{path}: the MCP result is not a report" + (f": '{msg}'" if msg else "")
                             + ". Fix the call and save the result again.")
    if isinstance(data, list):
        meta, rows = {}, data
    elif isinstance(data, dict) and isinstance(data.get("rows"), list):
        meta = dict(data.get("filters") or {})
        for k in ("model", "group_by", "conversion_event", "lookback_days", "half_life_days"):
            if k in data and k not in meta:
                meta[k] = data[k]
        rows = data["rows"]
    else:
        raise InputError(f"{path}: expected a get_attribution result with a 'rows' list")
    credit = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or "dimension" not in row or "conversions" not in row:
            raise InputError(f"{path}: row {i + 1} needs 'dimension' and 'conversions'")
        try:
            conv = float(row["conversions"])
            rev = float(row.get("revenue") or 0)
        except (TypeError, ValueError):
            raise InputError(f"{path}: row {i + 1} has a value that is not a number")
        key = clean_key(str(row["dimension"]))
        acc = credit.setdefault(key, {"conversions": 0.0, "revenue": 0.0})
        acc["conversions"] += conv
        acc["revenue"] += rev
    label = str(meta.get("model") or os.path.splitext(os.path.basename(path))[0])
    return {"path": path, "label": label, "meta": meta, "credit": credit}


# ---------------------------------------------------------------- formatting

def fnum(v, digits=0):
    if v is None:
        return "-"
    if digits == 0 and abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}"
    return f"{v:,.{max(digits, 1)}f}"


def pct(a, b):
    return f"{100.0 * a / b:.1f}%" if b else "-"


def money(v):
    return "-" if v is None else f"{v:,.2f}"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def noise(n):
    return 2 * math.sqrt(n) if n > 0 else 0


def too_small(n, small):
    """True when chance alone (2 x sqrt(n)) can move the count by half or more: n <= 16 by default."""
    return n <= small


def read_column(ordered, metric, small):
    """For each group in order: too small, clearly ahead of the next group, or not clearly ahead."""
    notes = []
    for i, (_, m) in enumerate(ordered):
        a = m[metric]
        if too_small(a, small):
            notes.append("too small")
            continue
        nxt = ordered[i + 1][1][metric] if i + 1 < len(ordered) else None
        if nxt is None:
            notes.append("ok")
        elif a > nxt + noise(nxt):
            notes.append("ahead of next")
        else:
            notes.append("tied with next")
    return notes


def roll_up(ordered, top, fields):
    if top <= 0 or len(ordered) <= top:
        return ordered, 0
    rest = ordered[top:]
    other = {f: (sum(m.get(f) or 0 for _, m in rest) if any(m.get(f) is not None for _, m in rest) else None)
             for f in fields}
    return ordered[:top] + [(f"(other {len(rest)} groups)", other)], len(rest)


# ---------------------------------------------------------------- report

def steam_section(groups, present, by, costs, sales, top, small, warnings):
    lines = [f"## Steam UTM by {by}", ""]
    rate_base = "tracked_visits" if "tracked_visits" in present else "total_visits"
    for key, s in (sales or {}).items():
        if key not in groups:
            warnings.append(f"Sales: `{key}` matches no Steam group; its revenue is left out of the table.")
    for key, c in (costs or {}).items():
        if key not in groups:
            warnings.append(f"Costs: `{key}` ({money(c.get('spend'))}) matches no Steam group. "
                            "Check the spelling against the UTM tag.")
    fields = STEAM_METRICS + ["revenue", "spend"]
    for key, m in groups.items():
        m["revenue"] = (sales or {}).get(key, {}).get("revenue") if sales else None
        m["spend"] = (costs or {}).get(key, {}).get("spend") if costs else None
    metric = "wishlists" if "wishlists" in present else ("purchases" if "purchases" in present else rate_base)
    ordered = sorted(groups.items(), key=lambda kv: (-kv[1].get(metric, 0), kv[0]))
    reads = read_column(ordered, metric, small)
    ordered, hidden = roll_up(ordered, top, fields)
    reads = reads[:len(ordered) - (1 if hidden else 0)] + (["-"] if hidden else [])
    tot = {f: sum((m.get(f) or 0) for m in groups.values()) for f in fields}
    paid = [m for m in groups.values() if m.get("spend")]
    tot["paid_wishlists"] = sum(m["wishlists"] for m in paid)
    tot["paid_purchases"] = sum(m["purchases"] for m in paid)
    tot["paid_revenue"] = sum(m.get("revenue") or 0 for m in paid)

    head = [by, "visits"]
    if rate_base == "tracked_visits":
        head.append("tracked visits")
    has_w, has_p = "wishlists" in present, "purchases" in present
    if has_w:
        head += ["wishlists", "wishlist rate", "share of wishlists"]
    if has_p:
        head += ["purchases", "purchase rate", "share of purchases"]
    if "activations" in present:
        head.append("activations")
    if sales:
        head += ["revenue", "share of revenue"]
    if costs:
        head += ["spend"] + (["cost per wishlist"] if has_w else []) + (["cost per purchase"] if has_p else [])
        if sales:
            head.append("revenue / spend")
    head.append("read")

    def row(name, m, read):
        r = [name, fnum(m["total_visits"])]
        if rate_base == "tracked_visits":
            r.append(fnum(m["tracked_visits"]))
        if has_w:
            r += [fnum(m["wishlists"]), pct(m["wishlists"], m[rate_base]), pct(m["wishlists"], tot["wishlists"])]
        if has_p:
            r += [fnum(m["purchases"]), pct(m["purchases"], m[rate_base]), pct(m["purchases"], tot["purchases"])]
        if "activations" in present:
            r.append(fnum(m["activations"]))
        if sales:
            r += [money(m.get("revenue")), pct(m.get("revenue") or 0, tot["revenue"]) if m.get("revenue") else "-"]
        if costs:
            sp = m.get("spend")
            pre = "paid_" if "paid_wishlists" in m else ""
            w, pu, rv = m[pre + "wishlists"], m[pre + "purchases"], m.get(pre + "revenue")
            r.append(money(sp))
            if has_w:
                r.append(money(sp / w) if sp and w else ("no wishlists" if sp else "-"))
            if has_p:
                r.append(money(sp / pu) if sp and pu else ("no purchases" if sp else "-"))
            if sales:
                r.append(f"{rv / sp:.2f}" if sp and rv else "-")
        r.append(read)
        return r

    rows = [row(k, m, rd) for (k, m), rd in zip(ordered, reads)]
    rows.append(row("**Total**", tot, ""))
    lines += table(head, rows)
    lines += ["", f"Rates are per {rate_base.replace('_', ' ')}. Groups are sorted by {metric}. "
              f"\"too small\": {small} or fewer {metric}, so chance alone can move the count by half. "
              "\"ahead of next\": more than the next group's count plus 2 x its square root. "
              "\"tied with next\": not clearly different yet."]
    if costs:
        lines += ["", "On the Total row, cost per wishlist, cost per purchase and revenue / spend count only "
                  "the groups with spend."]
        lines += ["", "Cost per wishlist from UTM data is an upper bound: Steam counts only tagged clicks by "
                  "signed-in players within 72 hours, so the true cost is lower."]
    lines.append("")
    return lines


def manalens_sections(models, costs, top, small, warnings):
    lines = []
    if not models:
        return lines
    metas = [m["meta"] for m in models]
    for k in ("conversion_event", "group_by", "date_from", "date_to", "lookback_days"):
        vals = {str(meta.get(k)) for meta in metas if meta.get(k) is not None}
        if len(vals) > 1:
            warnings.append(f"Manalens files differ in {k} ({', '.join(sorted(vals))}). Compare models on the "
                            "same event, grouping, dates and lookback.")
    sums = [sum(v["conversions"] for v in m["credit"].values()) for m in models]
    if len(sums) > 1 and max(sums) - min(sums) > 0.01 * max(sums) + 0.5:
        warnings.append("Total credit differs between the model files (" + ", ".join(fnum(x, 1) for x in sums)
                        + "). Every model splits the same conversions, so the runs used different events, dates, "
                        "lookbacks or filters, or a result was cut at 100 groups. Rerun them with the same inputs.")
    labels = [m["label"] for m in models]
    if len(set(labels)) < len(labels):
        for m in models:
            m["label"] = f"{m['label']} ({os.path.splitext(os.path.basename(m['path']))[0]})"
    group = metas[0].get("group_by", "group")
    event = metas[0].get("conversion_event", "conversion")
    for m in models:
        credit = m["credit"]
        tot_c = sum(v["conversions"] for v in credit.values())
        tot_r = sum(v["revenue"] for v in credit.values())
        has_rev = tot_r != 0
        ordered = sorted(credit.items(), key=lambda kv: (-kv[1]["conversions"], kv[0]))
        reads = read_column(ordered, "conversions", small)
        ordered, hidden = roll_up(ordered, top, ["conversions", "revenue"])
        reads = reads[:len(ordered) - (1 if hidden else 0)] + (["-"] if hidden else [])
        head = [group, f"{event} credit", "share"] + (["revenue", "share of revenue"] if has_rev else [])
        if costs:
            head += ["spend", "cost per conversion"] + (["revenue / spend"] if has_rev else [])
        head.append("read")
        rows = []
        for (k, v), rd in zip(ordered, reads):
            r = [k, fnum(v["conversions"], 1), pct(v["conversions"], tot_c)]
            if has_rev:
                r += [money(v["revenue"]), pct(v["revenue"], tot_r)]
            if costs:
                sp = costs.get(k, {}).get("spend")
                r += [money(sp), money(sp / v["conversions"]) if sp and v["conversions"] else "-"]
                if has_rev:
                    r.append(f"{v['revenue'] / sp:.2f}" if sp and v["revenue"] else "-")
            r.append(rd)
            rows.append(r)
        total = ["**Total**", fnum(tot_c, 1), "100%"] + ([money(tot_r), "100%"] if has_rev else [])
        if costs:
            paid = [k for k in credit if costs.get(k, {}).get("spend")]
            sp = sum(costs[k]["spend"] for k in paid)
            pc = sum(credit[k]["conversions"] for k in paid)
            pr = sum(credit[k]["revenue"] for k in paid)
            total += [money(sp), money(sp / pc) if sp and pc else "-"]
            if has_rev:
                total.append(f"{pr / sp:.2f}" if sp and pr else "-")
        rows.append(total + [""])
        meta = m["meta"]
        extra = ", ".join(f"{k} {meta[k]}" for k in ("date_from", "date_to", "lookback_days", "half_life_days")
                          if meta.get(k) not in (None, ""))
        lines += [f"## Manalens credit, model `{m['label']}`", "", f"Event `{event}`, grouped by `{group}`"
                  + (f"; {extra}" if extra else "") + ".", ""]
        lines += table(head, rows)
        lines.append("")
    if costs:
        keys = set().union(*(m["credit"].keys() for m in models))
        for k in costs:
            if k not in keys:
                warnings.append(f"Costs: `{k}` matches no Manalens group.")
    if len(models) >= 2:
        lines += side_by_side(models, group, small)
    return lines


def side_by_side(models, group, small):
    totals = [sum(v["conversions"] for v in m["credit"].values()) for m in models]
    keys = set().union(*(m["credit"].keys() for m in models))
    first = models[0]["credit"]
    ordered = sorted(keys, key=lambda k: (-first.get(k, {}).get("conversions", 0), k))
    head = [group]
    for m in models:
        head += [f"{m['label']} credit", f"{m['label']} share"]
    head += ["shift (points)", "read"]
    rows, movers = [], []
    for k in ordered:
        vals = [m["credit"].get(k, {}).get("conversions", 0.0) for m in models]
        shares = [100.0 * v / t if t else 0.0 for v, t in zip(vals, totals)]
        r = [k]
        for v, s in zip(vals, shares):
            r += [fnum(v, 1), f"{s:.1f}%"]
        hi, lo = max(shares), min(shares)
        winner = models[shares.index(hi)]["label"]
        shift = hi - lo
        lo_n, hi_n = min(vals), max(vals)
        if max(vals) <= small:
            read = "too small"
        elif shift >= 10 and hi_n > lo_n + noise(lo_n):
            read = f"model-sensitive: more under {winner}"
            movers.append((k, winner, shift))
        elif shift >= 10:
            read = "share moves, counts within noise"
        else:
            read = "agree"
        r += [f"{shift:.1f}", read]
        rows.append(r)
    lines = ["## Credit share by model", ""]
    lines += table(head, rows)
    lines += ["", "Share is the group's credit over all credit of that model. \"model-sensitive\": the share "
              "moves 10 points or more and the counts differ by more than 2 x the square root of the smaller one. "
              "\"agree\": the share moves less than 10 points, so the answer does not depend on the model. "
              "On the Total rows above, cost columns count only the groups with spend."]
    if movers:
        lines += ["", "Groups whose rank depends on the model:"]
        for k, w, s in sorted(movers, key=lambda x: -x[2]):
            lines.append(f"- `{k}` gets {s:.0f} points more under `{w}`.")
    lines.append("")
    return lines


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Attribution report from Steam UTM exports and/or Manalens get_attribution JSON, "
                    "with optional spend and sales CSVs. Writes Markdown.",
        epilog="Examples:\n"
               "  attribution.py --steam utm.csv --by campaign --costs costs.csv\n"
               "  attribution.py --manalens first_touch.json --manalens last_non_direct.json --costs costs.csv\n"
               "Exit codes: 0 ok, 2 bad input.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--steam", action="append", default=[], metavar="CSV",
                   help="Steam UTM Analytics export (repeat for several files)")
    p.add_argument("--manalens", action="append", default=[], metavar="JSON",
                   help="a get_attribution result saved to a file, one per model (repeat, up to 3)")
    p.add_argument("--costs", metavar="CSV", help="spend per group: a key column (source, campaign, content "
                   "or group) and a spend column (spend, cost, amount)")
    p.add_argument("--sales", metavar="CSV", help="revenue per group for the Steam table: a key column and "
                   "a revenue column (revenue, net_sales)")
    p.add_argument("--by", choices=sorted(DIMENSIONS), default="source",
                   help="how to group Steam rows, costs and sales (default source)")
    p.add_argument("--top", type=int, default=25, help="groups to list before '(other)' (default 25, 0 = all)")
    p.add_argument("--small", type=int, default=16,
                   help="a group with this many conversions or fewer is 'too small' (default 16: 2 x sqrt(16) "
                        "is half of 16)")
    p.add_argument("--title", default="Attribution report", help="report title")
    p.add_argument("--out", metavar="MD", help="write the report here instead of stdout")
    args = p.parse_args(argv)

    if not args.steam and not args.manalens:
        p.print_usage(sys.stderr)
        print("error: give at least one --steam CSV or --manalens JSON", file=sys.stderr)
        return 2
    if len(args.manalens) > 3:
        print("error: at most 3 --manalens files", file=sys.stderr)
        return 2
    warnings = []
    try:
        models = [load_manalens(path) for path in args.manalens]
        cost_by = args.by
        if not args.steam and models:
            g = str(models[0]["meta"].get("group_by", "source"))
            cost_by = g if g in KEY_ALIASES else args.by
        costs = load_keyed(args.costs, cost_by, {"spend": SPEND_ALIASES}, "spend") if args.costs else None
        sales = (load_keyed(args.sales, args.by, {"revenue": REVENUE_ALIASES, "units": UNITS_ALIASES}, "revenue")
                 if args.sales else None)
        if sales and not args.steam:
            warnings.append("--sales is used with --steam only; Manalens results carry their own revenue.")
        out = [f"# {args.title}", ""]
        if args.steam:
            groups, present = load_steam(args.steam, args.by, warnings)
            out += steam_section(groups, present, args.by, costs, sales, args.top, args.small, warnings)
        if models:
            if args.steam and costs and cost_by != str(models[0]["meta"].get("group_by", cost_by)):
                warnings.append("Costs are keyed by the Steam grouping, which differs from the Manalens group_by, "
                                "so Manalens cost columns may be empty.")
            out += manalens_sections(models, costs, args.top, args.small, warnings)
    except InputError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    out += ["## Read with care", ""]
    if args.steam:
        out.append("- Steam UTM is last click: a wishlist or purchase counts for a tagged visit by a signed-in "
                   "player within 72 hours. Phone viewers who later search the game on PC are not counted. "
                   "Read these numbers as a floor and compare groups with each other.")
        out.append("- Steam hides UTM combinations with few visits, and finalizes conversions about 4 days "
                   "after the visit. Export the last week again later.")
    if models:
        out.append("- Manalens credit uses observed website visits and clicks only: no impressions, no view-through. "
                   "A conversion with no touch in the lookback is credited to its own context, often Direct.")
        if len(models) < 2:
            out.append("- One model only. Run a second model (for example `first_touch` next to `last_non_direct`) "
                       "before moving budget.")
    out.append("- Credit is not cause. A group that gets credit may have reached players who would have bought anyway.")
    for w in dict.fromkeys(warnings):
        out.append(f"- Warning: {w}")
    text = "\n".join(out) + "\n"
    if args.out:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as err:
            print(f"error: cannot write {args.out} ({err.strerror})", file=sys.stderr)
            return 2
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
