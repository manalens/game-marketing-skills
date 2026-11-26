# Sources

Written in our own words. Checked 2026-11-26.

- Manalens docs, Funnels: https://docs.manalens.dev/features/funnels (2 to 5 steps, Sequential
  or Any order, conversion window, breakdowns with first or last touch, median time per step,
  conversion insights are correlation).
- Manalens docs, Retention: https://docs.manalens.dev/features/retention (cohorts by first entry
  event, recurring and rolling, daily periods 0 to 30, incomplete periods never counted as 0%,
  breakdown by the first value of a property, Did not return list).
- Manalens docs, User paths: https://docs.manalens.dev/features/user-paths (backward from a step,
  counts sessions, not people).
- Manalens docs, Explorer: https://docs.manalens.dev/features/explorer (`raw_events` and
  `sessions` columns, SQL limits, Studio plan).
- Manalens docs, MCP charts and overview: https://docs.manalens.dev/mcp/charts and
  https://docs.manalens.dev/mcp/overview (scopes, `execute_query`, `preview_chart` runs SQL specs
  only, chart spec for funnel, retention and paths, Indie `402`).
- Manalens docs, Game events and metrics: https://docs.manalens.dev/data/events/game and
  https://docs.manalens.dev/data/metrics (`game_open` with `is_first_open`, `session_end` with
  `duration_s`, D1, D7 and D30 definitions).
- Manalens docs, Install attribution: https://docs.manalens.dev/attribution/installs
  (`context.install_match_anon_id` on the first open).
- Manalens blog, first session funnel: https://manalens.dev/blog/first-session-funnel-ftue
- Manalens blog, PC retention benchmarks, quoting the GameAnalytics Benchmarks Hub (PC, desktop
  builds, October 2026): https://manalens.dev/blog/pc-indie-game-retention-benchmarks
- Steam refund policy (14 days, under 2 hours of playtime):
  https://store.steampowered.com/steam_refunds/
- ClickHouse `windowFunnel`: https://clickhouse.com/docs/sql-reference/aggregate-functions/parametric-functions#windowfunnel
- The SQL in `queries.md` was run against ClickHouse 26.11 (embedded) on synthetic events with
  the `raw_events` and `sessions` columns, and matched `scripts/funnel.py` on the same data.
