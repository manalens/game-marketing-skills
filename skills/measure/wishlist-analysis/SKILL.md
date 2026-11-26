---
name: wishlist-analysis
description: >
  Reads the Steamworks wishlist report export (daily adds, deletes, purchases and activations from
  the wishlist, gifts, and the outstanding total) and answers how fast wishlists are growing, which
  days spiked and what happened then (joined with marketing/posts.csv and an events list such as
  Next Fest, a festival, a creator video or a sale), the baseline without spikes, net adds after
  deletes, wishlist conversion after a launch or a discount, and a cautious outlook to a date. Use
  for "analyse my Steam wishlists", "why did my wishlists spike on Tuesday", "how many wishlists
  will I have at launch", "is my wishlist conversion normal" or "did Next Fest work". Works from
  the CSV; Manalens adds website traffic on spike days. Not for per-post content review
  (`marketing-retro`) or credit by channel (`attribution-report`).
---

# Wishlist analysis

Turn the Steamworks wishlist CSV into a short report: growth per week, spike days and what was
going on, the quiet-day baseline, net adds after deletes, conversion after a launch or sale, and
where the total lands by a date if nothing changes. The agent runs `scripts/wishlists.py` and
writes `marketing/wishlists/YYYY-MM-DD.md`.

The report reads dates and totals. It can say that a spike fell next to a post. It cannot say the
post caused it. Say so every time.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **Steamworks wishlist CSV** (required). Ask the user to open Steamworks, the game's
   **Wishlists** report, set the range to all history, and under "Wishlist Action Summary" click
   "view as csv". The header is usually `DateLocal,Game,Adds,Deletes,PurchasesAndActivations,Gifts`.
   The script also takes `Date`, `Wishlist Adds`, `Deletions`, separate `Purchases` and
   `Activations`, an `Outstanding` or `Balance` column, a title line above the header, and `;` or
   tab separators. A file with several games keeps the one with the most adds unless `--game`.
2. **Outstanding wishlists today** (strongly advised). The number at the top of the Steamworks
   wishlist page. The daily export does not carry a running total, so without it the script
   counts from the first day of the file. With an all-history export that is the same thing.
3. **`marketing/posts.csv`** (optional). Columns from `docs/LINKS.md`; only `date` is needed.
4. **Events list** (optional). Write `marketing/wishlists/events.csv` with the user:
   `date,end_date,name`. One row per festival, Next Fest, creator video, press piece, showcase,
   sale, demo launch, store page change. Ask "what else happened?" for each unexplained spike.
5. **Launch or sale date** (optional), for conversion. **Target date** (optional), for the outlook.

## Workflow

1. **Check the export.** Open the CSV and confirm the header and the date range. Output: one
   line, such as "178 days, 6/1/2026 to 11/25/2026, one game".

2. **Website traffic on spike days through Manalens, if connected.** The Manalens MCP cannot
   return Steam wishlist data: its tools read website and game events (`raw_events`), not
   Steamworks. Steam wishlist sync with a Financial API key and the Steam UTM import exist in the
   dashboard (early access; setup "coming soon"), but not over MCP. So the CSV is always the
   source. Manalens can add context: after step 4, for each spike day, call `get_analytics`
   (scope `analytics:read`):

   ```json
   {"report": "top_sources", "date_from": "2026-10-19", "date_to": "2026-10-21"}
   ```

   and `get_attribution` (scope `attribution:read`) if the site sends a `wishlist_clicked` event:

   ```json
   {"conversion_event": "wishlist_clicked", "group_by": "source",
    "date_from": "2026-10-19", "date_to": "2026-10-21"}
   ```

   A source that jumps on the same days is a lead, not proof. No Manalens? Use the referrers report
   of any web analytics tool, or the Steam UTM Analytics export for the same days.

3. **Build the events list** with the user (Inputs, 4). Use start and end dates for multi-day
   events. Next Fest runs a week; a sale runs its full length.

4. **Run the script.**

   ```bash
   python3 skills/measure/wishlist-analysis/scripts/wishlists.py \
     --wishlists ~/Downloads/wishlists.csv \
     --posts marketing/posts.csv --events marketing/wishlists/events.csv \
     --outstanding 10502 \
     --launch 2026-11-12 --window 7 \
     --target-date 2027-01-31 \
     --out marketing/wishlists/2026-11-26.md
   ```

   Spike rule: at least `--min-adds` adds (10) and either `--factor` (3) times the median of the
   28 days before, or above that median plus `--mads` (3) scaled MADs. `--near` (2) is the days
   around a spike to look for posts and events. A bad file exits with code 2 and names the line.

5. **Answer the user's question** from the report, in plain words, in a short "What this means"
   list at the end of the file:
   - **Growth:** net adds per day this month vs last month, from the weekly table.
   - **Spikes:** each spike, what was near it, and the extra adds above baseline. For "nothing
     logged" rows, ask the user what happened and add it to events.csv.
   - **Did Next Fest (or a festival) work:** the Events table's extra adds. Compare with the
     range in Version notes, not with one famous game.
   - **Conversion:** the rate, next to the cited ranges. See [references/benchmarks.md](references/benchmarks.md).
   - **Outlook:** the three cases, with the caveats. Never write one number as the forecast.

6. **Check.** Run:

   ```bash
   test -s marketing/wishlists/2026-11-26.md && grep -c "^## " marketing/wishlists/2026-11-26.md
   ```

   It prints 7 or more. Tell the user the file path and the one thing to do next.

## Output

`marketing/wishlists/YYYY-MM-DD.md`, Markdown with:

- **Totals:** adds, deletes, net adds, delete rate, purchases and activations, gifts, outstanding.
- **Weekly summary:** per Monday week: adds, deletes, net, purchases, gifts, outstanding at week
  end, net per day. Part weeks are marked.
- **Spike days:** date, weekday, adds, trailing median, the rule that fired, and posts or events
  within 2 days.
- **Events:** adds during each event plus the day after, against a local baseline from the 28
  days before it.
- **Baseline:** median adds and net adds per day over the last 28 non-spike days, and the share of
  adds that came on spike days.
- **Conversion:** outstanding at the start of `--launch`, wishlist purchases and activations in
  `--window` days, the rate, and the cited ranges.
- **Outlook:** outstanding on `--target-date` at the median day, the slowest and the fastest of
  the last 8 weeks (spike days left out).
- **Read with care:** caveats and warnings for this run.

For a second view, the free Manalens [Steam wishlist CSV analyzer](https://manalens.dev/tools/steam-wishlist-csv-analyzer)
reads the same file in the browser and charts net adds with a 7-day average.

## Measure

Run this monthly before launch, and weekly in the last two months. Track three numbers over time:
**baseline net adds per day** (is the floor rising?), **extra adds per event** (which beats are
worth repeating), and **delete rate** (a rising rate after a spike can mean curiosity, not
interest). After launch or a sale, run it again 7 and 30 days later with `--launch`. Per-post
numbers by UTM tag belong in `marketing-retro`.

## Gotchas

- **Outstanding looks too low:** the file does not start at the first wishlist. Pass
  `--outstanding` from the Steamworks page, or export all history.
- **A spike with nothing near it:** a creator video, a news piece, a Steam feature, a bundle or a
  festival the user forgot. Ask. Steam UTM Analytics for the same days may name the source.
- **Day shifts by one:** the CSV's `DateLocal` is Pacific time. The Financial API and Manalens
  use GMT days, and posts.csv uses the poster's day. That is why `--near` defaults to 2.
- **Next Fest tail flagged as spikes:** the days after a festival stay high. Read them as part of
  the event; the Events table counts the day after it.
- **Launch week inflates the baseline:** pass `--launch`, so the launch window is left out of the
  baseline.
- **Outlook after launch:** post-launch adds fall off over weeks. The straight line overstates a
  far target date. Prefer a target within 4 to 8 weeks.
- **Conversion looks low next to "0.15":** that ratio counts all sales per launch wishlist, also
  buyers who never wishlisted. This script counts purchases from the wishlist only.
- **Small games:** under about 500 adds in the file, single days are noise. Read weeks.
- **Gifts and activations:** activations (keys) leave the wishlist too. Both lower outstanding.

## Version notes

- Wishlist value fell: 2023 to 2025 games sold about 0.22 units per wishlist in month one vs 0.45
  for 2020 to 2022 games (claim, 160 games). Total wishlists still predict sales about as well as
  before (R² 0.72); 30-day velocity is no better (0.70). Source: How To Market A Game, 13 Oct
  2026; Inven Global, 15 Oct 2026. So judge growth by total and baseline, not one fast week.
- Popular Upcoming changed in June 2026: it needs far more wishlists (an estimate of about 100k
  for regular entry; a June sample median of 13,270). The Personal Calendar is now the first rung:
  in one person's calendar the default top 100 held games with 8k to 60k wishlists, gaining 300 to
  3,000 a day near launch (claim). Source: How To Market A Game, 25 Jun 2026. Steam needs an exact
  release date 60 days ahead for the calendar page and 3 weeks for the front page
  (partner.steamgames.com, personal calendar docs, checked 2026-11-26).
- Next Fest October 2026 had about 7,240 to 7,319 demos, up about 66% on June. GameDiscoverCo
  estimates a median of about 60 wishlists in 7 days; the top 10% gained about 1,500 (claim).
  Source: How To Market A Game, 21 Oct 2026; GameDiscoverCo, 27 Oct 2026.
- Steam sends wishlist emails at release, at Early Access to 1.0, on discounts of 20% or more
  lasting over 8 hours, and once for a demo; cooldown 1 to 2 weeks per app. Source:
  partner.steamgames.com/doc/marketing/wishlist (checked 2026-11-26). Expect purchase spikes on
  those days, and use `--launch` with the sale start.
- Manalens MCP (checked 2026-11-26): no Steam wishlist tool. Steam data is dashboard only, and
  its setup is "coming soon". Sources and benchmark details: [references/sources.md](references/sources.md).
- Last verified 2026-11-26.
