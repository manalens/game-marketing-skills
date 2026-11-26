#!/usr/bin/env python3
"""Weekly marketing retro: join posts to platform stats, Steam UTM and web analytics.

Reads marketing/posts.csv (one row per post, see docs/LINKS.md) and joins numbers on
post_id == utm_content (or utm_campaign with --key campaign). Writes a Markdown report: per post,
per clip, by campaign, wishlist lift, per format, keep / drop, links to fix and next week's mix.

Python 3 standard library only. Exit codes: 0 ok, 2 bad input.
"""

import argparse
import csv
import datetime as dt
import io
import math
import os
import re
import statistics
import sys
from urllib.parse import parse_qs, urlparse

POST_ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z]+)-([a-z0-9-]+)$")
TOTAL_RE = re.compile(r"^(grand )?totals?:?$", re.I)
FORMATS = ["caption", "mechanic", "conflict", "update", "series", "trailer", "reddit", "other"]


class InputError(Exception):
    pass


def norm(name):
    """Header name to lowercase letters and digits only (as Manalens matches Steam headers)."""
    return re.sub(r"[^a-z0-9]", "", (name or "").replace("\ufeff", "").strip().lower())


# Steam UTM Analytics columns, matched by normalized name. Same aliases as the Manalens parser.
STEAM_ALIASES = {
    "day": ["date", "day"],
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

STATS_ALIASES = {
    "post_id": ["postid", "id", "utmcontent", "content"],
    "views": ["views", "plays", "impressions"],
    "avd_s": ["avgviewdurations", "avgviewduration", "averageviewduration", "averageviewdurations",
              "avd", "avds", "avgwatchtime", "averagewatchtime", "avgwatchtimes"],
    "avd_pct": ["avgviewpct", "avgviewpercent", "averagepercentageviewed", "averageviewpercentage",
                "avgpercentviewed", "avdpct"],
    "likes": ["likes"],
    "comments": ["comments"],
    "shares": ["shares"],
    "follows": ["follows", "followers", "followersgained", "subscribers", "subscribersgained", "subs"],
    "variant": ["variant", "endcard", "cta"],
}

WEB_ALIASES = {
    "visits": ["visits", "visitors", "sessions", "totalvisits", "pageviews"],
    "signups": ["signups", "signup", "conversions", "wishlistclicks", "wishlistclicked", "goals"],
}

# Steamworks daily wishlist report: a date and the wishlist adds of that day.
WISH_ALIASES = {
    "date": ["date", "datelocal", "day"],
    "adds": ["adds", "wishlistadds", "additions", "wishlistadditions", "wishlists"],
}


def read_rows(path, header_hint=None):
    """Read a CSV with comma, semicolon or tab separators, a BOM and title lines above the header.

    header_hint: normalized names; the header is the first of the first 5 lines that has one.
    Returns (headers, rows as dicts, title text, first data line number).
    """
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            text = fh.read()
    except OSError as err:
        raise InputError(f"{path}: cannot read ({err.strerror})")
    if not text.strip():
        raise InputError(f"{path}: file is empty")
    sample = text[:4096]
    first = next((ln for ln in sample.splitlines() if ln.strip()), "")
    counts = {d: first.count(d) for d in [",", ";", "\t"]}
    lines = [ln for ln in sample.splitlines() if ln.strip()][:6]
    best = max(counts, key=lambda d: max(ln.count(d) for ln in lines))
    records = list(csv.reader(io.StringIO(text), delimiter=best))
    records = [r for r in records if any(c.strip() for c in r)]
    idx = 0
    if header_hint:
        for i, rec in enumerate(records[:5]):
            if any(norm(c) in header_hint for c in rec):
                idx = i
                break
    headers = [c.replace("\ufeff", "").strip() for c in records[idx]]
    title = " ".join(" ".join(r) for r in records[:idx])
    rows = []
    for rec in records[idx + 1:]:
        rows.append({h: (rec[i].strip() if i < len(rec) else "") for i, h in enumerate(headers)})
    return headers, rows, title, idx + 2


def map_columns(headers, aliases):
    mapping, used = {}, set()
    for field, names in aliases.items():
        for h in headers:
            if h not in used and norm(h) in names:
                mapping[field] = h
                used.add(h)
                break
    return mapping


def to_num(value, path, line, col, count=False):
    """Parse a number. count=True: a whole count, so 1.234 and 1,234 both mean thousands."""
    v = (value or "").strip().replace("\u00a0", "").replace(" ", "")
    if v in ("", "-", "n/a", "N/A"):
        return None
    if v.endswith("%"):
        v = v[:-1]
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", v):
        v = v.replace(",", "")
    elif count and re.fullmatch(r"\d{1,3}(\.\d{3})+", v):
        v = v.replace(".", "")
    try:
        return float(v)
    except ValueError:
        raise InputError(f"{path} line {line}: '{value}' in column '{col}' is not a number")


def to_seconds(value, path, line, col):
    v = (value or "").strip()
    m = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{2}(?:\.\d+)?)", v)
    if m:
        h = int(m.group(1) or 0)
        return h * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return to_num(v.rstrip("s"), path, line, col)


def parse_date(value):
    v = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(v, fmt).date()
        except ValueError:
            pass
    return None


def arg_date(value):
    d = parse_date(value) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") else None
    if not d:
        raise argparse.ArgumentTypeError(f"'{value}' is not a date in YYYY-MM-DD form")
    return d



def tag_name(key):
    return "utm_content" if key == "content" else "utm_campaign"


def wins_by(a, b):
    """Poisson rule of thumb: count a beats count b only if a > b + 2 * sqrt(b)."""
    return a > b + 2 * math.sqrt(b)


# ---------------------------------------------------------------- inputs

def load_posts(path, since, until, key):
    headers, rows, _, first = read_rows(path)
    need = ["post_id", "date", "platform", "format"]
    missing = [c for c in need if c not in [h.lower() for h in headers]]
    if missing:
        raise InputError(f"{path}: missing column(s) {', '.join(missing)}. "
                         "Expected: post_id,date,platform,format,title,url,link")
    lower = {h.lower(): h for h in headers}
    posts, seen, warnings = [], set(), []
    for n, row in enumerate(rows, start=first):
        get = lambda c: row.get(lower.get(c, ""), "").strip()
        pid = get("post_id").lower()
        if not pid:
            continue
        if pid in seen:
            raise InputError(f"{path} line {n}: post_id '{pid}' appears twice")
        seen.add(pid)
        day = parse_date(get("date"))
        if not day:
            raise InputError(f"{path} line {n}: date '{get('date')}' is not YYYY-MM-DD")
        fmt = get("format").lower() or "other"
        if fmt not in FORMATS:
            warnings.append(f"`{pid}`: format '{fmt}' is not one of {', '.join(FORMATS)}.")
        m = POST_ID_RE.match(pid)
        if not m:
            warnings.append(f"`{pid}`: post ID does not follow YYYY-MM-DD-<platform>-<slug>.")
        slug = m.group(3) if m else pid
        link = get("link")
        qs = parse_qs(urlparse(link).query) if link else {}
        tag = (qs.get(tag_name(key)) or [None])[0]
        beat = (qs.get("utm_campaign") or [None])[0]
        posts.append({
            "post_id": pid, "date": day, "platform": get("platform").lower(), "format": fmt,
            "title": get("title"), "url": get("url"), "link": link, "tag": tag, "slug": slug,
            "beat": beat.lower() if beat else None, "variant": get("variant"),
        })
    in_range = [p for p in posts if (not since or p["date"] >= since) and (not until or p["date"] <= until)]
    return in_range, len(posts), warnings


def load_stats(paths, warnings):
    stats = {}
    for path in paths:
        headers, rows, _, first = read_rows(path, {"postid"})
        mp = map_columns(headers, STATS_ALIASES)
        if "post_id" not in mp:
            raise InputError(f"{path}: no post_id column")
        if not any(k in mp for k in ("views", "avd_s", "avd_pct")):
            raise InputError(f"{path}: no views, avg_view_duration_s or avg_view_pct column")
        for n, row in enumerate(rows, start=first):
            pid = row.get(mp["post_id"], "").strip().lower()
            if not pid or TOTAL_RE.match(pid):
                continue
            rec = {}
            for f in ("views", "likes", "comments", "shares", "follows", "avd_pct"):
                if f in mp:
                    rec[f] = to_num(row.get(mp[f]), path, n, mp[f], count=f != "avd_pct")
            if "avd_s" in mp:
                rec["avd_s"] = to_seconds(row.get(mp["avd_s"]), path, n, mp["avd_s"])
            if "variant" in mp:
                rec["variant"] = row.get(mp["variant"], "").strip()
            if pid in stats:
                warnings.append(f"`{pid}`: more than one stats row; the last one is used.")
            stats[pid] = rec
    return stats


def zero():
    return {m: 0.0 for m in STEAM_METRICS}


def load_steam(paths, key, warnings):
    """Read Steam UTM Analytics exports.

    Returns a dict:
      post: {tag: metrics} summed by the join column (utm_content or utm_campaign)
      beat: {utm_campaign: metrics}, from campaign-only files when given, else all rows
      tagged: {utm_campaign: metrics} of rows that have a utm_content value
      post_level: True when some file has the join column
      beat_from_campaign_files: True when beat totals come from files with no content column
    """
    hint = {"utmsource", "source", "utmcampaign", "campaign"}
    post, beat_all, beat_camp, tagged = {}, {}, {}, {}
    seen_keys, post_level, camp_files = {}, False, 0
    for path in paths:
        headers, rows, _, first = read_rows(path, hint)
        mp = map_columns(headers, STEAM_ALIASES)
        if "utm_campaign" not in mp:
            raise InputError(f"{path}: no UTM Campaign column (headers: {', '.join(headers)})")
        if not any(m in mp for m in STEAM_METRICS):
            raise InputError(f"{path}: no visits, wishlists or purchases column")
        has_content = "utm_content" in mp
        join_col = mp.get("utm_content") if key == "content" else mp["utm_campaign"]
        if join_col:
            post_level = True
        elif key == "content":
            warnings.append(f"Steam: `{os.path.basename(path)}` has no UTM Content column, so it gives "
                            "campaign totals only (see By campaign), not numbers per post.")
        if not has_content:
            camp_files += 1
        name_day = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", os.path.basename(path))
        file_day = "-".join(name_day.groups()) if name_day else ""
        dims = [d for d in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term") if d in mp]
        for n, row in enumerate(rows, start=first):
            cells = [row.get(mp[d], "") for d in dims] + ([row.get(mp["day"], "")] if "day" in mp else [])
            if any(TOTAL_RE.match(c.strip()) for c in cells if c):
                continue
            camp = row.get(mp["utm_campaign"], "").strip().lower()
            content = row.get(mp["utm_content"], "").strip().lower() if has_content else ""
            if not camp and not content:
                continue
            vals = {m: (to_num(row.get(mp[m]), path, n, mp[m], count=True) or 0) if m in mp else 0
                    for m in STEAM_METRICS}
            day = row.get(mp["day"], "").strip() if "day" in mp else file_day
            dkey = (has_content and key == "content", day, camp, content,
                    row.get(mp["utm_source"], "").strip().lower() if "utm_source" in mp else "")
            if day and dkey in seen_keys and seen_keys[dkey] != path:
                warnings.append(f"Steam: `{content or camp}` day {day} is in both {os.path.basename(seen_keys[dkey])} "
                                f"and {os.path.basename(path)}. It is counted twice; drop the older export.")
            seen_keys.setdefault(dkey, path)

            def add(table, k):
                acc = table.setdefault(k, zero())
                for m in STEAM_METRICS:
                    acc[m] += vals[m]
            if camp:
                add(beat_all, camp)
                if not has_content:
                    add(beat_camp, camp)
                elif content:
                    add(tagged, camp)
            jk = row.get(join_col, "").strip().lower() if join_col else ""
            if jk:
                add(post, jk)
    from_camp = camp_files > 0
    return {"post": post, "beat": beat_camp if from_camp else beat_all, "tagged": tagged,
            "post_level": post_level, "beat_from_campaign_files": from_camp}


def load_web(paths, key):
    aliases = dict(WEB_ALIASES)
    aliases["tag"] = ["utmcontent", "content", "dimension", "postid"] if key == "content" else \
                     ["utmcampaign", "campaign", "dimension", "postid"]
    totals = {}
    for path in paths:
        headers, rows, _, first = read_rows(path, set(aliases["tag"]) | {"utmcampaign", "campaign"})
        mp = map_columns(headers, aliases)
        if "tag" not in mp:
            hint = " (for a file keyed by utm_campaign, use --key campaign)" if key == "content" else ""
            raise InputError(f"{path}: no {tag_name(key)} column{hint}")
        if "visits" not in mp and "signups" not in mp:
            raise InputError(f"{path}: no visits or signups column")
        for n, row in enumerate(rows, start=first):
            k = row.get(mp["tag"], "").strip().lower()
            if not k or TOTAL_RE.match(k):
                continue
            acc = totals.setdefault(k, {"visits": 0.0, "signups": 0.0})
            for f in ("visits", "signups"):
                if f in mp:
                    acc[f] += to_num(row.get(mp[f]), path, n, mp[f], count=True) or 0
    return totals


def load_wishlists(path):
    """Steamworks daily wishlist CSV: {date: adds}, summed when a day has several rows."""
    headers, rows, _, first = read_rows(path, {"date", "datelocal", "day"})
    mp = map_columns(headers, WISH_ALIASES)
    if "date" not in mp or "adds" not in mp:
        raise InputError(f"{path}: needs a date column and a wishlist adds column (headers: {', '.join(headers)})")
    days = {}
    for n, row in enumerate(rows, start=first):
        raw = row.get(mp["date"], "").strip()
        if not raw or TOTAL_RE.match(raw):
            continue
        d = parse_date(raw)
        if not d:
            raise InputError(f"{path} line {n}: date '{raw}' is not a date like 2026-11-20")
        days[d] = days.get(d, 0.0) + (to_num(row.get(mp["adds"]), path, n, mp["adds"], count=True) or 0)
    if not days:
        raise InputError(f"{path}: no daily rows")
    return days


# ---------------------------------------------------------------- report

def fmt_n(v, digits=0):
    if v is None:
        return "-"
    if digits == 0:
        return f"{int(round(v)):,}"
    return f"{v:,.{digits}f}"


def med(values):
    vals = [v for v in values if v is not None]
    return statistics.median(vals) if vals else None


def per_k(wish, views):
    if wish is None or not views:
        return None
    return wish / views * 1000


def compare_wishlists(a_name, a, na, b_name, b, nb):
    """Verdict and sentence for two wishlist counts with the 2 x sqrt rule.

    na and nb are the post counts. When they differ, b is scaled to na posts first.
    Returns (winner or None, sentence).
    """
    bs = b * na / nb if nb else b
    detail = f"{fmt_n(a)} in {na} posts vs {fmt_n(b)} in {nb}" + \
             (f", {fmt_n(bs, 1)} scaled to {na}" if na != nb else "")
    if wins_by(a, bs):
        return a_name, f"`{a_name}` wins on wishlists ({detail})"
    if wins_by(bs, a):
        return b_name, f"`{b_name}` wins on wishlists ({detail})"
    return None, f"not different yet on wishlists ({detail}; a win needs a gap over 2 x sqrt)"


def build(posts, stats, steam, web, wish, args, total_posts, warnings):
    out = []
    tag = tag_name(args.key)
    have_steam, have_web, have_stats = bool(args.steam), bool(args.web), bool(args.stats)
    steam_post = steam["post"] if have_steam else {}
    steam_ok = have_steam and steam["post_level"]
    # Join key: the link's tag (should equal post_id). No tag: try post_id, else no numbers.
    owner = {}
    # A post whose tag is its own ID claims that key first.
    for p in sorted(posts, key=lambda x: ((x["tag"] or "").lower() != x["post_id"], x["date"], x["post_id"])):
        k = (p["tag"] or "").lower() or p["post_id"]
        if not p["tag"] and k not in steam_post and k not in web:
            p["key"] = None
        elif k in owner:
            p["key"] = None
            warnings.append(f"`{p['post_id']}` shares the link `{tag}={k}` with `{owner[k]}`. "
                            f"Its visits and wishlists are shown on `{owner[k]}` only.")
        else:
            p["key"] = k
            owner[k] = p["post_id"]
    for p in posts:
        s = stats.get(p["post_id"], {})
        st = steam_post.get(p["key"]) if p["key"] else None
        wb = web.get(p["key"]) if p["key"] else None
        known = p["key"] is not None
        p["views"] = s.get("views")
        p["avd_s"] = s.get("avd_s")
        p["avd_pct"] = s.get("avd_pct")
        p["follows"] = s.get("follows")
        p["variant"] = s.get("variant") or p["variant"]
        p["steam_visits"] = st["total_visits"] if st else (0.0 if steam_ok and known else None)
        p["wishlists"] = st["wishlists"] if st else (0.0 if steam_ok and known else None)
        p["web_visits"] = wb["visits"] if wb else (0.0 if have_web and known else None)
        p["signups"] = wb["signups"] if wb else (0.0 if have_web and known else None)
        vis = [v for v in (p["steam_visits"], p["web_visits"]) if v is not None]
        p["visits"] = sum(vis) if vis else None

    since = args.since.isoformat() if args.since else (min(p["date"] for p in posts).isoformat() if posts else "-")
    until = args.until.isoformat() if args.until else (max(p["date"] for p in posts).isoformat() if posts else "-")
    out.append(f"# Marketing retro {args.today.isoformat()}")
    out.append("")
    out.append(f"Posts from {since} to {until}: {len(posts)} of {total_posts} in `{args.posts}`.")
    srcs = []
    if have_stats:
        srcs.append("platform stats: " + ", ".join(f"`{os.path.basename(x)}`" for x in args.stats))
    if have_steam:
        srcs.append("Steam UTM: " + ", ".join(f"`{os.path.basename(x)}`" for x in args.steam))
    if have_web:
        srcs.append("web analytics: " + ", ".join(f"`{os.path.basename(x)}`" for x in args.web))
    if wish:
        srcs.append(f"Steam wishlists: `{os.path.basename(args.wishlists)}`")
    out.append("Sources: " + ("; ".join(srcs) if srcs else "none (posts only)") + ".")
    out.append(f"Join: `post_id` equals `{tag}` (the link's tag when it differs). "
               "Visits = Steam total visits + web visits. `-` means no number.")
    if have_steam and not steam["post_level"]:
        out.append(f"No Steam file has a {'UTM Content' if args.key == 'content' else 'UTM Campaign'} column, "
                   "so Steam numbers per post are missing. See By campaign for the totals.")
    out.append("")
    if not posts:
        out.append("No posts in this date range. Check `--since` and `--until`.")
        return "\n".join(out) + "\n"

    # Per post
    out.append("## Per post")
    out.append("")
    sign_h, sign_d = (" Web signups |", "---:|") if have_web else ("", "")
    out.append("| Post | Format | Views | AVD (s) | AVD % | Visits | Wishlists | Wishlists / 1000 views |" + sign_h)
    out.append("|---|---|---:|---:|---:|---:|---:|---:|" + sign_d)
    for p in sorted(posts, key=lambda x: (x["date"], x["post_id"])):
        out.append(f"| `{p['post_id']}` | {p['format']} | {fmt_n(p['views'])} | {fmt_n(p['avd_s'], 1)} | "
                   f"{fmt_n(p['avd_pct'], 1)} | {fmt_n(p['visits'])} | {fmt_n(p['wishlists'])} | "
                   f"{fmt_n(per_k(p['wishlists'], p['views']), 2)} |"
                   + (f" {fmt_n(p['signups'])} |" if have_web else ""))
    out.append("")
    if have_stats:
        no_stats = [p["post_id"] for p in posts if p["post_id"] not in stats]
        if no_stats:
            out.append("No platform stats for: " + ", ".join(f"`{x}`" for x in no_stats) + ".")
            out.append("")

    # Per clip (cross-posts share date and slug)
    clips = {}
    for p in posts:
        clips.setdefault((p["date"], p["slug"]), []).append(p)
    multi = {k: v for k, v in clips.items() if len(v) > 1}
    if multi:
        out.append("## Per clip (cross-posts added up)")
        out.append("")
        out.append("| Clip | Platforms | Views | Visits | Wishlists |")
        out.append("|---|---|---:|---:|---:|")
        for (day, slug), ps in sorted(multi.items()):
            def tot(field):
                vals = [x[field] for x in ps if x[field] is not None]
                return sum(vals) if vals else None
            out.append(f"| {day} {slug} | {', '.join(sorted(x['platform'] for x in ps))} | {fmt_n(tot('views'))} | "
                       f"{fmt_n(tot('visits'))} | {fmt_n(tot('wishlists'))} |")
        out.append("")

    # By campaign (beat)
    if have_steam and args.key == "content" and steam["beat"]:
        beat_posts = {}
        for p in posts:
            if p["beat"]:
                beat_posts[p["beat"]] = beat_posts.get(p["beat"], 0) + 1
        out.append("## By campaign")
        out.append("")
        if steam["beat_from_campaign_files"]:
            out.append("Totals from the Steam export with no UTM Content column. It can count visits whose "
                       "per-post rows Steam hides.")
        else:
            out.append("Totals are the sum of the Steam rows. Rows that Steam hid are missing here too. For a fuller "
                       "total, also pass an export without the UTM Content column.")
        out.append("")
        out.append("| Campaign | Posts in range | Steam visits | Wishlists | Visits not in per-post rows "
                   "| Wishlists not in per-post rows |")
        out.append("|---|---:|---:|---:|---:|---:|")
        for c in sorted(steam["beat"], key=lambda c: -steam["beat"][c]["wishlists"]):
            b = steam["beat"][c]
            rows = steam["tagged"].get(c, zero())
            out.append(f"| {c} | {beat_posts.get(c, 0)} | {fmt_n(b['total_visits'])} | {fmt_n(b['wishlists'])} | "
                       f"{fmt_n(max(b['total_visits'] - rows['total_visits'], 0))} | "
                       f"{fmt_n(max(b['wishlists'] - rows['wishlists'], 0))} |")
        out.append("")

    # Wishlist lift
    if wish:
        out.append("## Wishlist lift")
        out.append("")
        out.append("Daily wishlist adds minus the median of the 7 days before. UTM counts only tagged clicks, "
                   "so lift catches players who searched Steam later.")
        out.append("")
        out.append("| Day | Wishlist adds | Baseline | Lift | UTM wishlists | Posts |")
        out.append("|---|---:|---:|---:|---:|---|")
        by_day = {}
        for p in posts:
            by_day.setdefault(p["date"], []).append(p)
        lift_sum, utm_sum, counted = 0.0, 0.0, 0
        for d in sorted(by_day):
            prior = [wish[d - dt.timedelta(days=i)] for i in range(1, 8) if d - dt.timedelta(days=i) in wish]
            base = statistics.median(prior) if len(prior) >= 4 else None
            adds = wish.get(d)
            lift = adds - base if adds is not None and base is not None else None
            utm = [p["wishlists"] for p in by_day[d] if p["wishlists"] is not None]
            if lift is not None:
                lift_sum += lift
                counted += 1
                utm_sum += sum(utm)
            out.append(f"| {d} | {fmt_n(adds)} | {fmt_n(base, 1)} | {fmt_n(lift, 1)} | "
                       f"{fmt_n(sum(utm) if utm else None)} | "
                       + ", ".join(f"`{p['post_id']}`" for p in sorted(by_day[d], key=lambda x: x["post_id"])) + " |")
        out.append("")
        if counted:
            out.append(f"Lift on {counted} post days: {fmt_n(lift_sum, 1)}. UTM wishlists of the same posts: "
                       f"{fmt_n(utm_sum)}. UTM is a floor; the lift is a rough upper view that also includes "
                       "sales, festivals and press on those days.")
        else:
            out.append("No lift: each post day needs adds and at least 4 of the 7 days before it in the file.")
        out.append("")

    # Per format
    by_fmt = {}
    for p in posts:
        by_fmt.setdefault(p["format"], []).append(p)
    summary = {}
    for f, ps in by_fmt.items():
        def tot(field):
            vals = [x[field] for x in ps if x[field] is not None]
            return sum(vals) if vals else None
        views_sum = tot("views")
        summary[f] = {
            "count": len(ps), "med_views": med(x["views"] for x in ps),
            "med_avd_s": med(x["avd_s"] for x in ps), "med_avd_pct": med(x["avd_pct"] for x in ps),
            "n_avd_s": sum(1 for x in ps if x["avd_s"] is not None),
            "n_avd_pct": sum(1 for x in ps if x["avd_pct"] is not None),
            "visits": tot("visits"), "wishlists": tot("wishlists"),
            "n_wish": sum(1 for x in ps if x["wishlists"] is not None),
            "per_k": per_k(tot("wishlists"), views_sum),
        }
    out.append("## Per format")
    out.append("")
    out.append("| Format | Posts | Median views | Median AVD (s) | Median AVD % | Visits | Wishlists | Wishlists / 1000 views |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for f in sorted(summary, key=lambda k: -summary[k]["count"]):
        s = summary[f]
        out.append(f"| {f} | {s['count']} | {fmt_n(s['med_views'])} | {fmt_n(s['med_avd_s'], 1)} | "
                   f"{fmt_n(s['med_avd_pct'], 1)} | {fmt_n(s['visits'])} | {fmt_n(s['wishlists'])} | "
                   f"{fmt_n(s['per_k'], 2)} |")
    out.append("")

    # Keep / drop
    n_min = args.min_posts
    use_s = any(s["n_avd_s"] for s in summary.values())
    key, n_key, label = ("med_avd_s", "n_avd_s", "median AVD in seconds") if use_s else \
                        ("med_avd_pct", "n_avd_pct", "median AVD %")
    with_avd = {f: s for f, s in summary.items() if s[n_key] > 0}
    eligible = {f: s for f, s in with_avd.items() if s[n_key] >= n_min}
    early = {f: s for f, s in with_avd.items() if s[n_key] < n_min}
    no_avd = [f for f in summary if f not in with_avd]
    out.append("## Keep / drop")
    out.append("")
    out.append(f"Rule: rank video formats by {label}. Keep the top 2 once each has at least {n_min} posts with "
               "that number. On wishlists, a format wins only if its count is over the other's plus "
               "2 x sqrt(the other's count).")
    out.append("")
    ranked = sorted(eligible, key=lambda f: -eligible[f][key])
    keep = ranked[:2] if len(ranked) >= 2 else []
    if keep:
        for f in ranked:
            line = f"- {f}: {'**keep**' if f in keep else 'drop'} ({label} {fmt_n(eligible[f][key], 1)}, " \
                   f"{eligible[f][n_key]} posts)"
            weak = keep[-1]
            sf, sw = summary[f], summary[weak]
            if f not in keep and sf["n_wish"] and sw["n_wish"]:
                winner, text = compare_wishlists(weak, sw["wishlists"], sw["n_wish"], f, sf["wishlists"], sf["n_wish"])
                line += f". Against `{weak}`: {text}"
                if winner == f:
                    line += ". Do not drop it yet"
            out.append(line + ".")
        a, b = keep
        if summary[a]["n_wish"] and summary[b]["n_wish"]:
            _, text = compare_wishlists(a, summary[a]["wishlists"], summary[a]["n_wish"],
                                        b, summary[b]["wishlists"], summary[b]["n_wish"])
            out.append(f"- Between the two kept: {text}.")
    else:
        out.append(f"- Too early: fewer than 2 formats have {n_min} posts with watch-time numbers. Keep the current mix.")
    for f in sorted(early):
        out.append(f"- {f}: too early ({early[f][n_key]} of {n_min} posts).")
    for f in sorted(no_avd):
        out.append(f"- {f}: no watch-time numbers. Judge it by visits and wishlists.")
    out.append("")

    # Variant (CTA end-card) test
    variants = {}
    for p in posts:
        if p.get("variant"):
            variants.setdefault(p["variant"], []).append(p)
    if len(variants) >= 2:
        out.append("## Variant test (for example the end card)")
        out.append("")
        out.append("| Variant | Posts | Median views | Median AVD (s) | Median AVD % | Wishlists |")
        out.append("|---|---:|---:|---:|---:|---:|")
        vw, vn = {}, {}
        for v, ps in sorted(variants.items()):
            wl = [x["wishlists"] for x in ps if x["wishlists"] is not None]
            vw[v], vn[v] = (sum(wl) if wl else None), len(wl)
            out.append(f"| {v} | {len(ps)} | {fmt_n(med(x['views'] for x in ps))} | {fmt_n(med(x['avd_s'] for x in ps), 1)} | "
                       f"{fmt_n(med(x['avd_pct'] for x in ps), 1)} | {fmt_n(vw[v])} |")
        out.append("")
        small = [v for v, ps in variants.items() if len(ps) < n_min]
        if small:
            out.append("Too early to call: " + ", ".join(f"`{v}` has {len(variants[v])}" for v in sorted(small))
                       + f" of {n_min} posts.")
        else:
            top = sorted(variants, key=lambda v: -len(variants[v]))[:2]
            if all(vn[v] for v in top):
                _, text = compare_wishlists(top[0], vw[top[0]], vn[top[0]], top[1], vw[top[1]], vn[top[1]])
                out.append(f"Wishlists: {text}.")
        out.append("")

    # Untagged links
    untagged = [p for p in posts if not p["tag"]]
    wrong = [p for p in posts if p["tag"] and p["tag"].lower() != p["post_id"]]
    no_beat = [p for p in posts if p["link"] and args.key == "content" and p["tag"] and not p["beat"]]
    out.append("## Links to fix")
    out.append("")
    if not untagged and not wrong and not no_beat:
        out.append(f"Every post has a link with `{tag}` set to its post ID.")
    for p in untagged:
        why = "no link" if not p["link"] else f"link has no {tag}"
        out.append(f"- `{p['post_id']}`: {why}. Its visits and wishlists cannot be counted per post.")
    for p in wrong:
        out.append(f"- `{p['post_id']}`: link is tagged `{tag}={p['tag']}`, not the post ID. "
                   "Numbers were joined on that tag; use the post ID next time.")
    for p in no_beat:
        out.append(f"- `{p['post_id']}`: link has no `utm_campaign` (the beat, such as devlog or demo).")
    used = {p["key"] for p in posts if p["key"]} | {p["post_id"] for p in posts} | \
        {(p["tag"] or "").lower() for p in posts}
    for name, data in (("Steam", steam_post), ("Web", web)):
        orphans = sorted(c for c in data if c not in used)
        if orphans and args.since is None and args.until is None:
            out.append(f"- {name} `{tag}` values with no post in `posts.csv`: "
                       + ", ".join(f"`{c}`" for c in orphans[:15]) + (" ..." if len(orphans) > 15 else "") + ".")
    out.append("")

    # Next week's mix
    slots = args.slots
    out.append(f"## Next week ({slots} posts)")
    out.append("")
    if keep:
        a = (slots + 1) // 2
        out.append(f"- {keep[0]}: {a}")
        out.append(f"- {keep[1]}: {slots - a}")
        out.append("- Keep one variant test running (for example end card on odd posts, none on even).")
    else:
        counts = sorted(summary.items(), key=lambda kv: -kv[1]["count"])
        video = [(f, s) for f, s in counts if f not in no_avd] or counts
        # Round robin over this period's formats, most used first (7 slots, 4 formats: 2, 2, 2, 1).
        alloc = {f: 0 for f, _ in video}
        for i in range(slots):
            alloc[video[i % len(video)][0]] += 1
        for f, _ in video:
            if alloc[f]:
                out.append(f"- {f}: {alloc[f]}")
        need = {f: n_min - s[n_key] for f, s in early.items()}
        if need:
            out.append("- Same mix as this period, until each format has "
                       f"{n_min} posts: " + ", ".join(f"{f} needs {n} more" for f, n in sorted(need.items())) + ".")
    out.append("")

    out.append("## Read with care")
    out.append("")
    out.append("- Views are not wishlists. A format can hold viewers and still bring no one to the store page.")
    if have_steam:
        out.append("- Steam counts only visits to the app page with UTM tags, and finalizes wishlists about 4 days "
                   "after the visit. Export the last week again later.")
        if args.key == "content":
            out.append("- Steam hides UTM combinations with few visits. A post can show 0 or no row while its "
                       "campaign total still counts those visits. Read By campaign before you call a post dead.")
        else:
            out.append("- Steam hides UTM combinations with few visits, so a post can show 0 or no row.")
    small = [f for f, s in summary.items() if s["count"] < n_min]
    if small:
        out.append(f"- Small samples: {', '.join(sorted(small))} have fewer than {n_min} posts. One viral post moves a median.")
    for w in warnings:
        out.append(f"- {w}")
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Join marketing/posts.csv with platform stats, Steam UTM Analytics, web analytics and Steam "
                    "daily wishlists (post_id == utm_content by default) and write a Markdown retro.",
        epilog="Example: retro.py --posts marketing/posts.csv --stats stats.csv --steam utm_2026-11-25.csv "
               "--wishlists wishlists.csv --since 2026-11-19 --until 2026-11-25 --out marketing/retro/2026-11-26.md")
    ap.add_argument("--posts", default="marketing/posts.csv", help="tracker CSV (default: marketing/posts.csv)")
    ap.add_argument("--key", choices=["content", "campaign"], default="content",
                    help="UTM tag that holds the post ID: content (utm_content, default) or campaign "
                         "(utm_campaign, the old convention)")
    ap.add_argument("--stats", action="append", default=[], metavar="CSV",
                    help="platform stats: post_id, views, avg_view_duration_s or avg_view_pct, likes, comments, "
                         "shares, follows, optional variant. Repeatable.")
    ap.add_argument("--steam", action="append", default=[], metavar="CSV",
                    help="Steamworks UTM Analytics export. Columns matched by name; Total row skipped; summed by "
                         "the --key column, and by UTM Campaign for the By campaign section. Repeatable.")
    ap.add_argument("--web", action="append", default=[], metavar="CSV",
                    help="web analytics keyed by utm_content (or utm_campaign with --key campaign), with visits "
                         "and/or signups. Repeatable.")
    ap.add_argument("--wishlists", metavar="CSV",
                    help="Steamworks daily wishlist CSV (a date column and a wishlist adds column) for the lift section")
    ap.add_argument("--since", type=arg_date, help="first post date to include (YYYY-MM-DD)")
    ap.add_argument("--until", type=arg_date, help="last post date to include (YYYY-MM-DD)")
    ap.add_argument("--min-posts", type=int, default=5, help="posts per format before keep/drop (default 5)")
    ap.add_argument("--slots", type=int, default=7, help="posts planned for next week (default 7)")
    ap.add_argument("--today", type=arg_date, default=dt.date.today(), help="report date (default: today)")
    ap.add_argument("--out", help="write the report here (default: print it)")
    args = ap.parse_args(argv)
    if args.since and args.until and args.since > args.until:
        print("error: --since is after --until", file=sys.stderr)
        return 2
    if args.min_posts < 1 or args.slots < 1:
        print("error: --min-posts and --slots must be at least 1", file=sys.stderr)
        return 2
    warnings = []
    try:
        posts, total, w = load_posts(args.posts, args.since, args.until, args.key)
        warnings += w
        stats = load_stats(args.stats, warnings)
        steam = load_steam(args.steam, args.key, warnings)
        web = load_web(args.web, args.key)
        wish = load_wishlists(args.wishlists) if args.wishlists else None
    except InputError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    if total == 0:
        print(f"error: {args.posts} has no posts", file=sys.stderr)
        return 2
    report = build(posts, stats, steam, web, wish, args, total, warnings)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
