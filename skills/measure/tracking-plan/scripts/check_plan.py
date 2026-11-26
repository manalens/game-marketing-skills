#!/usr/bin/env python3
"""Check an analytics tracking plan CSV, and optionally the code that sends it.

The plan is analytics/tracking-plan.csv with the columns
event,description,properties,trigger,funnel_step,owner

Checks on the plan:
  - event names are snake_case object_action (such as level_complete), or one of the reserved
    single words purchase, resource, error;
  - no duplicate events (also not by case);
  - property names are snake_case, at most 8 per event (warning), at most 50 (error);
  - no property names that look like personal data (email, name, ip, phone, address ...);
  - funnel_step and owner use the known values;
  - the required funnel steps are present (default: visit, wishlist, install, tutorial, play).

With --code DIR (repeatable), it also greps the code for track calls and reports:
  - planned events that the code never sends (owners game, web and server only; owners sdk and
    external are sent by an SDK or counted by another system);
  - events the code sends that are not in the plan;
  - property keys on a track call line that look like personal data;
  - track calls with a name that is not a string literal (check those by hand).

Python 3 standard library only.
Exit codes: 0 ok (warnings allowed), 1 problems found, 2 bad input (missing file or columns).
"""

import argparse
import csv
import os
import re
import sys

COLUMNS = ["event", "description", "properties", "trigger", "funnel_step", "owner"]
FUNNEL_STEPS = ["visit", "wishlist", "install", "tutorial", "play", "return", "purchase",
                "identity", "health"]
DEFAULT_REQUIRED = ["visit", "wishlist", "install", "tutorial", "play"]
OWNERS = ["game", "web", "server", "sdk", "external"]
CODE_OWNERS = {"game", "web", "server"}
RESERVED_SINGLE = {"purchase", "resource", "error"}

EVENT_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
PROP_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
NUMBERED_RE = re.compile(r"(^|_)\d+(_|$)")

# Tokens that mark a property as personal data. Matched on the parts of a snake_case name.
PII_TOKENS = {"email", "mail", "ip", "ipv4", "ipv6", "phone", "mobile", "password", "passwd",
              "address", "street", "zip", "postcode", "postal", "birthday", "birthdate", "dob",
              "ssn", "surname", "firstname", "lastname", "fullname", "username", "realname",
              "gps", "latitude", "longitude", "lat", "lon", "lng"}
# "name" is personal only with these parts in front (step_name and item_name are fine).
PERSON_PREFIX = {"first", "last", "full", "real", "user", "player", "display", "account", "nick",
                 "given", "family", "middle", "screen", "steam", "discord"}
# Allowed but worth a second look.
PII_WARN = {"steam_id", "steamid", "device_id", "deviceid", "hwid", "mac", "chat", "age",
            "country", "city", "location", "message", "text", "comment"}

CODE_EXT = {".gd", ".cs", ".cpp", ".cc", ".h", ".hpp", ".js", ".mjs", ".cjs", ".ts", ".tsx",
            ".jsx", ".html", ".htm", ".astro", ".vue", ".svelte", ".py", ".lua", ".gml", ".rs",
            ".go", ".java", ".kt", ".swift", ".hx", ".php", ".rb"}
SKIP_DIRS = {".git", ".godot", ".import", "node_modules", "Library", "Temp", "Obj", "obj",
             "Logs", "Intermediate", "Binaries", "DerivedDataCache", "Saved", "build", "dist",
             ".next", ".astro", ".svelte-kit", "vendor", "__pycache__"}
# Analytics SDK sources: their own internal track calls are not the game's events.
SKIP_SDK_PATHS = ["addons/manalens", "Plugins/Manalens", "Packages/dev.manalens.sdk",
                  "node_modules/@manalens"]

# A function declaration such as "func track(event", not a call.
DECL_RE = re.compile(r"\b(func|def|function|void|public|private|static|fn)\b")

DEFAULT_CALLS = r"track|Track|TrackJson|track_event|trackEvent|TrackEvent|logEvent|LogEvent|capture"


class InputError(Exception):
    pass


def split_list(value):
    return [p.strip() for p in re.split(r"[;|]", value or "") if p.strip()]


def prop_name(raw):
    """'level:int' or 'level (number)' -> 'level'."""
    return re.split(r"[:\s(=]", raw.strip(), maxsplit=1)[0]


def pii_level(name):
    """Return 'error', 'warn' or None for a property name."""
    low = name.lower()
    parts = [p for p in re.split(r"[_\-.]", low) if p]
    joined = "".join(parts)
    if any(p in PII_TOKENS for p in parts) or joined in PII_TOKENS:
        return "error"
    if low in {"name", "ip_address", "ipaddr"}:
        return "error"
    for i, p in enumerate(parts):
        if p == "name" and i > 0 and parts[i - 1] in PERSON_PREFIX:
            return "error"
    if low in PII_WARN or any(p in PII_WARN for p in parts):
        return "warn"
    return None


def read_plan(path):
    if not os.path.isfile(path):
        raise InputError(f"{path}: file not found")
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise InputError(f"{path}: empty file")
        header = [h.strip().lower() for h in reader.fieldnames]
        missing = [c for c in COLUMNS if c not in header]
        if missing:
            raise InputError(f"{path}: missing columns {missing}; need {','.join(COLUMNS)}")
        rows = []
        for i, raw in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            if not any(row.values()):
                continue
            row["_line"] = i
            rows.append(row)
    if not rows:
        raise InputError(f"{path}: no events")
    return rows


def check_plan(rows, required):
    errors, warnings = [], []
    seen = {}
    steps = set()
    for row in rows:
        line, ev = row["_line"], row["event"]
        where = f"line {line} ({ev or 'no name'})"
        if not ev:
            errors.append(f"{where}: empty event name")
            continue
        if ev in RESERVED_SINGLE:
            pass
        elif not EVENT_RE.match(ev):
            errors.append(f"{where}: name must be snake_case object_action, such as level_complete")
        if len(ev) > 40:
            warnings.append(f"{where}: name over 40 characters; keep names short")
        if NUMBERED_RE.search(ev):
            warnings.append(f"{where}: number in the name; send one event with a property "
                            f"(level_complete with level: 3, not level_3_complete)")
        key = ev.lower()
        if key in seen:
            errors.append(f"{where}: duplicate of line {seen[key]}")
        else:
            seen[key] = line

        for col in ("description", "trigger"):
            if not row[col]:
                errors.append(f"{where}: empty {col}")

        step = row["funnel_step"].lower()
        if step not in FUNNEL_STEPS:
            errors.append(f"{where}: funnel_step '{row['funnel_step']}' not one of {FUNNEL_STEPS}")
        else:
            steps.add(step)

        owners = [o.lower() for o in split_list(row["owner"])]
        if not owners:
            errors.append(f"{where}: empty owner")
        for o in owners:
            if o not in OWNERS:
                errors.append(f"{where}: owner '{o}' not one of {OWNERS}")
        row["_owners"] = owners

        props = [prop_name(p) for p in split_list(row["properties"])]
        row["_props"] = props
        if len(props) > 50:
            errors.append(f"{where}: {len(props)} properties; the limit is 50")
        elif len(props) > 8:
            warnings.append(f"{where}: {len(props)} properties; keep it to a few")
        if len(set(props)) != len(props):
            errors.append(f"{where}: a property is listed twice")
        for p in props:
            if not PROP_RE.match(p):
                errors.append(f"{where}: property '{p}' is not snake_case")
            level = pii_level(p)
            if level == "error":
                errors.append(f"{where}: property '{p}' looks like personal data; drop it")
            elif level == "warn":
                warnings.append(f"{where}: property '{p}' may be personal or free text; check it")

    for step in required:
        if step not in steps:
            errors.append(f"funnel step '{step}' has no event")
    return errors, warnings


def iter_code_files(root, extra_skip):
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root).replace(os.sep, "/")
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d not in extra_skip]
        if any(rel == s or rel.startswith(s + "/") or ("/" + s + "/") in ("/" + rel + "/")
               for s in SKIP_SDK_PATHS):
            dirnames[:] = []
            continue
        for name in filenames:
            if os.path.splitext(name)[1].lower() in CODE_EXT:
                yield os.path.join(dirpath, name)


def scan_code(roots, calls, extra_skip):
    call_re = re.compile(
        r"(?<![A-Za-z0-9_])(?:" + calls + r")\s*\(\s*(?:TEXT\s*\(\s*)?(?:(?P<q>[\"'`])(?P<name>[^\"'`\n]+)(?P=q)|(?P<dyn>[A-Za-z_][\w.]*))")
    lit_re = re.compile(r"[\"'`]([a-z][a-z0-9_]*)[\"'`]")
    key_res = [re.compile(r"[\"']([A-Za-z_]\w*)[\"']\s*\]?\s*[:=]"),
               re.compile(r"[{,]\s*([A-Za-z_]\w*)\s*:")]
    sent = {}       # name -> list of (file, line, keys)
    literals = {}   # string literal -> first place
    dynamic = []
    files = 0
    for root in roots:
        if not os.path.isdir(root):
            raise InputError(f"{root}: not a folder")
        for path in iter_code_files(root, extra_skip):
            files += 1
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except OSError as e:
                raise InputError(f"{path}: {e}")
            for n, text in enumerate(lines, start=1):
                place = f"{os.path.relpath(path, root)}:{n}"
                for lit in lit_re.findall(text):
                    literals.setdefault(lit, place)
                for m in call_re.finditer(text):
                    if m.group("name"):
                        rest = text[m.end():]
                        keys = set()
                        for kr in key_res:
                            keys.update(kr.findall(rest))
                        sent.setdefault(m.group("name"), []).append((place, keys))
                    elif not DECL_RE.search(text[:m.start()]):
                        dynamic.append(f"{place}: {text.strip()[:100]}")
    return sent, literals, dynamic, files


def check_code(rows, sent, literals, dynamic, owner_filter):
    errors, warnings = [], []
    plan = {r["event"]: r for r in rows if r["event"]}
    checked = 0
    for ev, row in plan.items():
        owners = set(row.get("_owners", []))
        code_owners = owners & CODE_OWNERS
        if owner_filter:
            code_owners &= set(owner_filter)
        if not code_owners:
            continue
        checked += 1
        if ev in sent:
            planned = set(row.get("_props", []))
            for place, keys in sent[ev]:
                for k in sorted(keys):
                    if pii_level(k) == "error":
                        errors.append(f"{place}: {ev} sends '{k}', which looks like personal data")
                    elif planned and k not in planned and PROP_RE.match(k):
                        warnings.append(f"{place}: {ev} sends '{k}', not a planned property")
        elif ev in literals:
            warnings.append(f"{ev}: found as a string at {literals[ev]} but not in a direct track "
                            f"call; check that it is sent (a constant or a wrapper is fine)")
        else:
            errors.append(f"{ev}: planned ({','.join(sorted(code_owners))}) but never sent")
    for ev, places in sorted(sent.items()):
        if ev not in plan:
            errors.append(f"{ev}: sent at {places[0][0]} but not in the plan"
                          + (f" (and {len(places) - 1} more)" if len(places) > 1 else ""))
    for d in dynamic:
        warnings.append(f"name is not a string literal, check by hand: {d}")
    return errors, warnings, checked


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", nargs="?", default="analytics/tracking-plan.csv",
                    help="the plan CSV (default: analytics/tracking-plan.csv)")
    ap.add_argument("--code", action="append", default=[], metavar="DIR",
                    help="a code folder to grep for track calls; repeat for the game and the site")
    ap.add_argument("--owner", action="append", default=[], choices=sorted(CODE_OWNERS),
                    help="only check planned events of this owner against the code; repeatable")
    ap.add_argument("--require", default=",".join(DEFAULT_REQUIRED),
                    help="comma-separated funnel steps that must have an event "
                         f"(default: {','.join(DEFAULT_REQUIRED)}; empty string for none)")
    ap.add_argument("--calls", default=DEFAULT_CALLS,
                    help="regex of function names that send an event (default: %(default)s)")
    ap.add_argument("--skip", action="append", default=[], metavar="DIRNAME",
                    help="another folder name to skip in --code; repeatable")
    args = ap.parse_args()

    required = [s.strip().lower() for s in args.require.split(",") if s.strip()]
    bad = [s for s in required if s not in FUNNEL_STEPS]
    if bad:
        print(f"error: --require has unknown steps {bad}; use {FUNNEL_STEPS}", file=sys.stderr)
        return 2
    try:
        rows = read_plan(args.plan)
        errors, warnings = check_plan(rows, required)
        print(f"plan: {args.plan}, {len(rows)} events")
        if args.code:
            sent, literals, dynamic, files = scan_code(args.code, args.calls, set(args.skip))
            cerr, cwarn, checked = check_code(rows, sent, literals, dynamic, args.owner)
            errors += cerr
            warnings += cwarn
            print(f"code: {files} files in {', '.join(args.code)}; {len(sent)} event names sent; "
                  f"{checked} planned events checked")
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} problem(s), {len(warnings)} warning(s)")
        return 1
    print(f"\nok ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
