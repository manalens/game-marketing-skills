#!/usr/bin/env python3
"""Build or check a dated Steam launch plan from a launch date.

The rules (Valve numbers, our lead times, sale and Next Fest dates) come from
references/steam-rules.md, which this script parses. Edit that file when Valve changes a rule.

  plan   writes timeline.md, timeline.csv (date,task,owner,hard_deadline,source) and, with --ics,
         timeline.ics. Exits 1 with --strict when the plan has a problem.
  check  prints problems and notes for the same options and exits 1 on any problem:
         Coming Soon too short, launch before the earliest possible date, a seasonal sale you want
         to discount in inside the 30-day release cooldown, Next Fest ending on or after release,
         Next Fest without a demo, a Next Fest registration that has closed.

Examples:
  timeline.py plan 2027-05-20 --demo --next-fest feb-2027 --out-dir launch --ics
  timeline.py plan asap --today 2026-11-26
  timeline.py check 2026-12-03 --coming-soon 2026-11-30 --join-sale 2026-12-17

Dates are ISO (YYYY-MM-DD). Business days skip weekends, not public holidays.
"""
import argparse
import csv
import datetime as dt
import io
import re
import sys
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "references" / "steam-rules.md"
D = dt.date


# ---------- parsing the rules file ----------

def parse_tables(text):
    """Return {section heading: [row dicts]} for every Markdown table under a '## ' heading."""
    tables, section, header = {}, None, None
    for line in text.splitlines():
        if line.startswith("## "):
            section, header = line[3:].strip(), None
            continue
        if not line.startswith("|") or section is None:
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        tables.setdefault(section, []).append(dict(zip(header, cells)))
    return tables


def load_rules(path):
    tables = parse_tables(Path(path).read_text(encoding="utf-8"))
    for need in ("Rules", "Steam events", "Next Fest editions", "Claims"):
        if need not in tables:
            sys.exit(f"error: section '## {need}' with a table not found in {path}")
    rules = {r["key"]: r for r in tables["Rules"]}
    claims = {r["key"]: r for r in tables["Claims"]}
    events, announced_until = [], None
    for r in tables["Steam events"]:
        if r["name"] == "calendar_announced_until":
            announced_until = iso(r["start"])
            continue
        r = dict(r)
        r["start_d"] = None if r["start"] == "TBD" else iso(r["start"])
        r["end_d"] = None if r["end"] == "TBD" else iso(r["end"])
        events.append(r)
    editions = []
    for r in tables["Next Fest editions"]:
        r = dict(r)
        for k in ("start", "end", "register_by", "press_preview_submit", "all_items_submit", "press_preview"):
            r[k + "_d"] = iso(r[k])
        editions.append(r)
    return rules, claims, events, editions, announced_until


def num(rules, key):
    try:
        return int(rules[key]["value"])
    except KeyError:
        sys.exit(f"error: rule '{key}' missing from {RULES_PATH}")


# ---------- dates ----------

def iso(text):
    try:
        return D.fromisoformat(text)
    except ValueError:
        sys.exit(f"error: '{text}' is not a date in YYYY-MM-DD form")


def add_bd(day, count):
    step = -1 if count < 0 else 1
    left = abs(count)
    while left:
        day += dt.timedelta(days=step)
        if day.weekday() < 5:
            left -= 1
    return day


def friday_or_before(day):
    while day.weekday() > 4:
        day -= dt.timedelta(days=1)
    return day


def days(n):
    return dt.timedelta(days=n)


def fmt(day):
    return day.strftime("%a %d %b %Y")


# ---------- the plan ----------

class Plan:
    def __init__(self):
        self.rows, self.problems, self.notes = [], [], []

    def add(self, date, task, owner, hard, source, phase):
        self.rows.append({"date": date, "task": task, "owner": owner, "hard": hard, "source": source, "phase": phase})


def earliest_launch(args, R, C, today):
    page_live = add_bd(today, num(R, "page_review_business_days"))
    if args.coming_soon and args.coming_soon > page_live:
        page_live = args.coming_soon
    out = page_live + days(num(R, "coming_soon_min_days"))
    if not args.not_first_game:
        out = max(out, today + days(num(R, "app_fee_wait_days")))
        if args.new_account:
            out = max(out, today + days(int(C["claim_new_account_days"]["value"])))
    return out


def find_edition(value, editions):
    for e in editions:
        if value in (e["id"], e["start"]):
            return e
    return None


def build(args, R, C, events, editions, announced_until):
    P = Plan()
    today = args.today
    earliest = earliest_launch(args, R, C, today)
    launch = earliest if args.launch == "asap" else iso(args.launch)
    if args.launch == "asap":
        launch = add_bd(launch, 0) if launch.weekday() < 5 else add_bd(launch, 1)
        P.notes.append(f"ASAP: the earliest launch Valve's rules allow from {fmt(today)} is {fmt(launch)} "
                       f"(page review, then {num(R, 'coming_soon_min_days')} days Coming Soon"
                       + ("" if args.not_first_game else f", and {num(R, 'app_fee_wait_days')} days after the fee if you pay it today")
                       + (f", and the claimed {C['claim_new_account_days']['value']}-day new account queue" if args.new_account and not args.not_first_game else "")
                       + "). Such a short plan gives no time for wishlists; it misses the Personal Calendar page (60 days).")
    src = lambda key: R[key]["source"]
    cs_min = num(R, "coming_soon_min_days")
    cooldown = num(R, "release_cooldown_days")

    if launch <= today:
        P.problems.append("The launch date is today or in the past.")
    elif launch < earliest:
        P.problems.append(f"Launch {fmt(launch)} is before the earliest possible date {fmt(earliest)}: "
                          f"{num(R, 'page_review_business_days')} business days of page review, then {cs_min} days of a public Coming Soon page"
                          + ("" if args.not_first_game else f", and {num(R, 'app_fee_wait_days')} days after paying the app fee") + ".")
    if launch.weekday() > 4:
        P.notes.append("The launch is on a weekend. Valve does not recommend it; the Personal Calendar shows it on the next Monday.")
    if announced_until and launch > announced_until:
        P.notes.append(f"Valve has announced events only up to {fmt(announced_until)}. Sales after that are not in this plan.")

    # Next Fest
    edition = None
    if args.next_fest:
        edition = find_edition(args.next_fest, editions)
        if edition is None:
            nf_start = iso(args.next_fest)
            edition = {"name": f"Next Fest starting {nf_start}", "start_d": nf_start, "end_d": nf_start + days(7),
                       "register_by_d": None, "press_preview_submit_d": nf_start - days(7 * num(R, "next_fest_preview_weeks")),
                       "all_items_submit_d": nf_start - days(7 * num(R, "next_fest_fest_weeks")), "press_preview_d": nf_start - days(11),
                       "source": src("next_fest_fest_weeks")}
            P.notes.append(f"{nf_start} is not a Next Fest edition in the rules table. Deadlines use Valve's generic 5 and 3 weeks; "
                           "registration date unknown, check Steamworks.")
        if edition["end_d"] >= launch:
            P.problems.append(f"{edition['name']} ends {fmt(edition['end_d'])}, on or after launch {fmt(launch)}. "
                              "Valve: the game must not release before the edition ends.")
        if not args.demo:
            P.problems.append("Next Fest needs a public demo when the fest starts. Add --demo or drop --next-fest.")
        if edition.get("register_by_d") and edition["register_by_d"] < today:
            P.problems.append(f"Registration for {edition['name']} closed on {fmt(edition['register_by_d'])}.")
        if args.next_fest_before:
            P.problems.append("You said the game was already in a Next Fest. A game can join only one, ever.")

    # Coming Soon
    if args.coming_soon:
        cs = args.coming_soon
        cs_basis = "your date"
    else:
        cs = friday_or_before(launch - days(7 * num(R, "announce_weeks")))
        if edition and edition.get("register_by_d"):
            cs = min(cs, friday_or_before(edition["register_by_d"] - days(num(R, "page_before_nf_registration_days"))))
        cs = min(cs, launch - days(cs_min))
        cs_basis = "our practice"
        if add_bd(cs, -num(R, "page_review_business_days")) < today:
            cs = add_bd(today if today.weekday() < 5 else add_bd(today, 1), num(R, "page_review_business_days"))
            cs_basis = "as soon as review allows"
    lead = (launch - cs).days
    if lead < cs_min:
        P.problems.append(f"Coming Soon {fmt(cs)} is " + (f"only {lead} days before launch" if lead >= 0 else "after the launch date") + f". Valve needs at least {cs_min} days.")
    if lead < num(R, "calendar_page_days"):
        P.notes.append(f"The exact date is public {max(lead, 0)} days ahead at most, under the {num(R, 'calendar_page_days')} days the Personal Calendar page needs"
                       + (f" and under the {num(R, 'calendar_front_days')} days for the front page." if lead < num(R, "calendar_front_days") else "."))
    if edition and edition.get("register_by_d") and cs > edition["register_by_d"]:
        P.problems.append(f"Coming Soon {fmt(cs)} is after the Next Fest registration deadline {fmt(edition['register_by_d'])}. The base game page must be public to register.")

    # Sales
    sales = [e for e in events if e["kind"] == "Seasonal sale" and e["start_d"]]
    for e in events:
        if e["start_d"] and e["start_d"] <= launch <= e["end_d"]:
            P.notes.append(f"Launch falls inside {e['name']} ({fmt(e['start_d'])} to {fmt(e['end_d'])}). Shoppers look at discounts or demos then; pick an open week.")
    for want in args.join_sale or []:
        sale = next((s for s in sales if want in (s["start"], s["name"])), None)
        if sale is None:
            try:
                start = iso(want)
                sale = {"name": f"sale starting {want}", "start_d": start}
            except SystemExit:
                P.problems.append(f"Unknown sale '{want}'. Use its start date or exact name from the rules table.")
                continue
        last_release = sale["start_d"] - days(cooldown)
        if sale["start_d"] < launch:
            P.problems.append(f"{sale['name']} starts before launch; an unreleased game cannot discount in it.")
        elif launch > last_release:
            P.problems.append(f"{sale['name']} starts {(sale['start_d'] - launch).days} days after launch, inside Valve's {cooldown}-day release cooldown. "
                              f"To discount in it, release on or before {fmt(last_release)}.")

    # --- Setup ---
    if not args.not_first_game:
        fee_by = min(add_bd(cs, -num(R, "page_review_business_days")), launch - days(num(R, "app_fee_wait_days") + num(R, "tax_check_days")))
        fee_by = max(fee_by, today)
        P.add(fee_by, f"Pay the Steam Direct fee ({num(R, 'app_fee_usd')} USD, paid back after 1,000 USD adjusted gross revenue), finish identity and bank checks, send tax info (up to {num(R, 'tax_check_days')} days)", "you", "no", src("app_fee_usd"), "Setup")
        P.add(launch - days(num(R, "app_fee_wait_days")), f"Last day to have paid the app fee ({num(R, 'app_fee_wait_days')}-day wait before release)", "you", "yes", src("app_fee_wait_days"), "Setup")
        if args.new_account:
            c = C["claim_new_account_days"]
            P.notes.append(f"Claim, not a Valve rule: new Steamworks accounts were taking about {c['value']} days to clear onboarding ({c['source']}, {c['date']}).")

    # --- Store page and announce ---
    P.add(add_bd(cs, -num(R, "page_review_business_days")), "Submit the store page for review (Valve: 7 business days before you want it live)", "you", "no", src("page_review_business_days"), "Store page")
    P.add(cs, f"Announce and click Post as Coming Soon ({cs_basis}); announcement trailer, press kit, owned channels", "you", "no", R["announce_weeks"]["source"], "Announce")
    P.add(cs, "Wave 1: announcement to press and creators, one tagged Steam link per outlet", "marketing", "no", R["announce_weeks"]["source"], "Press and creators")
    P.add(cs, "Email your own list: the Steam page is live", "marketing", "no", "https://manalens.dev/tools/game-launch-email-templates?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=launch_timeline", "Wishlist emails")
    P.add(add_bd(launch - days(cs_min), -num(R, "page_review_business_days")), "Latest page submission that can still meet the 2-week Coming Soon rule", "you", "yes", src("page_review_business_days"), "Store page")
    P.add(launch - days(cs_min), "Latest day the Coming Soon page can go public (2 weeks before release)", "you", "yes", src("coming_soon_min_days"), "Store page")
    cal = launch - days(num(R, "calendar_page_days"))
    if cal >= today:
        P.add(cal, "Show the exact release date (day, not month) by this day for the Personal Calendar page", "you", "yes", src("calendar_page_days"), "Store page")
    else:
        # Too late for the 60-day page: a row dated today would read as a task that can still be met.
        P.notes.append(f"Too late for the Personal Calendar page: the exact date had to be public by {fmt(cal)}.")
    P.add(launch - days(num(R, "calendar_front_days")), "Exact date public by this day for the Personal Calendar on the front page", "you", "yes", src("calendar_front_days"), "Store page")
    if (launch - cs).days >= 56:
        P.add(friday_or_before(cs + days((launch - cs).days // 2)), "Second beat: date reveal, new trailer or devlog, with tagged links", "marketing", "no", R["announce_weeks"]["source"], "Announce")
    P.add(launch - days(60), "Email your own list: release date reveal", "marketing", "no", "https://manalens.dev/tools/game-launch-email-templates?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=launch_timeline", "Wishlist emails")

    # --- Demo and Next Fest ---
    demo_live = None
    if args.demo:
        if edition:
            name = edition["name"]
            s = edition["source"]
            if edition.get("register_by_d"):
                P.add(edition["register_by_d"], f"Register for {name} from the base game (11:59 PM Pacific); one Next Fest per game", "you", "yes", s, "Next Fest")
            P.add(edition["press_preview_submit_d"], "Submit the demo build and demo store page for review, to be in the Press Preview", "you", "yes", s, "Next Fest")
            P.add(edition["all_items_submit_d"], "Submit every required Next Fest item for review", "you", "yes", s, "Next Fest")
            P.add(friday_or_before(edition["press_preview_d"] - days(7)), "Wave 2: send the demo to press and creators before the Press Preview", "marketing", "no", R["announce_weeks"]["source"], "Press and creators")
            P.add(edition["press_preview_d"], "Press Preview starts; last day to opt out of trailer use", "Valve", "yes", s, "Next Fest")
            P.add(edition["start_d"], f"{name} starts: demo live before 10 AM Pacific; stream, post, log wishlists daily", "you", "yes", s, "Next Fest")
            P.add(edition["end_d"], f"{name} ends; do not release before this", "Valve", "yes", s, "Next Fest")
            demo_live = min(edition["press_preview_d"], edition["start_d"])
            c = C["claim_demo_live_days"]
            P.notes.append(f"Claim: top demos in Oct 2026 Next Fest had been live about {c['value']} days before the fest ({c['source']}). "
                           "Consider releasing the demo a few weeks before the fest.")
        else:
            demo_live = max(friday_or_before(launch - days(7 * num(R, "demo_weeks"))), cs)
            P.add(add_bd(demo_live, -num(R, "build_backlog_business_days")), "Submit the demo build and demo page for review (planned like a build: 12 business days)", "you", "no", src("build_backlog_business_days"), "Demo")
            P.add(demo_live, "Release the demo; re-publish the base page so the demo button shows", "you", "no", R["demo_weeks"]["source"], "Demo")
            P.add(demo_live, "Wave 2: send the demo to press and creators", "marketing", "no", R["demo_weeks"]["source"], "Press and creators")
        P.add(demo_live + days(num(R, "demo_notify_window_days")), "Last day to send the demo notification to wishlisters (once, within 14 days of the demo's first release)", "you", "yes", src("demo_notify_window_days"), "Wishlist emails")
        if (launch - demo_live).days < num(R, "wishlist_notify_gap_days"):
            P.notes.append("The demo goes live less than 14 days before launch. Valve suggests 14 days between the demo notification and the release email.")

    # --- Press, creators, keys ---
    first_keys = None
    if not args.not_first_game:
        first_keys = add_bd(cs, -num(R, "page_review_business_days")) + days(num(R, "first_keys_wait_days"))
    P.add(friday_or_before(launch - days(7 * num(R, "creator_outreach_weeks"))), "Start creator emails (4 to 6 weeks ahead); one tagged link per creator", "marketing", "no", src("creator_outreach_weeks"), "Press and creators")
    press_keys = friday_or_before(launch - days(7 * num(R, "press_keys_weeks")))
    P.add(max(press_keys, cs), "Wave 3: review keys to press with the embargo date and time", "marketing", "no", src("press_keys_weeks"), "Press and creators")
    P.add(max(friday_or_before(launch - days(7 * num(R, "creator_keys_weeks"))), cs), "Wave 4: keys to creators; ask when they will stream", "marketing", "no", src("creator_keys_weeks"), "Press and creators")
    if first_keys and first_keys > press_keys:
        P.notes.append(f"First-time developers wait 3 weeks after app ID creation for keys. If the app ID is created at page submission, keys arrive about {fmt(first_keys)}, after the press key date.")
    c = C["claim_press_build_weeks"]
    P.notes.append(f"Claim: {c['claim']} ({c['source']}, {c['date']}).")

    # --- Build, date lock, discount ---
    P.add(add_bd(launch, -num(R, "build_backlog_business_days")), "Submit the launch build for review (Valve said up to 12 business days on 3 Nov 2026)", "you", "no", src("build_backlog_business_days"), "Build")
    P.add(add_bd(launch, -num(R, "build_review_business_days")), "Latest build submission at Valve's 7 business days", "you", "yes", src("build_review_business_days"), "Build")
    lock = launch - days(num(R, "date_lock_days"))
    P.add(lock, f"Release date locks. From now a delay of more than {num(R, 'late_delay_hours')} hours drops the game off the Personal Calendar until release", "Valve", "yes", src("date_lock_days"), "Build")
    P.add(lock, f"Set the launch discount if you want one: up to {num(R, 'launch_discount_max_pct')}%, {num(R, 'launch_discount_min_days')} to {num(R, 'launch_discount_max_days')} days, only before release", "you", "yes", src("launch_discount_max_pct"), "Launch")
    P.add(launch - days(30), "Email your own list: one month to go", "marketing", "no", "https://manalens.dev/tools/game-launch-email-templates?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=launch_timeline", "Wishlist emails")
    P.add(launch - days(7), "Email your own list: one week to go", "marketing", "no", "https://manalens.dev/tools/game-launch-email-templates?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=launch_timeline", "Wishlist emails")

    # --- Launch ---
    P.add(launch, "Launch: press Release yourself (approved games do not release themselves); Steam emails every wishlister", "you", "yes", "https://partner.steamgames.com/doc/store/releasing", "Launch")
    P.add(launch, "Launch day checklist: launch trailer and tagged posts, press release, own list email, watch crashes and refunds (see timeline.md)", "you", "no", "https://manalens.dev/tools/game-marketing-timeline?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=launch_timeline", "Launch")
    P.add(launch + days(num(R, "review_request_days")), "Email your own list: ask for an honest review, nothing offered in return", "marketing", "no", src("review_request_days"), "After launch")
    P.add(launch + days(cooldown), "First day you can discount (30-day release cooldown ends)", "Valve", "yes", src("release_cooldown_days"), "After launch")

    # --- Steam events between Coming Soon and 90 days after launch ---
    for e in events:
        if not e["start_d"] or e["start_d"] < max(cs, today) or e["start_d"] > launch + days(90):
            continue
        if e["kind"] == "Seasonal sale" and e["start_d"] > launch:
            ok = e["start_d"] >= launch + days(cooldown)
            P.add(e["start_d"], f"{e['name']} starts: " + ("you can discount in it" if ok else "inside the 30-day cooldown, full price only"), "Valve", "no", e["source"], "Steam events")
        elif e["kind"] == "Seasonal sale":
            P.add(e["start_d"], f"{e['name']} (before launch): keep big announcements out of it", "Valve", "no", e["source"], "Steam events")
        elif e["kind"] == "Next Fest" and not (edition and e["start_d"] == edition["start_d"]):
            P.add(e["start_d"], f"{e['name']} (not joined): avoid launching or announcing during it", "Valve", "no", e["source"], "Steam events")

    P.rows.sort(key=lambda r: (r["date"], r["phase"]))
    for r in P.rows:
        r["overdue"] = r["date"] < today
    if any(r["overdue"] and r["hard"] == "yes" for r in P.rows):
        P.notes.append("Some hard deadlines are already past (marked OVERDUE). Re-plan with a later date or 'asap'.")
    return launch, cs, P


# ---------- writers ----------

def to_csv(P):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["date", "task", "owner", "hard_deadline", "source"])
    for r in P.rows:
        w.writerow([r["date"].isoformat(), r["task"], r["owner"], r["hard"], r["source"]])
    return buf.getvalue()


def to_md(launch, cs, P, args, today):
    out = [f"# Launch timeline to {fmt(launch)}", "",
           f"- Generated {today.isoformat()} by launch-timeline/scripts/timeline.py from references/steam-rules.md",
           f"- Coming Soon: {fmt(cs)} ({(launch - cs).days} days before launch)",
           f"- Demo: {'yes' if args.demo else 'no'}. Next Fest: {args.next_fest or 'none'}. First game on the account: {'no' if args.not_first_game else 'yes'}",
           "- Hard deadline = a Valve rule or Valve date. Everything else is our practice; move it if you need to.", ""]
    if P.problems:
        out += ["## Problems (fix before you commit to this date)", ""] + [f"- {p}" for p in P.problems] + [""]
    if P.notes:
        out += ["## Notes", ""] + [f"- {n}" for n in P.notes] + [""]
    out += ["## Plan", "", "| Date | Days to launch | Task | Owner | Hard | Phase |", "|---|---|---|---|---|---|"]
    for r in P.rows:
        flag = " OVERDUE" if r["overdue"] else ""
        out.append(f"| {r['date'].isoformat()}{flag} | {(r['date'] - launch).days} | {r['task']} | {r['owner']} | {r['hard']} | {r['phase']} |")
    out += ["", "## Launch day checklist", "",
            "- [ ] Build approved, launch discount (if any) saved before release",
            "- [ ] Press Release App in Steamworks at the planned hour; check the page shows the price",
            "- [ ] Launch trailer and posts up, each link tagged (utm_campaign=launch)",
            "- [ ] Press release sent under a personal email; embargo lifts at the same time for everyone",
            "- [ ] Email your own list; post a Steam event",
            "- [ ] Creators with keys reminded of the date",
            "- [ ] Watch crashes, refunds and reviews every few hours; reply to reviews",
            "- [ ] First 10 reviews: Steam shows a score from 10 reviews by buyers, and key activations do not count. "
            "One studio (Bite Me Games) advises lining up about 10 people who will buy at launch and leave an honest review. "
            "Treat it as one studio's advice. Never pay for, reward or require a review: Valve forbids incentives.",
            "", "Sources for every row are in timeline.csv.", ""]
    return "\n".join(out)


def to_ics(P, launch):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//game-marketing-skills//launch-timeline//EN", "CALSCALE:GREGORIAN"]
    for i, r in enumerate(P.rows):
        summary = (("[HARD] " if r["hard"] == "yes" else "") + r["task"]).replace(",", "\\,").replace(";", "\\;")
        lines += ["BEGIN:VEVENT", f"UID:launch-{launch.isoformat()}-{i}@game-marketing-skills", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{r['date'].strftime('%Y%m%d')}",
                  f"DTEND;VALUE=DATE:{(r['date'] + days(1)).strftime('%Y%m%d')}",
                  f"SUMMARY:{summary[:200]}", f"DESCRIPTION:{r['source']}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["plan", "check"], help="plan writes files; check only reports")
    p.add_argument("launch", help="launch date YYYY-MM-DD, or 'asap'")
    p.add_argument("--today", help="today's date (default: system date)")
    p.add_argument("--demo", action="store_true", help="the game will have a demo")
    p.add_argument("--next-fest", help="edition id (feb-2027, june-2027) or its start date")
    p.add_argument("--next-fest-before", action="store_true", help="the game was already in a Next Fest")
    p.add_argument("--coming-soon", help="date the Coming Soon page goes (or went) public")
    p.add_argument("--join-sale", action="append", help="seasonal sale you want to discount in (start date or name); repeatable")
    p.add_argument("--not-first-game", action="store_true", help="the account already released a game: no fee wait")
    p.add_argument("--new-account", action="store_true", help="add the claimed new-account onboarding queue to 'asap'")
    p.add_argument("--out-dir", default="launch", help="folder for timeline.md/.csv/.ics (default: launch)")
    p.add_argument("--ics", action="store_true", help="also write timeline.ics")
    p.add_argument("--strict", action="store_true", help="plan: exit 1 when the plan has problems")
    p.add_argument("--rules", default=str(RULES_PATH), help="path to steam-rules.md")
    args = p.parse_args()

    args.today = iso(args.today) if args.today else D.today()
    args.coming_soon = iso(args.coming_soon) if args.coming_soon else None
    if args.launch != "asap":
        iso(args.launch)
    R, C, events, editions, until = load_rules(args.rules)
    launch, cs, P = build(args, R, C, events, editions, until)

    if args.mode == "check":
        print(f"Launch {fmt(launch)}, Coming Soon {fmt(cs)}")
        for x in P.problems:
            print(f"PROBLEM: {x}")
        for x in P.notes:
            print(f"note: {x}")
        if P.problems:
            print(f"\n{len(P.problems)} problem(s): this plan does not work as given.")
            sys.exit(1)
        print("\nok: no rule broken")
        return

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "timeline.csv").write_text(to_csv(P), encoding="utf-8")
    (out / "timeline.md").write_text(to_md(launch, cs, P, args, args.today), encoding="utf-8")
    written = ["timeline.md", "timeline.csv"]
    if args.ics:
        (out / "timeline.ics").write_text(to_ics(P, launch), encoding="utf-8", newline="")
        written.append("timeline.ics")
    print(f"wrote {', '.join(str(out / w) for w in written)}: {len(P.rows)} tasks, {len(P.problems)} problem(s), {len(P.notes)} note(s)")
    for x in P.problems:
        print(f"PROBLEM: {x}")
    if args.strict and P.problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
