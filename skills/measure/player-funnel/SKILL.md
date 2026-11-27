---
name: player-funnel
description: >
  Analyse the player journey of an indie game from store or site visit to retained player: a
  step funnel (visit, demo download or first open, tutorial complete, first session over N
  minutes, level 3, purchase) with drop-off and time between steps, day 1, 7 and 30 retention by
  install cohort and by acquisition source, playtime distribution, and the last event before
  players quit. Turns the numbers into a short list of next steps, such as the tutorial step to
  fix or the Short whose players churn fastest. Use for "where do players drop off in my demo",
  "day 1 retention for my game", "do TikTok players stick around", "build a funnel for my Steam
  demo" or "make an analytics dashboard for my game". Works from any raw event CSV; Manalens is
  the documented default. Not for choosing which events to send (`tracking-plan`) or giving
  channels credit for sales and wishlists (`attribution-report`).
---

# Player funnel

Find where players leave and which players stay. The agent reads raw events (Manalens through
MCP, or a CSV export from any tool), builds the funnel, retention, playtime and quit-point
tables, and writes `marketing/player-funnel/YYYY-MM-DD.md` ending with up to three changes to
make, each with the number to check afterwards.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **The steps.** Read the game's event names from the code (`track(`, `Manalens.track`,
   `analytics.track`, a tracking plan file) or from `describe_schema` / `top_events`. Propose a
   funnel of 3 to 7 steps and confirm it with the user. Typical demo funnel:
   `store_visit` or a page, `game_open`, `tutorial_complete`, a first session of 10 minutes or
   more (`session_end` with `duration_s >= 600`), `level_complete` level 3, `purchase` or
   `wishlist_clicked`. If an event the user wants does not exist, say so and point to
   `tracking-plan`. Do not invent it.
2. **Date range.** Default: the last 30 days for the funnel. Retention to day 30 needs 60 to 90
   days and ends yesterday.
3. **The question.** Drop-off, retention by source, playtime, quit points, or a dashboard. Tie
   it to a decision the user must make, such as "rebalance level 4 or not", and pin it to one
   event, one date range and one split (by build or by source). "Is my game fun?" has no event
   behind it (our practice).
4. **Data.** Manalens MCP if connected (check that `get_analytics` is listed). Otherwise a CSV
   from any analytics tool's raw event export with these columns:
   `user_id` or `anonymous_id`, `event`, `timestamp`, optional `properties` (JSON) and `source`.
   Header names are matched loosely (`distinct_id`, `event_name`, `user_pseudo_id`,
   `event_timestamp` all work). Ask the user to export it and report back with the path.

## Workflow

1. **Pick the data path.** Output: one line, such as "Manalens Studio (SQL)", "Manalens Indie
   (no SQL)" or "CSV: ~/Downloads/events.csv". If `execute_query` is listed, call it once with
   `SELECT count() AS n FROM raw_events WHERE original_timestamp >= now() - INTERVAL 1 DAY`.
   A `402` `PLAN_UPGRADE_REQUIRED`, or no `execute_query` tool (Indie keys cannot have the
   `query:read` scope), means step 3. On Studio, a key without `query:read` needs a new key.

2. **Manalens with SQL (Studio).** Run the templates in
   [references/queries.md](references/queries.md) with `execute_query`
   (`{"sql": "...", "date_from": "2026-09-01", "date_to": "2026-11-25"}`):
   - section 2: step funnel with step and overall conversion;
   - section 3: median time between two steps that matter;
   - section 4: retention by install week (day 1, 7, 30);
   - section 5: retention by `utm_source` of the first session;
   - section 6: playtime buckets and quantiles;
   - section 7: last event before churn.
   Replace the event names with the user's. Results stop at 200 rows. Save each result as a
   CSV next to the report (`marketing/player-funnel/sql-<name>-YYYY-MM-DD.csv`), so the numbers
   can be checked later.

3. **Manalens without SQL (Indie).** `execute_query` is not on Indie. Use what is:
   - Reach of each step, total and per source. `get_analytics` `top_events` returns `event`,
     `occurrences` and `visitors` for the first 20 events:
     `{"report": "top_events", "date_from": "2026-11-01", "date_to": "2026-11-25", "utm_source": "tiktok"}`.
     For one event with a property, use `filters`:
     `{"report": "event_timeseries", "date_from": "...", "date_to": "...", "filters": [{"field": "event", "op": "eq", "value": "level_complete"}, {"field": "properties.level", "op": "eq", "value": "3"}]}`
     and read `totals.visitors`. These counts are not ordered and not joined across website and
     game, so ratios between them are a rough upper view of the funnel, not conversion.
   - The real funnel and retention come from the dashboard's own **Funnel** and **Retention**
     charts, which work on every plan and join linked IDs. Ask the user to add them (or offer to,
     step 7), then read the numbers from the chart or its **Export** CSV and report back.
     Retention: entry `game_open`, return `session_start`, daily periods, breakdown
     **UTM Source**. Funnel: Sequential, breakdown **UTM Source** with **First Touch**.
   - Quit points: a **User paths** chart backward from `level_fail`, or the **Did not return**
     list of a retention cell, exported as CSV.

4. **CSV path (any tool).** Run the script:

   ```bash
   python3 skills/measure/player-funnel/scripts/funnel.py --events ~/Downloads/events.csv \
     --steps "store_visit,game_open,tutorial_complete,session_end[duration_s>=600],level_complete[level=3],purchase" \
     --window 168 --retention --entry-event game_open --return-event session_start \
     --playtime --quits --quits-after game_open --by source \
     --out marketing/player-funnel/2026-11-26.md
   ```

   Steps take alternatives (`game_open|demo_open`) and property filters (`[level=3]`,
   `[duration_s>=600]`). `--window` is hours from the first step. `--by` splits by a column or
   `properties.<key>` (first value per player). `--rolling` counts day N or later.
   `--min-players` (default 30) flags small groups. A bad file exits with code 2 and names the
   line. Fix it and run again. For tutorial detail, run a second funnel of the tutorial steps
   alone, such as `game_open,tutorial_step[step=1],...,tutorial_complete`.

5. **Read the numbers.** For each table, write one plain sentence of what it shows:
   - **Funnel:** the step with the biggest drop in share, and in players. A drop at the store
     or download step is the store page, not the game.
   - **Retention:** D1, D7, D30 for all players, then per source. Compare to the user's own
     earlier weeks first. Public PC medians (GameAnalytics, desktop builds, October 2026) are
     about 6.5% D1, 1.4% D7, 0.2% D30, for free-to-play-heavy samples; a premium or demo build
     differs. More: https://manalens.dev/blog/pc-indie-game-retention-benchmarks?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=player_funnel
   - **Playtime:** the share under 5 minutes, the median, and for a paid game on Steam the share
     over 2 hours (the refund line).
   - **Quits:** the top 3 last events with their level or step.
   Every group or cohort under 30 players: say "too small" and do not rank it.
   Before you write, check the numbers (OpenAI and Anthropic advice for AI data work; the order
   is our practice):
   - **Row count first:** the events and players the script or SQL read match the export. A
     partial read, or rows dropped for empty IDs, gives confident numbers about the wrong players.
   - **One number by hand:** recompute one or two headline numbers, such as players at step 1,
     and compare them with the analytics tool's own report for the same dates.
   - **Keep the method:** the SQL files or the script command stay next to the report, so anyone
     can rerun them.
   - **Say what the data cannot answer.** Write "the data cannot show this" rather than a guess.

6. **Turn findings into next steps.** Add `## What we change` to the report: at most three
   actions, each naming the number that triggered it and the number to check later. Use the
   table below. One action per finding, never a claim that the change will work.

   | Finding | Next step |
   |---|---|
   | One step loses far more than its neighbours (such as 40% at tutorial step 3) | Watch 3 to 5 players at that step (a playtest or a recording). Open a User paths chart backward from the next step. Fix that one step: shorter, skippable, a clearer prompt. Compare the step on the new build. Guide: https://manalens.dev/blog/first-session-funnel-ftue?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=player_funnel |
   | Big drop between store visit and download or first open | The store page, the demo button or the download, not the game. Check that the demo is on the page and the link goes to the app page. |
   | Many players whose last event is `game_open`, or 0 to 5 minute playtime | Check crashes and load errors first (Manalens Game health template, or the tool's crash report), then the first minute. |
   | Fine tutorial, low D1 | The first session ends with no reason to return. Test a clear goal or unlock at the end of session 1. |
   | One source has the lowest D1 or D7 with 30+ players per cohort | Its posts may promise a different game. Find the posts behind it (`utm_content`, see `marketing-retro`) and compare their hook to the first 10 minutes. Do not cut the channel on retention alone: check its wishlists and sales with `marketing-retro` or `attribution-report`. |
   | Fails pile up on one level | A difficulty spike. Check fails per attempt on that level before you change it. |

7. **Dashboard, only if the user asked.** Never create or change a dashboard on your own. If the
   user asked for a dashboard, follow [references/queries.md](references/queries.md) section 8:
   `get_dashboards`, then `save_dashboard` (name "Game health", or another board if the
   built-in Game health crash board exists and the user prefers), then `save_chart` for the
   funnel, retention and paths charts (every plan) and the SQL charts (Studio, after
   `preview_chart`). Funnel, retention and paths charts cannot be previewed; tell the user to open
   the board. List every chart you added.

8. **Check.** Run:

   ```bash
   test -s marketing/player-funnel/2026-11-26.md && grep -c "^## " marketing/player-funnel/2026-11-26.md \
     && grep -q "^## What we change" marketing/player-funnel/2026-11-26.md && echo ok
   ```

   It prints a count of 3 or more and `ok`. On the Manalens paths, write the report by hand with
   the same section names (Funnel, Retention, Playtime, Where players quit, Read with care,
   What we change). Then tell the user the path and the single biggest drop.

## Output

`marketing/player-funnel/YYYY-MM-DD.md`, Markdown:

- **Funnel:** per step: players, dropped off, step conversion, overall conversion, median time
  from the previous step; one table per source with `--by`.
- **Retention:** one row per install week: players, day 1, 7 and 30 share, with "(of N)" when
  only N players have reached that day, and a note for cohorts under 30.
- **Playtime:** players per bucket (0 to 5 minutes up to 5 hours or more), median, P25, P75.
- **Where players quit:** last event before churn, with level or step.
- **Read with care:** small groups, missing events, what the data cannot show.
- **What we change:** up to three actions with the number to check and when.

## Measure

- After a fix ships, run the same funnel split by build (`--by properties.build`, or the
  **Build** breakdown in Manalens) and compare the fixed step for players on the new build.
  Wait for at least 30 players per build past that step, usually one to two weeks.
- Retention by source pairs with `marketing-retro`: keep `utm_source` as the platform and
  `utm_content` as the post ID (see `docs/LINKS.md`), so a churn-fast source leads back to posts.
- Re-run monthly; D30 needs 30 days after the last cohort day before it is complete.

## Gotchas

- **Lower counts than expected:** players did steps in another order, skipped one, or played on
  a second device. Remove a middle step, or check with a User paths chart.
- **Website and game are two people:** a native build has its own ID. A funnel from store visit
  to first open only joins with `identify()`, a handoff link, or install matching. Without one,
  start the funnel at `game_open` and read the store step from store data.
- **Retention looks like 0% for new weeks:** days that have not happened yet. The script and the
  SQL leave them out; spreadsheets often do not.
- **Last day is partial:** an export that ends today undercounts today. End the range yesterday.
- **Steam UTM tags stop at the store:** Steam counts tagged visits and wishlists in Steamworks,
  but the game build never sees the tag. Source per install comes from your website (install
  matching, a handoff link) or a separate demo key or build per channel.
- **Correlation:** TikTok players retaining worse may mean a younger or more casual audience, not
  bad content. Say "goes with", never "causes".
- **Numbers as strings:** `level` may be `3` or `"3"`. The script compares both; in SQL use
  `JSONExtractRaw` (see the queries file).
- **Heartbeats as quit points:** skip housekeeping events with `--ignore` (default:
  `session_start,session_end,heartbeat,app_crash`).
- **Raw exports hold personal data:** the European Commission counts cookie IDs, IP addresses
  and advertising IDs as personal data, and pseudonymised data that can be re-identified still
  counts. Keep the raw CSV out of the repo and out of the report: the report holds counts and
  rates, never user IDs. Do not paste raw rows into another AI chat. For a question about one
  player, look in the analytics tool.

## Version notes

- Manalens: `execute_query` and `preview_chart` need the Studio plan (or trial) and the
  `query:read` scope; Indie gets `402` `PLAN_UPGRADE_REQUIRED`. Results up to 200 rows, 8 seconds,
  256 MiB, 10 queries a minute. `get_analytics` returns up to 100 rows; `top_events` lists the
  first 20 events. Funnel (2 to 5 steps, window 60 seconds to 90 days), retention (daily: days 0
  to 30) and user paths charts work on every plan, have no SQL, and `preview_chart` refuses them.
  A dashboard holds up to 24 charts. Dashboard changes need `dashboards:write`.
- Manalens SDKs (Godot, Unity, Unreal) send `game_open` (with `is_first_open`),
  `session_start` and `session_end` (with `duration_s`). A browser game or HTTP app events must
  send them with `track`.
- Steam refunds: within 14 days of purchase and under 2 hours of playtime.
- GameAnalytics Benchmarks Hub, PC, October 2026: D1 6.54%, D7 1.44%, D30 0.19% (median).
- Last verified 2026-11-26.
