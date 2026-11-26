#!/usr/bin/env python3
"""Steam regional prices and discount schedules: build, draft and check.

Commands:
  table     From a USD base price, write the regional price table from Valve's recommended
            conversion (bundled CSV). Optional scaling per region or for all regions.
  calendar  Draft a first-year discount schedule CSV from a release date and USD price.
  check     Validate a user-edited regional price CSV (--prices) and/or a discount
            schedule CSV (--discounts with --release). Exit 1 on any error.

Reference data: assets/valve-regional-prices.csv, built from Valve's pricing explorer
("Multi-variable" method, data as of October 2026, read 2026-11-18) via Manalens content.

Regional price CSV (what `table` writes and `check --prices` reads):
  code,name,valve_price,price,diff_pct
  Only `code` and `price` are required. The USD row sets the base price. A filled valve_price
  (for example pasted from Steamworks Propose Pricing) is used as the recommendation for that
  row; an empty one falls back to the bundled table.

Discount schedule CSV (what `calendar` writes and `check --discounts` reads):
  name,type,start,end,percent
  type is one of: launch, custom, weeklong, fest, hub, seasonal, price_increase, price_decrease.
  Dates are YYYY-MM-DD. `end` is the day the discount ends (Steam ends discounts at 10am
  Pacific), so a 7 day discount from Monday 2027-03-01 ends Monday 2027-03-08. Price rows
  need only `start`. Lines starting with # are comments.

Rules checked (Valve, Steamworks Discounting and Pricing docs, read 2026-11-18):
  - Discounts are 10% to 95%. A launch discount is 10% to 40%, runs 7 to 14 days and starts
    at release. Other discounts run 1 to 14 days; a Weeklong Deal is 7 days from a Monday.
  - No discount for 30 days after release, except the launch discount.
  - 30 days between discounts, counted from the end of the last one. Seasonal sales are
    exempt and start no cooldown.
  - No discount of any kind for 30 days after a price increase in any currency.
  - Price changes wait until 30 days after release.
  - Two discounts on the same package cannot run at the same time.

Exit codes: 0 ok (warnings allowed), 1 check failed, 2 bad input.
Stdlib only.
"""
import argparse
import csv
import math
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "assets" / "valve-regional-prices.csv"

# Valve's announced seasonal sales (Steamworks Upcoming Steam Events and Seasonal Sales pages,
# read 2026-11-18 via Manalens steam-events-2027.ts). Autumn 2027 and Winter 2027 are TBD.
KNOWN_SALES = [
    ("Steam Winter Sale 2026", date(2026, 12, 17), date(2027, 1, 4)),
    ("Steam Spring Sale 2027", date(2027, 3, 18), date(2027, 3, 25)),
    ("Steam Summer Sale 2027", date(2027, 6, 24), date(2027, 7, 8)),
]
LAST_KNOWN = date(2027, 7, 8)
COOLDOWN = 30
DISCOUNT_TYPES = {"launch", "custom", "weeklong", "fest", "hub", "seasonal"}
PRICE_TYPES = {"price_increase", "price_decrease"}


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


# ---------- reference table ----------

def load_ref(path=REF):
    try:
        lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    except OSError as e:
        die(f"cannot read reference table {path}: {e}")
    rows = list(csv.reader(lines))
    points = [float(x) for x in rows[0][2:]]
    table = {}
    for r in rows[1:]:
        table[r[0]] = {"name": r[1], "prices": [float(x) for x in r[2:]]}
    return points, table


def point_index(points, usd):
    for i, p in enumerate(points):
        if abs(p - usd) < 0.001:
            return i
    return None


def decimals_of(values):
    d = 0
    for v in values:
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        if "." in s:
            d = max(d, len(s.split(".")[1]))
    return d


def last_digit(v, dec):
    return int(round(v * 10 ** dec)) % 10


def style(values):
    """How a currency's prices end in Valve's table: 'nine', 'eight' or 'round'."""
    dec = decimals_of(values)
    digits = [last_digit(v, dec) for v in values]
    nine = sum(d == 9 for d in digits)
    eight = sum(d == 8 for d in digits)
    if nine * 2 >= len(digits):
        return "nine"
    if eight * 2 >= len(digits):
        return "eight"
    return "round"


def fmt(v, dec):
    if dec == 1 and abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.{dec}f}" if dec else str(int(round(v)))


def snap(value, values):
    """Round a scaled price to the ending style Valve uses for that currency."""
    dec = decimals_of(values)
    st = style(values)
    if dec == 2:
        if st == "nine":
            base = math.floor(value)
            cands = [base - 0.01, base + 0.49, base + 0.99]
            best = min((c for c in cands if c > 0), key=lambda c: abs(c - value))
            return round(best, 2)
        return round(round(value / 0.05) * 0.05, 2)
    if dec == 1:
        return round(value, 1)
    n = len(str(int(round(value))))
    if st in ("nine", "eight"):
        step = 10 ** max(1, n - 2)
        off = 1 if st == "nine" else 2
        return max(step - off, round(value / step) * step - off)
    step = 5 * 10 ** (n - 3) if n >= 3 else 1
    return max(step, round(value / step) * step)


def parse_scales(text):
    out = {}
    for part in filter(None, (p.strip() for p in (text or "").split(","))):
        if "=" not in part:
            die(f"--region-scale item '{part}' must look like CODE=0.9")
        k, v = part.split("=", 1)
        try:
            out[k.strip()] = float(v)
        except ValueError:
            die(f"--region-scale value '{v}' is not a number")
    return out


def cmd_table(a):
    points, table = load_ref(a.ref)
    i = point_index(points, a.usd)
    if i is None:
        near = sorted(points, key=lambda p: abs(p - a.usd))[:3]
        die(f"${a.usd:.2f} is not one of Valve's USD price points. Nearest: "
            + ", ".join(f"{p:.2f}" for p in sorted(near))
            + ". Valve's table only has these points: " + ", ".join(f"{p:.2f}" for p in points))
    scales = parse_scales(a.region_scale)
    unknown = [k for k in scales if k not in table]
    if unknown:
        die("unknown region code(s) in --region-scale: " + ", ".join(unknown))
    out_rows = []
    for code, row in table.items():
        valve = row["prices"][i]
        dec = decimals_of(row["prices"])
        factor = 1.0 if code == "USD" else scales.get(code, a.scale)
        price = valve if abs(factor - 1) < 1e-9 else snap(valve * factor, row["prices"])
        diff = (price - valve) / valve * 100
        out_rows.append([code, row["name"], fmt(valve, dec), fmt(price, dec), f"{diff:.1f}"])
    header = ["code", "name", "valve_price", "price", "diff_pct"]
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(header)
            w.writerows(out_rows)
        print(f"wrote {a.out}: {len(out_rows)} currencies at a USD base of {a.usd:.2f}")
    w = csv.writer(sys.stdout, lineterminator="\n")
    if not a.out or a.print:
        w.writerow(header)
        w.writerows(out_rows)
    print("# Source: Valve pricing explorer, Multi-variable method, data as of October 2026, read 2026-11-18.",
          file=sys.stderr)
    return 0


# ---------- check: regional prices ----------

def read_csv(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as e:
        die(f"cannot read {path}: {e}")
    lines = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    if not lines:
        die(f"{path} is empty")
    rows = list(csv.DictReader(lines))
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in rows]


def check_prices(path, tol, ref):
    points, table = load_ref(ref)
    rows = read_csv(path)
    if not rows or "code" not in rows[0] or "price" not in rows[0]:
        die(f"{path} needs columns 'code' and 'price'")
    errors, warns = [], []
    seen = {}
    for n, r in enumerate(rows, start=2):
        code = r["code"]
        if code in seen:
            errors.append(f"line {n}: {code} appears twice")
        if code not in table:
            errors.append(f"line {n}: unknown currency code '{code}' (not in Valve's table)")
            continue
        if not r["price"]:
            seen[code] = None
            continue
        try:
            seen[code] = float(r["price"])
        except ValueError:
            errors.append(f"line {n}: {code} price '{r['price']}' is not a number")
    valve_given = {}
    for r in rows:
        if r.get("valve_price"):
            try:
                valve_given[r["code"]] = float(r["valve_price"])
            except ValueError:
                errors.append(f"{r['code']}: valve_price '{r['valve_price']}' is not a number")
    missing = [c for c in table if seen.get(c) is None]
    for c in missing:
        errors.append(f"{c} ({table[c]['name']}): no price. A currency with no price makes the game "
                      "unavailable to players who pay in it.")
    usd = seen.get("USD")
    if usd is None:
        errors.append("no USD base price, so the other rows cannot be compared")
        return errors, warns
    i = point_index(points, usd)
    if i is None:
        errors.append(f"USD {usd:.2f} is not one of Valve's price points, so there is no recommendation "
                      "to compare with. Use one of: " + ", ".join(f"{p:.2f}" for p in points))
        return errors, warns
    if last_digit(usd, 2) != 9:
        warns.append(f"USD base {usd:.2f} does not end in 9 like every USD point in Valve's table")
    for code, price in seen.items():
        if price is None or code not in table or code == "USD":
            continue
        row = table[code]
        valve = row["prices"][i]
        given = valve_given.get(code)
        if given is not None:
            valve = given
        dec = decimals_of(row["prices"])
        bad_dec = abs(round(price * 10 ** dec) - price * 10 ** dec) > 1e-6
        if bad_dec:
            errors.append(f"{code}: {price:g} has more decimals than Valve uses for this currency ({dec})")
        floor = row["prices"][0]
        if price < floor - 1e-9:
            errors.append(f"{code}: {fmt(price, dec)} is below Valve's minimum, the conversion of the $0.99 tier ({fmt(floor, dec)})")
        diff = (price - valve) / valve * 100
        if abs(diff) > tol + 1e-9:
            errors.append(f"{code}: {fmt(price, dec)} is {diff:+.1f}% from Valve's {fmt(valve, dec)} "
                          f"(allowed: within {tol:g}%; change --tolerance if you meant it)")
        st, ud = style(row["prices"]), last_digit(price, dec)
        want = {"nine": 9, "eight": 8}.get(st)
        if want is not None and ud != want and not bad_dec:
            warns.append(f"{code}: {fmt(price, dec)} does not end in {want} like Valve's prices in this "
                         f"currency (here {fmt(valve, dec)}); mixed endings read as a typo in that store")
    return errors, warns


# ---------- check: discount schedule ----------

def pdate(text, where):
    try:
        return date.fromisoformat(text)
    except ValueError:
        die(f"{where}: '{text}' is not a YYYY-MM-DD date")


def load_schedule(path):
    rows = read_csv(path)
    need = {"name", "type", "start"}
    if not rows or not need <= set(rows[0]):
        die(f"{path} needs columns name,type,start,end,percent")
    items = []
    for n, r in enumerate(rows, start=2):
        t = r["type"].lower()
        if t not in DISCOUNT_TYPES | PRICE_TYPES:
            die(f"line {n}: type '{r['type']}' must be one of {sorted(DISCOUNT_TYPES | PRICE_TYPES)}")
        it = {"line": n, "name": r.get("name") or t, "type": t, "start": pdate(r["start"], f"line {n} start")}
        if t in DISCOUNT_TYPES:
            if not r.get("end"):
                die(f"line {n}: a discount needs an end date")
            it["end"] = pdate(r["end"], f"line {n} end")
            try:
                it["percent"] = float(r.get("percent", "").rstrip("%"))
            except ValueError:
                die(f"line {n}: percent '{r.get('percent')}' is not a number")
        items.append(it)
    return items


def check_schedule(path, release):
    items = load_schedule(path)
    errors, warns, info = [], [], []
    disc = sorted((i for i in items if i["type"] in DISCOUNT_TYPES), key=lambda i: i["start"])
    incs = sorted(i["start"] for i in items if i["type"] == "price_increase")
    for p in (i for i in items if i["type"] in PRICE_TYPES):
        if p["start"] < release + timedelta(days=COOLDOWN):
            errors.append(f"line {p['line']} {p['name']}: price change on {p['start']} is less than 30 days "
                          f"after release ({release}); Valve asks you to wait 30 days")
    launches = [d for d in disc if d["type"] == "launch"]
    if len(launches) > 1:
        errors.append("more than one launch discount")
    for d in disc:
        tag = f"line {d['line']} {d['name']}"
        days = (d["end"] - d["start"]).days
        pct = d["percent"]
        if days < 1:
            errors.append(f"{tag}: ends on or before its start")
            continue
        if d["type"] == "launch":
            if d["start"] != release:
                errors.append(f"{tag}: a launch discount starts at release ({release}), not {d['start']}")
            if not 10 <= pct <= 40:
                errors.append(f"{tag}: launch discount {pct:g}% must be 10% to 40%")
            if not 7 <= days <= 14:
                errors.append(f"{tag}: launch discount runs {days} days; Valve allows 7 to 14")
        else:
            if not 10 <= pct <= 95:
                errors.append(f"{tag}: {pct:g}% must be 10% to 95%")
            if d["start"] < release + timedelta(days=COOLDOWN):
                errors.append(f"{tag}: starts {d['start']}, inside the 30 day release cooldown "
                              f"(first possible day {release + timedelta(days=COOLDOWN)})")
            if d["type"] == "weeklong":
                if d["start"].weekday() != 0:
                    errors.append(f"{tag}: a Weeklong Deal starts on a Monday, {d['start']} is a {d['start']:%A}")
                if days != 7:
                    errors.append(f"{tag}: a Weeklong Deal runs 7 days, this one {days}")
            elif d["type"] != "seasonal" and days > 14:
                errors.append(f"{tag}: runs {days} days; Valve allows at most 14")
        if d["type"] == "seasonal":
            match = [s for s in KNOWN_SALES if s[1] == d["start"] and s[2] == d["end"]]
            near = [s for s in KNOWN_SALES if abs((s[1] - d["start"]).days) <= 20]
            if not match and near:
                warns.append(f"{tag}: dates differ from {near[0][0]} ({near[0][1]} to {near[0][2]})")
            if not match and not near and d["start"] <= LAST_KNOWN:
                warns.append(f"{tag}: no announced seasonal sale on these dates")
            if d["start"] > LAST_KNOWN:
                info.append(f"{tag}: Valve has not announced dates this far out (last known sale ends {LAST_KNOWN}); check Steamworks")
        for inc in incs:
            if inc <= d["start"] < inc + timedelta(days=COOLDOWN):
                errors.append(f"{tag}: starts {(d['start'] - inc).days} days after the price increase on {inc}; "
                              "no discount for 30 days after an increase, seasonal sales included")
        if pct >= 20 and days >= 1:
            info.append(f"{tag}: {pct:g}% for {days} days sends a wishlist email (20% or more, over 8 hours)")
    # overlaps and the cooldown between discounts
    for a_i, a in enumerate(disc):
        for b in disc[a_i + 1:]:
            if b["start"] < a["end"]:
                errors.append(f"line {a['line']} {a['name']} and line {b['line']} {b['name']} overlap "
                              f"({a['start']} to {a['end']} and {b['start']} to {b['end']})")
    cooling = [d for d in disc if d["type"] != "seasonal"]
    for idx, d in enumerate(cooling):
        if d["type"] == "launch":
            continue
        for prev in cooling[:idx]:
            gap = (d["start"] - prev["end"]).days
            if 0 <= gap < COOLDOWN:
                errors.append(f"line {d['line']} {d['name']}: starts {gap} days after {prev['name']} ends "
                              f"({prev['end']}); custom discounts need 30 days (seasonal sales are the only exception)")
    # wishlist email cooldown and depth ramp: advice only
    emails = [d for d in disc if d["percent"] >= 20]
    for x, y in zip(emails, emails[1:]):
        if (y["start"] - x["start"]).days < 14:
            warns.append(f"{y['name']}: starts {(y['start'] - x['start']).days} days after {x['name']}; "
                         "players emailed in the last 2 weeks are skipped")
    deepest = 0.0
    for d in disc:
        if deepest and d["percent"] - deepest > 15:
            warns.append(f"{d['name']}: jumps from {deepest:g}% to {d['percent']:g}%; raise depth slowly")
        deepest = max(deepest, d["percent"])
    if disc and (disc[-1]["end"] - release).days > 365:
        info.append("schedule runs past the first year")
    first = next((d for d in disc if d["type"] != "launch"), None)
    if first and first["percent"] < 20:
        warns.append(f"{first['name']}: the first discount after launch is {first['percent']:g}%; "
                     "20% or more lets Steam email your wishlisters")
    print("\nSchedule (day 0 = release):")
    for d in sorted(items, key=lambda i: i["start"]):
        off = (d["start"] - release).days
        if d["type"] in DISCOUNT_TYPES:
            print(f"  day {off:>4}  {d['start']} to {d['end']}  {d['percent']:>4g}%  {d['type']:<9} {d['name']}")
        else:
            print(f"  day {off:>4}  {d['start']}                 {d['type']:<9} {d['name']}")
    return errors, warns, info


def cmd_check(a):
    if not a.prices and not a.discounts:
        die("give --prices and/or --discounts")
    errors, warns, info = [], [], []
    if a.prices:
        e, w = check_prices(a.prices, a.tolerance, a.ref)
        errors += [f"prices: {x}" for x in e]
        warns += [f"prices: {x}" for x in w]
    if a.discounts:
        if not a.release:
            die("--discounts needs --release YYYY-MM-DD")
        e, w, i = check_schedule(a.discounts, pdate(a.release, "--release"))
        errors += [f"discounts: {x}" for x in e]
        warns += [f"discounts: {x}" for x in w]
        info += [f"discounts: {x}" for x in i]
    print()
    for x in info:
        print(f"INFO  {x}")
    for x in warns:
        print(f"WARN  {x}")
    for x in errors:
        print(f"FAIL  {x}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors or (a.strict and warns) else 0


# ---------- calendar ----------

def next_monday(d):
    return d + timedelta(days=(7 - d.weekday()) % 7)


def cmd_calendar(a):
    release = pdate(a.release, "--release")
    horizon = release + timedelta(days=365)
    first_ok = release + timedelta(days=COOLDOWN)
    launch_pct = a.launch_percent if a.launch_percent is not None else (10 if a.usd < 10 else 15)
    rows = [("Launch discount", "launch", release, release + timedelta(days=a.launch_days), launch_pct)]
    sales = [s for s in KNOWN_SALES if first_ok <= s[1] <= horizon]
    skipped = [s for s in KNOWN_SALES if release <= s[1] < first_ok]
    events = [(s[0], "seasonal", s[1], s[2]) for s in sales]
    # Custom weeklong discounts between sales: 30 days after the last custom one ends, and 14 days
    # clear of each seasonal sale so the wishlist email goes out for the bigger event (our rule).
    last_end = rows[0][3]
    cursor = next_monday(max(first_ok, last_end + timedelta(days=COOLDOWN)))
    stop = min(horizon, LAST_KNOWN + timedelta(days=1)) if not a.past_known else horizon
    while cursor + timedelta(days=7) <= stop:
        end = cursor + timedelta(days=7)
        clash = [s for s in sales if cursor < s[2] + timedelta(days=14) and end > s[1] - timedelta(days=14)]
        if clash:
            cursor = next_monday(clash[0][2] + timedelta(days=14))
            continue
        events.append(("Weeklong discount", "weeklong", cursor, end))
        cursor = next_monday(end + timedelta(days=COOLDOWN + a.gap_days))
    events.sort(key=lambda e: e[2])
    ramp = [20, 25, 30, 35, 40, 50, 50, 55, 60]
    for n, e in enumerate(events):
        rows.append((e[0], e[1], e[2], e[3], ramp[min(n, len(ramp) - 1)]))
    lines = ["# Draft first-year discount plan. Check with: pricing.py check --discounts <file> --release " + a.release,
             f"# Launch discount {launch_pct}% (Valve suggests about 10 to 15%). Depth ramp 20% upward is a rule of thumb.",
             "# Seasonal dates: Valve, Steamworks Upcoming Steam Events, read 2026-11-18."]
    for s in skipped:
        lines.append(f"# {s[0]} ({s[1]}) starts inside the 30 day release cooldown: the game can be there only at full price.")
    if horizon > LAST_KNOWN:
        lines.append(f"# Valve has not announced sales after {LAST_KNOWN} (Autumn and Winter Sale 2027 are TBD). Add them when listed.")
    out = []
    for r in rows:
        out.append([r[0], r[1], r[2].isoformat(), r[3].isoformat(), f"{r[4]:g}"])
    text = "\n".join(lines) + "\nname,type,start,end,percent\n" + "\n".join(",".join(r) for r in out) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    print(text, end="")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ref", default=str(REF), help="reference CSV (default: the bundled Valve table)")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("table", help="regional price table from a USD base price")
    t.add_argument("--usd", type=float, required=True, help="USD base price, one of Valve's points, e.g. 19.99")
    t.add_argument("--scale", type=float, default=1.0,
                   help="multiply every non-USD price by this, e.g. 0.9 for 10%% below Valve (default 1)")
    t.add_argument("--region-scale", default="", help="per region factors, e.g. 'CNY=0.85,BRL=0.9' (overrides --scale)")
    t.add_argument("--out", help="write CSV here, e.g. launch/regional-prices.csv")
    t.add_argument("--print", action="store_true", help="also print the CSV when --out is given")
    t.set_defaults(func=cmd_table)

    c = sub.add_parser("calendar", help="draft a first-year discount schedule")
    c.add_argument("--release", required=True, help="release date YYYY-MM-DD")
    c.add_argument("--usd", type=float, required=True, help="USD base price")
    c.add_argument("--launch-percent", type=float, help="launch discount (default 10 below $10, else 15)")
    c.add_argument("--launch-days", type=int, default=7, help="launch discount length, 7 to 14 (default 7)")
    c.add_argument("--gap-days", type=int, default=28,
                   help="extra days after the 30 day cooldown between custom discounts (default 28)")
    c.add_argument("--past-known", action="store_true", help="also place custom discounts after the last announced sale")
    c.add_argument("--out", help="write CSV here, e.g. launch/discounts.csv")
    c.set_defaults(func=cmd_calendar)

    k = sub.add_parser("check", help="validate a regional price CSV and/or a discount schedule")
    k.add_argument("--prices", help="regional price CSV with columns code,price")
    k.add_argument("--tolerance", type=float, default=25.0, help="allowed %% from Valve's recommendation (default 25)")
    k.add_argument("--discounts", help="discount schedule CSV")
    k.add_argument("--release", help="release date YYYY-MM-DD (needed with --discounts)")
    k.add_argument("--strict", action="store_true", help="fail on warnings too")
    k.set_defaults(func=cmd_check)

    a = p.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
