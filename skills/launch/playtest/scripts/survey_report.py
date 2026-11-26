#!/usr/bin/env python3
"""Summarise a playtest survey CSV export (Google Forms, Tally or similar) as Markdown.

What it does:
  - Reads the CSV (UTF-8, with or without BOM). One row per tester, one column per question.
  - Skips metadata columns (timestamp, submission or respondent ID, email). A tester ID column is
    counted but never quoted.
  - Detects each question type from the answers: numeric or scale (also "4 - very good"),
    single choice, multi choice (answers joined with ", " or ";"), or free text.
  - Numbers: n, median, mean, min, max and the count of each value. A 0 to 10 "recommend"
    question also gets the share of 9 to 10 and of 0 to 6 answers.
  - Choices: count and share of each option.
  - Free text: keyword frequency (stop words removed), answers grouped under their most
    frequent keyword, up to 3 quotes per group.
  - --segment splits every numeric and choice question by a column (for example "How often do
    you play games like this"), matched by header text.
  - Flags small samples: under 5 answers overall or per segment, and under 30 for rates.
  - Key questions are matched by header text and listed first: recommend, wishlist, overall,
    hardest, confusing, change. Override or add with --role name=pattern.

Examples:
  python3 survey_report.py responses.csv --out playtest/report-data.md
  python3 survey_report.py responses.csv --segment "how often do you play" --min-responses 5
  python3 survey_report.py responses.csv --role change="what would you change" --text "device"

Exit codes: 0 ok; 1 bad input (missing file, no rows, segment column not found);
2 fewer answers than --min-responses.
"""
import argparse
import csv
import re
import statistics
import sys
from collections import Counter, OrderedDict

META = re.compile(r"^(timestamp|submitted at|submission id|respondent id|response id|response type|"
                  r"start date|submit date|network id|e-?mail( address)?|score)$", re.I)
TESTER_ID = re.compile(r"tester.?id|player.?id|^id$", re.I)
EMPTY = {"", "-", "n/a", "na", "null"}

ROLES = OrderedDict([
    ("recommend", r"recommend"),
    ("wishlist", r"wishlist"),
    ("overall", r"overall"),
    ("hardest", r"hardest|most difficult"),
    ("confusing", r"confus|did not know what to do|didn't know what to do|stuck"),
    ("change", r"one thing|change one|would you change"),
])
TEXT_ROLES = {"hardest", "confusing", "change"}

STOP = set("""
a about after again all also am an and any are as at be because been before being but by can could
did do does doing don't dont for from get got had has have having he her here him his how i i'm im
if in into is it it's its just like me more most my no not of on once only or other our out over
really so some such than that the their them then there these they thing things this those to too
very was we were what when where which while who why will with would you your game games play played
playing bit lot much felt feel think one first part time didn't didnt wasn't wasnt
""".split())


def norm(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def read_csv(path):
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
    except OSError as e:
        sys.exit(f"error: cannot read {path}: {e}")
    if len(rows) < 2:
        sys.exit("error: the CSV has no answer rows")
    seen = Counter()
    headers = []
    for h in rows[0]:
        h = norm(h) or "(no header)"
        seen[h] += 1
        headers.append(h if seen[h] == 1 else f"{h} ({seen[h]})")
    data = [r + [""] * (len(headers) - len(r)) for r in rows[1:] if any(c.strip() for c in r)]
    if not data:
        sys.exit("error: the CSV has no answer rows")
    return headers, data


def find_column(headers, pattern, what):
    rx = re.compile(pattern, re.I)
    hits = [h for h in headers if rx.search(h)]
    if not hits:
        sys.exit(f"error: no column header matches {what} '{pattern}'. Headers: " + "; ".join(headers))
    return hits[0]


NUM = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*(?:$|[-:(=/]|\s)")


def as_number(value):
    m = NUM.match(value)
    return float(m.group(1).replace(",", ".")) if m else None


def split_multi(value):
    return [p.strip() for p in re.split(r";|,\s+", value) if p.strip()]


def detect(values, forced=None):
    if forced:
        return forced
    n = len(values)
    if n == 0:
        return "empty"
    if all(as_number(v) is not None for v in values):
        return "numeric"
    distinct = set(values)
    avg = sum(len(v) for v in values) / n
    if any(re.search(r";|,\s", v) for v in values):
        tokens = [t for v in values for t in split_multi(v)]
        tset = set(tokens)
        if len(tset) <= 12 and len(tset) < len(distinct) + 1 and len(tokens) >= 1.5 * len(tset) \
                and max(len(t) for t in tset) <= 60:
            return "multi"
    if avg <= 40 and len(distinct) <= 12 and (len(distinct) <= n / 2 or (n < 6 and avg <= 25)):
        return "single"
    return "text"


def fmt(x):
    return str(int(x)) if float(x).is_integer() else f"{x:.2f}".rstrip("0").rstrip(".")


def pct(k, n):
    return f"{round(100 * k / n)}%" if n else "n/a"


def small(n, rates=True):
    if n < 5:
        return f" **Small sample ({n}): read as anecdotes, not rates.**"
    if n < 30 and rates:
        return f" (n={n}: treat percentages as rough.)"
    return ""


def numeric_block(values, role):
    nums = [as_number(v) for v in values]
    out = [f"- Answers: {len(nums)}. Median **{fmt(statistics.median(nums))}**, mean {fmt(statistics.mean(nums))}, "
           f"min {fmt(min(nums))}, max {fmt(max(nums))}.{small(len(nums), False)}"]
    counts = Counter(nums)
    lo, hi = min(nums), max(nums)
    if lo >= 0 and hi <= 10 and all(float(x).is_integer() for x in counts):
        scale_hi = 10 if hi > 5 else 5
        scale_lo = 0 if lo == 0 or scale_hi == 10 else 1
        out.append("- Counts: " + ", ".join(f"{v}: {counts.get(float(v), 0)}" for v in range(scale_lo, scale_hi + 1)))
    if role == "recommend" and max(nums) <= 10 and max(nums) > 5:
        top = sum(1 for x in nums if x >= 9)
        low = sum(1 for x in nums if x <= 6)
        out.append(f"- 9 to 10: {pct(top, len(nums))}; 0 to 6: {pct(low, len(nums))} "
                   f"(difference {round(100 * (top - low) / len(nums))} points).")
    return out


def choice_counts(values, kind):
    c = Counter()
    for v in values:
        for t in (split_multi(v) if kind == "multi" else [v]):
            c[t] += 1
    return c


def choice_block(values, kind):
    c = choice_counts(values, kind)
    n = len(values)
    note = " Testers could pick more than one, so shares add up to more than 100%." if kind == "multi" else ""
    out = [f"- Answers: {n}.{note}{small(n)}", "", "| Option | Count | Share |", "|---|---|---|"]
    for opt, k in c.most_common():
        out.append(f"| {opt} | {k} | {pct(k, n)} |")
    return out


def words_of(text):
    ws = re.findall(r"[a-z][a-z'\-]+", text.lower())
    out = []
    for w in ws:
        w = w.strip("'-")
        if len(w) < 3 or w in STOP:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def text_block(values, seg_of, quote_max, header=""):
    n = len(values)
    # Words from the question itself ("hardest", "moment") say nothing about the answers.
    asked = set(words_of(header)) | {w.rstrip("est") for w in words_of(header)}
    doc = [set(words_of(v)) - asked for v in values]
    freq = Counter(w for d in doc for w in d)
    out = [f"- Answers: {n}.{small(n, False)}"]
    common = [(w, k) for w, k in freq.most_common(10) if k >= 2]
    if common:
        out.append("- Top keywords (answers that use the word): " + ", ".join(f"{w} ({k})" for w, k in common))
    left = set(range(n))
    groups = []
    for w, k in freq.most_common():
        if k < 2 or len(groups) >= 6:
            break
        members = [i for i in sorted(left) if w in doc[i]]
        if len(members) >= 2:
            groups.append((w, members))
            left -= set(members)
    if groups:
        out.append("")
        for w, members in groups:
            out.append(f"**\"{w}\"** ({len(members)} answers)")
            for i in members[:quote_max]:
                out.append(f"> {quote(values[i])}{seg_of(i)}")
            out.append("")
    if left:
        if not groups:
            out.append("")
        out.append(f"Other answers ({len(left)}):")
        for i in sorted(left)[:quote_max]:
            out.append(f"> {quote(values[i])}{seg_of(i)}")
    return out


def quote(v, limit=180):
    v = norm(v)
    return v if len(v) <= limit else v[:limit].rsplit(" ", 1)[0] + " ..."


def segment_block(values_by_row, kind, seg_values, segs):
    out = ["", f"By segment:", ""]
    if kind == "numeric":
        out += ["| Segment | n | Median | Mean |", "|---|---|---|---|"]
        for s in segs:
            nums = [as_number(v) for r, v in values_by_row if seg_values[r] == s]
            if nums:
                flag = " (small)" if len(nums) < 5 else ""
                out.append(f"| {s}{flag} | {len(nums)} | {fmt(statistics.median(nums))} | {fmt(statistics.mean(nums))} |")
            else:
                out.append(f"| {s} | 0 | | |")
    else:
        allc = choice_counts([v for _, v in values_by_row], kind)
        opts = [o for o, _ in allc.most_common()]
        out += ["| Segment | n | " + " | ".join(opts) + " |", "|---|---|" + "---|" * len(opts)]
        for s in segs:
            vals = [v for r, v in values_by_row if seg_values[r] == s]
            c = choice_counts(vals, kind)
            flag = " (small)" if len(vals) < 5 else ""
            out.append(f"| {s}{flag} | {len(vals)} | " + " | ".join(f"{c.get(o, 0)} ({pct(c.get(o, 0), len(vals))})" for o in opts) + " |")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="survey export, one row per tester")
    p.add_argument("--out", help="write Markdown here (default: print)")
    p.add_argument("--segment", metavar="PATTERN", help="split results by the first column whose header matches (regex, case-insensitive)")
    p.add_argument("--role", action="append", default=[], metavar="NAME=PATTERN", help="match a key question by header text, e.g. change='one thing'")
    p.add_argument("--text", action="append", default=[], metavar="PATTERN", help="force columns whose header matches to free text")
    p.add_argument("--choice", action="append", default=[], metavar="PATTERN", help="force columns whose header matches to single choice")
    p.add_argument("--quotes", type=int, default=3, help="quotes per keyword group (default 3)")
    p.add_argument("--min-responses", type=int, default=0, metavar="N", help="exit 2 if fewer than N testers")
    p.add_argument("--title", default="Playtest survey results", help="report heading")
    args = p.parse_args()

    headers, data = read_csv(args.csv)
    roles = OrderedDict(ROLES)
    for r in args.role:
        if "=" not in r:
            sys.exit(f"error: --role needs NAME=PATTERN, got '{r}'")
        k, v = r.split("=", 1)
        roles[k.strip()] = v.strip()

    seg_col = find_column(headers, args.segment, "--segment") if args.segment else None
    seg_idx = headers.index(seg_col) if seg_col else None
    seg_values = [norm(r[seg_idx]) or "(no answer)" for r in data] if seg_col else []
    segs = [s for s, _ in Counter(seg_values).most_common()] if seg_col else []

    questions = []
    skipped = []
    for i, h in enumerate(headers):
        if META.match(h) or TESTER_ID.search(h):
            skipped.append(h)
            continue
        if i == seg_idx:
            continue
        rows_vals = [(r, norm(row[i])) for r, row in enumerate(data) if norm(row[i]).lower() not in EMPTY]
        role = next((k for k, pat in roles.items() if re.search(pat, h, re.I)), None)
        forced = None
        if any(re.search(t, h, re.I) for t in args.text) or role in TEXT_ROLES:
            forced = "text"
        elif any(re.search(t, h, re.I) for t in args.choice):
            forced = "single"
        kind = detect([v for _, v in rows_vals], forced)
        questions.append({"header": h, "role": role, "kind": kind, "rows": rows_vals})

    n = len(data)
    lines = [f"# {args.title}", "",
             f"- Source: `{args.csv}`. Testers: **{n}**.{small(n)}",
             f"- Questions summarised: {len(questions)}. Skipped metadata columns: {', '.join(skipped) or 'none'}."]
    if seg_col:
        lines.append(f"- Segment column: \"{seg_col}\" ("
                     + ", ".join(f"{s}: {seg_values.count(s)}" for s in segs) + ").")
        tiny = [s for s in segs if seg_values.count(s) < 5]
        if tiny:
            lines.append(f"- **Segments under 5 testers: {', '.join(tiny)}. Do not compare them as rates.**")
    found = [q for q in questions if q["role"]]
    missing = [k for k in roles if k not in {q["role"] for q in questions}]
    if found:
        lines.append("- Key questions found: " + ", ".join(f"{q['role']} (\"{q['header']}\")" for q in found) + ".")
    if missing:
        lines.append("- Key questions not found by header text: " + ", ".join(missing) + ". Use --role to map them.")
    lines.append("- Quotes are copied from testers. Remove names or personal data before sharing this file.")

    order = sorted(questions, key=lambda q: (0 if q["role"] else 1, list(roles).index(q["role"]) if q["role"] else 0))
    for q in order:
        tag = f" [{q['role']}]" if q["role"] else ""
        lines += ["", f"## {q['header']}{tag}", "", f"*Type: {q['kind']}*", ""]
        vals = [v for _, v in q["rows"]]
        if q["kind"] == "empty":
            lines.append("- No answers.")
            continue
        if q["kind"] == "numeric":
            lines += numeric_block(vals, q["role"])
        elif q["kind"] in ("single", "multi"):
            lines += choice_block(vals, q["kind"])
        else:
            rowmap = [r for r, _ in q["rows"]]
            seg_of = (lambda i: f" *({seg_values[rowmap[i]]})*") if seg_col else (lambda i: "")
            lines += text_block(vals, seg_of, args.quotes, q["header"])
        if seg_col and q["kind"] in ("numeric", "single", "multi"):
            lines += segment_block(q["rows"], q["kind"], seg_values, segs)

    md = "\n".join(lines).rstrip() + "\n"
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
        except OSError as e:
            sys.exit(f"error: cannot write {args.out}: {e}")
        print(f"wrote {args.out}: {n} testers, {len(questions)} questions")
    else:
        sys.stdout.write(md)
    if args.min_responses and n < args.min_responses:
        print(f"FAIL: {n} testers, fewer than --min-responses {args.min_responses}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
