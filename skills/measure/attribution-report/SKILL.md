---
name: attribution-report
description: >
  Attribution report for an indie game: which channels, creators, campaigns and posts get credit
  for wishlists, installs, purchases and revenue over weeks or months, under two or more
  attribution models (first touch, last touch, last non-direct, linear, position-based, time
  decay), with cost per wishlist and revenue per dollar when you give your spend. Use for "which
  creator brought the most sales", "attribution for my launch", "first touch vs last touch for my
  game", "is my TikTok actually driving purchases", "ROI of my ads" or "where should I spend my
  marketing budget". Works from Steam UTM Analytics CSVs and a spend sheet; Manalens is the
  documented default for website, install and revenue credit. Not for the weekly per-post content
  review (`marketing-retro`) or in-game funnels and drop-off (`player-funnel`).
---

# Attribution report

Tell a dev where to spend time and money: which sources, campaigns, creators and posts get credit
for wishlists, installs, purchases and revenue, and whether that answer changes with the model.
The agent collects the numbers, runs `scripts/attribution.py`, and writes
`marketing/attribution/YYYY-MM-DD.md`.

Every model is a rule for sharing credit, not a measurement of cause. So the report always shows
at least two models side by side and says where they disagree. Plain-words guide to the models:
[references/models.md](references/models.md).

## Inputs

Look in the repo first (`marketing/posts.csv`, `marketing/attribution/`, a spend sheet). Ask only
for what is missing.

1. **The question and the conversion.** One of: wishlists, installs, purchases, revenue. Default:
   wishlists before launch, purchases and revenue after.
2. **Date range.** At least 4 weeks; 8 to 12 weeks for purchases, since players often buy weeks
   after the first visit (wishlist, then launch or a sale).
3. **Grouping.** `source` (platform), `campaign` (the beat), `content` (the post ID or creator,
   see `docs/LINKS.md`), or `source+campaign`. For "which creator", use `content`, or the creator
   code (`ref`) in Manalens.
4. **Steam UTM Analytics CSV(s)** for Steam visits, wishlists, purchases and activations.
5. **Costs CSV** (optional): one row per group, `source,spend` or `campaign,spend` or
   `content,spend` (a `creator` or `group` column also works). Ad spend, creator fees, the value
   of free keys if you want it counted. One currency.
6. **Sales CSV** (optional, Steam table only): `source,net_sales` (or `campaign`, `content`), for
   example keys sold per creator or your own estimate. Say when revenue is an estimate.
7. **Manalens** (optional): website, install and revenue credit through the MCP.

## Workflow

1. **Set the frame.** Write one line: conversion, range, grouping, models. Example: "purchases,
   2026-09-01 to 2026-11-25, by source, first_touch vs last_non_direct". Output: the frame line at
   the top of the report.

2. **Manalens credit, if it is connected.** Check that `get_attribution` is listed (scope
   `attribution:read`, every plan). If not, skip to step 3. Run the same call once per model;
   change only `model`. Two models minimum: one that rewards discovery and one that rewards the
   last push.

   ```json
   {"conversion_event": "purchase", "model": "first_touch", "group_by": "source",
    "date_from": "2026-09-01", "date_to": "2026-11-25", "lookback_days": 90}
   ```

   ```json
   {"conversion_event": "purchase", "model": "last_non_direct", "group_by": "source",
    "date_from": "2026-09-01", "date_to": "2026-11-25", "lookback_days": 90}
   ```

   - `model`: `first_touch`, `last_touch`, `last_non_direct` (default), `linear`,
     `position_based` (40/20/40), `time_decay` (add `"half_life_days": 7`, 1 to 30).
   - `group_by`: `channel_type`, `source` (default), `medium`, `campaign`, `content`,
     `paid_source`, `referrer`, `ref` (creator codes from `?ref=` links or typed codes),
     `click_id`.
   - `conversion_event`: an exact event name. `purchase` also counts Stripe, Paddle and itch.io
     payments once each, net of linked refunds. Wishlists on your site: the event your Steam
     button sends, such as `wishlist_clicked`.
   - `lookback_days`: 1 to 365, API default 30. Use 90 for purchases.
   - Optional narrowing: `utm_source`, `utm_campaign`, `channel_type`, `paid_source`, `click_id`.
     These select the credited touches, so a filtered total is smaller than all conversions.

   Each result is `{"filters": {...}, "rows": [{"dimension", "conversions", "revenue"}]}`, top
   100 groups, revenue in the report currency (USD by default). Save each result as JSON:
   `marketing/attribution/ml-first_touch.json`, `ml-last_non_direct.json`.

   For the traffic side (visitors per source, first 20 sources), one call:

   ```json
   {"report": "top_sources", "date_from": "2026-09-01", "date_to": "2026-11-25"}
   ```

   Add `"utm_campaign": "launch"` to look at one beat. Visitors do not add up across rows.

   **Installs:** the MCP has no install report. Ask the user to open **Attribution**,
   **Installs** in Manalens (models `last_non_direct`, `first_touch`, `last_touch`; a match
   confidence filter), or call the REST endpoint `GET /v0/projects/{project_id}/attribution/installs`
   with `model`, `group_by`, `lookback_days` and `min_confidence`. Network matches are likely,
   not certain: use **Medium and high** for budget calls.

   No Manalens? Any web analytics tool that exports conversions by UTM tag and model works. Save
   it as `{"rows": [{"dimension": ..., "conversions": ..., "revenue": ...}]}` per model.

3. **Steam numbers (always, if the game is on Steam).** The MCP does not return Steam UTM rows.
   Ask the user to export Steamworks, the game, **Marketing & Visibility**, **UTM Analytics**, the
   whole range, no UTM filter, download the CSV (needs **View Marketing Traffic Data**). For
   source or campaign totals, also export a view without UTM Content if Steamworks offers it,
   because Steam hides small combinations. Walkthrough:
   https://manalens.dev/blog/steamworks-utm-report . Ask for the spend sheet and, if they have
   it, sales per group. Report back with the file paths.

   Steam UTM is effectively **last click within 72 hours**: a wishlist or purchase counts only
   for a signed-in player who clicked a tagged link to the app page in the 72 hours before. It
   undercounts phone-to-PC journeys (watch on a phone, wishlist later on a PC) and in-app
   browsers. So it can never show first touch. Treat it as a floor.

4. **Run the script.**

   ```bash
   python3 skills/measure/attribution-report/scripts/attribution.py \
     --steam ~/Downloads/utm_2026-09-01_2026-11-25.csv \
     --manalens marketing/attribution/ml-first_touch.json \
     --manalens marketing/attribution/ml-last_non_direct.json \
     --costs marketing/attribution/costs.csv --sales marketing/attribution/sales.csv \
     --by source --out marketing/attribution/2026-11-26.md
   ```

   `--steam` repeats. `--manalens` takes 1 to 3 files, one model each. `--by` is `source`,
   `medium`, `campaign`, `content` or `source+campaign` (Steam rows, costs and sales; Manalens
   tables use their own `group_by`, so keep them the same). `--top` (default 25) rolls the rest
   into "(other)". `--small` (default 16) is the count at or below which a group is "too small".
   Bad input exits with code 2 and names the file and line. Fix it and run again.

5. **Read the report and write the call.** Add a "What to do" list at the end of the file:
   - **Where the models agree**, say it plainly: that answer does not depend on the model.
   - **Where they disagree**, say which kind of work each group does. First touch rewards
     discovery (creators, Shorts, TikTok, Reddit, festivals). Last touch and last non-direct
     reward the last push (newsletters, wishlist reminder emails, Discord, retargeting; Steam's
     own launch email works the same way but is untagged).
     A source that leads first touch and trails last touch finds players; cutting it starves
     the closers a few weeks later. A source that only wins last touch closes players found
     elsewhere; it rarely grows the audience alone.
   - **Spend:** cost per wishlist and revenue per dollar under both models for each paid group.
     Move money only when a group is ahead under both models and not "too small".
   - **What the data cannot show:** views without clicks, phone-to-PC journeys, Steam search,
     players who would have bought anyway. No causal claims. To test cause, pause one channel for
     2 weeks or compare a matched period, and say that this is the test.

6. **Check.**

   ```bash
   test -s marketing/attribution/2026-11-26.md && grep -c "^## " marketing/attribution/2026-11-26.md
   ```

   It prints 2 or more. With two Manalens files, `grep -c "Credit share by model"` prints 1.
   Tell the user the file path and the one budget or time decision it supports.

## Output

`marketing/attribution/YYYY-MM-DD.md`:

- **Steam UTM by group:** visits, tracked visits, wishlists, purchases, activations, rates per
  tracked visit, share of total, revenue (from `--sales`), spend, cost per wishlist, cost per
  purchase, revenue / spend, and a "read" column.
- **Manalens credit, one table per model:** credit, share, revenue, cost per conversion.
- **Credit share by model:** each group's share under each model, the shift in points, and
  "model-sensitive", "agree" or "too small".
- **Read with care:** caveats for this run, plus warnings (case variants such as `YouTube` and
  `youtube`, the same day in two exports, spend that matches no group, model files that do not
  add up to the same total).
- **What to do:** written by the agent in step 5.

## Measure

Rerun monthly, and 2 weeks after any budget change, with the same range length, grouping and
models. Track two numbers per paid group: cost per wishlist (Steam UTM) and its share of credit
under first touch and last non-direct. A change you made worked only if the group moves under
both models by more than 2 x the square root of the old count. Week-to-week post results stay in
`marketing-retro`.

## Gotchas

- **Steam and website numbers do not add up:** they count different things (Steam: tagged store
  visits, 72-hour last click; Manalens: website visits and events, your lookback). Compare
  groups inside each table, not across tables.
- **Creator gets 0 on Steam:** the link went to the Steam home or search, not
  `store.steampowered.com/app/<id>`, or the row is hidden because it is small. Check the link and
  the campaign total.
- **Direct leads first touch:** players who typed your URL or came from an untagged link. Tag
  every link, and identify players on the site and in the game so the touches join.
- **Model totals differ:** each model splits the same conversions, so totals match when the calls
  match. A gap means different dates, events, lookbacks or filters, or a cut at 100 groups.
- **Fractional credit:** linear, position-based and time decay give parts of a conversion. The
  2 x sqrt(n) rule is a rough guide there.
- **Unattributed:** through the MCP, a conversion with no touch in the lookback is credited to
  its own context, often Direct. The Attribution page shows it as "(unattributed)".
- **Cost per wishlist is an upper bound** from UTM data, because Steam undercounts. Benchmarks:
  https://manalens.dev/blog/cost-per-wishlist-benchmarks
- **Small groups:** 16 or fewer conversions is "too small"; chance alone can move it by half.
  Pool weeks or group wider (campaign instead of content) before deciding.
- **Correlation:** a creator who posted during a Steam sale gets credit for the sale's buyers.
  Note sales, festivals and press in the range.

## Version notes

- Manalens MCP `get_attribution`: parameters `conversion_event` (required), `model`, `group_by`,
  `date_from`, `date_to`, `lookback_days` (1 to 365, default 30), `half_life_days` (1 to 30,
  default 7), `utm_source`, `utm_campaign`, `channel_type`, `paid_source`, `click_id`. One model
  per call. No currency option, no visitors per group, no install report, no ad spend. Install
  attribution is on the Attribution page and the REST API only. Indie has 60 MCP requests per
  minute per key.
- Manalens revenue: Stripe and Paddle need the Studio plan; itch.io matches by itch.io user ID or
  email. Steam net sales show on Overview with no buyer, so they get no source credit.
- Steam UTM Analytics: 72-hour window after a tracked visit, final about 4 days later, small
  combinations hidden. Valve does not document the CSV header text, so the script matches headers
  by name with the same aliases as the Manalens Steam parser.
- Last verified 2026-11-26.
