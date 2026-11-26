# SQL templates for Manalens

Contents:

1. Rules that every query here follows
2. Step funnel with conversion
3. Median time between two steps
4. Retention by install week (day 1, 7, 30)
5. Retention by utm_source of the first session
6. Playtime distribution
7. Last event before churn
8. Saving charts (only when the user asks)

These run with `execute_query` (or in the Explorer). They need the Studio plan or a Studio
trial. On Indie, `execute_query` returns `402` `PLAN_UPGRADE_REQUIRED`: use the Indie path in
[SKILL.md](../SKILL.md). Checked on 2026-11-26 against ClickHouse 26.11 with synthetic data shaped
like `raw_events` and `sessions`.

## 1. Rules

From `describe_schema` and the Explorer docs:

- One `SELECT` or `WITH` statement over `raw_events`, `sessions` or `session_events`. No SQL
  comments, no `SETTINGS`, no `numbers()`. Do not name a CTE `sessions`, `session_events` or
  `raw_events`.
- At most 200 result rows, 8 seconds, 256 MiB. 10 queries a minute per person.
- `raw_events` has bot rows: keep `JSONExtractString(context, 'device') != 'bot'`.
- Pass `date_from` and `date_to` (`YYYY-MM-DD`) to `execute_query`; they fill `{{date_from}}`
  and `{{date_to}}`. Default: the last 30 days. For day 30 retention, use 90 days and set
  `date_to` to yesterday.
- `sessions` follows the date range by itself. Never add a date condition to it.
- A player here is `if(user_id != '', user_id, anonymous_id)`. That joins only the rows that carry
  the `user_id`. Manalens's own funnel and retention charts also join IDs linked by `identify()`
  or a handoff link, so their counts can be higher.
- Numbers in `properties` (such as `level: 3`) are not strings. Read them with
  `JSONExtractFloat`, or with `trim(BOTH '"' FROM JSONExtractRaw(properties, 'level'))` when the
  value can be a number or a name.

Replace the event names with the user's own. Check them first with `describe_schema` (its
`events` list) or `get_analytics` `top_events`.

## 2. Step funnel with conversion

`windowFunnel(window_seconds)` returns how many steps in a row each player reached, in order,
within the window from the first step. Other events may happen between steps (the "Sequential"
mode of the funnel chart). Up to 32 steps; keep 3 to 7.

Example: first open, tutorial done, a first session of 10 minutes or more, level 3, purchase,
within 7 days.

```sql
WITH per_player AS (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        windowFunnel(604800)(
            toDateTime(original_timestamp),
            event = 'game_open',
            event = 'tutorial_complete',
            event = 'session_end' AND JSONExtractFloat(properties, 'duration_s') >= 600,
            event = 'level_complete' AND trim(BOTH '"' FROM JSONExtractRaw(properties, 'level')) = '3',
            event = 'purchase'
        ) AS reached
    FROM raw_events
    WHERE type = 'track'
        AND (user_id != '' OR anonymous_id != '')
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
),
steps AS (
    SELECT step, countIf(reached >= step) AS players
    FROM per_player
    ARRAY JOIN [1, 2, 3, 4, 5] AS step
    GROUP BY step
)
SELECT
    step,
    players,
    lagInFrame(players, 1, players) OVER (ORDER BY step ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) - players AS dropped_off,
    round(players / lagInFrame(players, 1, players) OVER (ORDER BY step ROWS BETWEEN 1 PRECEDING AND CURRENT ROW), 4) AS step_conversion,
    round(players / max(players) OVER (), 4) AS overall_conversion
FROM steps
ORDER BY step
```

Change the step list in two places: the conditions in `windowFunnel` and the array
`[1, 2, 3, 4, 5]` (one number per step).

- **A website step first** (store or site visit): add `type IN ('page', 'track')` and use
  `type = 'page' AND JSONExtractString(context, 'page', 'path') = '/demo'` as a step. This only
  joins when the website and the game share an ID (a browser game, or `identify()` with the same
  `user_id`). For a native build, use the funnel chart (section 8) or start at `game_open`.
- **By source:** add `argMin(JSONExtractString(context, 'utm_source'), original_timestamp) AS source`
  to `per_player`, then `GROUP BY source, step` and partition the window functions by source:
  `OVER (PARTITION BY source ORDER BY step ...)`. Game events usually carry no UTM tags; see
  section 5 for the source of a native install.
- **Tutorial steps:** one condition per step, such as
  `event = 'tutorial_step' AND JSONExtractFloat(properties, 'step') = 3`.

## 3. Median time between two steps

For players who did both, in order. `minIf` returns 1970 when a player never did the event, so
the `HAVING` keeps only players who did both.

```sql
SELECT
    count() AS players,
    round(quantile(0.5)(dateDiff('second', a, b)) / 60, 1) AS median_minutes,
    round(quantile(0.9)(dateDiff('second', a, b)) / 60, 1) AS p90_minutes
FROM (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        minIf(original_timestamp, event = 'game_open') AS a,
        minIf(original_timestamp, event = 'tutorial_complete') AS b
    FROM raw_events
    WHERE type = 'track'
        AND event IN ('game_open', 'tutorial_complete')
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
    HAVING countIf(event = 'game_open') > 0 AND countIf(event = 'tutorial_complete') > 0 AND b >= a
)
```

## 4. Retention by install week (day 1, 7, 30)

Cohort: the week (Monday) of the first `game_open` with `is_first_open` true, the install event
the Godot, Unity and Unreal SDKs send. Return: a `session_start` on exactly day N (the
"Recurring" type of the retention chart). A day N that is not over yet for a player is left out
of both the count and the share, so partial weeks never show as 0%.

```sql
WITH installs AS (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        toDate(min(original_timestamp)) AS first_day
    FROM raw_events
    WHERE type = 'track'
        AND event = 'game_open'
        AND JSONExtractBool(properties, 'is_first_open')
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
),
returns AS (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        groupUniqArray(toDate(original_timestamp)) AS days
    FROM raw_events
    WHERE type = 'track'
        AND event = 'session_start'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
),
last_day AS (
    SELECT least(toDate({{date_to}}), yesterday()) AS d
)
SELECT
    toMonday(i.first_day) AS cohort_week,
    count() AS players,
    countIf(i.first_day + 1 <= (SELECT d FROM last_day)) AS d1_players,
    round(countIf(i.first_day + 1 <= (SELECT d FROM last_day) AND has(r.days, i.first_day + 1)) / nullIf(d1_players, 0), 4) AS d1,
    countIf(i.first_day + 7 <= (SELECT d FROM last_day)) AS d7_players,
    round(countIf(i.first_day + 7 <= (SELECT d FROM last_day) AND has(r.days, i.first_day + 7)) / nullIf(d7_players, 0), 4) AS d7,
    countIf(i.first_day + 30 <= (SELECT d FROM last_day)) AS d30_players,
    round(countIf(i.first_day + 30 <= (SELECT d FROM last_day) AND has(r.days, i.first_day + 30)) / nullIf(d30_players, 0), 4) AS d30
FROM installs AS i
LEFT JOIN returns AS r ON r.player = i.player
GROUP BY cohort_week
ORDER BY cohort_week
```

- `dN_players` is the players whose day N is over. Flag any cohort where it is under 30.
- An empty (`NULL`) share means no player in the cohort has reached that day yet.
- **Rolling** retention (returned on day N or later): replace `has(r.days, i.first_day + 7)` with
  `arrayExists(x -> x >= i.first_day + 7, r.days)`.
- **No `is_first_open`** (a browser game or HTTP app events that do not send it): use the first
  `game_open` in a range that starts before the game came out, or the cohorts start with
  returning players.
- A day here is a UTC calendar day, as in the Manalens retention chart.

## 5. Retention by utm_source of the first session

The source is the landing source of the player's first session in the `sessions` table (the same
sessions as the Overview). A native build has its own `anonymous_id`, so the query uses the
website visitor that install matching linked to the first open
(`context.install_match_anon_id`), and falls back to the install's own ID (a browser game).

```sql
WITH installs AS (
    SELECT
        anonymous_id AS player,
        argMin(if(JSONExtractString(context, 'install_match_anon_id') != '', JSONExtractString(context, 'install_match_anon_id'), anonymous_id), original_timestamp) AS web_id,
        toDate(min(original_timestamp)) AS first_day
    FROM raw_events
    WHERE type = 'track'
        AND event = 'game_open'
        AND JSONExtractBool(properties, 'is_first_open')
        AND anonymous_id != ''
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
),
first_source AS (
    SELECT
        anonymous_id,
        argMin(if(utm_source != '', utm_source, if(channel_type != '', concat('(', channel_type, ')'), '(Direct)')), first_at) AS source
    FROM sessions
    GROUP BY anonymous_id
),
returns AS (
    SELECT anonymous_id AS player, groupUniqArray(toDate(original_timestamp)) AS days
    FROM raw_events
    WHERE type = 'track'
        AND event = 'session_start'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
),
last_day AS (
    SELECT least(toDate({{date_to}}), yesterday()) AS d
)
SELECT
    if(s.source = '', '(no website visit)', s.source) AS source,
    count() AS players,
    countIf(i.first_day + 1 <= (SELECT d FROM last_day)) AS d1_players,
    round(countIf(i.first_day + 1 <= (SELECT d FROM last_day) AND has(r.days, i.first_day + 1)) / nullIf(d1_players, 0), 4) AS d1,
    countIf(i.first_day + 7 <= (SELECT d FROM last_day)) AS d7_players,
    round(countIf(i.first_day + 7 <= (SELECT d FROM last_day) AND has(r.days, i.first_day + 7)) / nullIf(d7_players, 0), 4) AS d7,
    countIf(i.first_day + 30 <= (SELECT d FROM last_day)) AS d30_players,
    round(countIf(i.first_day + 30 <= (SELECT d FROM last_day) AND has(r.days, i.first_day + 30)) / nullIf(d30_players, 0), 4) AS d30
FROM installs AS i
LEFT JOIN returns AS r ON r.player = i.player
LEFT JOIN first_source AS s ON s.anonymous_id = i.web_id
GROUP BY source
ORDER BY players DESC
LIMIT 50
```

- A source in brackets, such as `(Organic Search)`, had no `utm_source`; it is the channel.
- `(no website visit)` is an install with no matched visit in the date range: Steam search,
  a key, a phone to PC switch. Often the biggest row. It is not "bad traffic".
- `sessions` can hit the memory limit above about 200,000 page views and custom events in the
  range. Then shorten the range, or use the retention chart with a `utm_source` breakdown.
- For one cohort week per source, add `toMonday(i.first_day) AS cohort_week` and group by both.
  Each cell gets small fast: flag every cell under 30 players.

## 6. Playtime distribution

Total playtime per player from the `duration_s` of `session_end` (sent by the Godot, Unity and
Unreal SDKs). Two queries: buckets, then quantiles.

```sql
SELECT
    multiIf(minutes < 5, '0-5 min', minutes < 15, '5-15 min', minutes < 30, '15-30 min', minutes < 60, '30-60 min', minutes < 120, '1-2 h', minutes < 300, '2-5 h', '5 h+') AS bucket,
    count() AS players,
    round(count() / sum(count()) OVER (), 4) AS share
FROM (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        sum(JSONExtractFloat(properties, 'duration_s')) / 60 AS minutes
    FROM raw_events
    WHERE type = 'track'
        AND event = 'session_end'
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
)
GROUP BY bucket
ORDER BY min(minutes)
```

```sql
SELECT
    count() AS players,
    round(quantile(0.25)(minutes), 1) AS p25_minutes,
    round(quantile(0.5)(minutes), 1) AS median_minutes,
    round(quantile(0.75)(minutes), 1) AS p75_minutes,
    round(quantile(0.9)(minutes), 1) AS p90_minutes,
    round(countIf(minutes >= 120) / count(), 4) AS share_over_2h
FROM (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        sum(JSONExtractFloat(properties, 'duration_s')) / 60 AS minutes
    FROM raw_events
    WHERE type = 'track'
        AND event = 'session_end'
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
)
```

A session that never sent `session_end` (a crash, a killed process) adds nothing here.
`share_over_2h` matters for a paid game on Steam: a refund needs under 2 hours of playtime.

## 7. Last event before churn

Churned: no event in the last 7 days before `date_to`, and first seen before that. The last event
skips session housekeeping, so it shows what the player did last. `level` and `step` show where.

```sql
WITH per_player AS (
    SELECT
        if(user_id != '', user_id, anonymous_id) AS player,
        min(original_timestamp) AS first_seen,
        max(original_timestamp) AS last_seen,
        argMaxIf(event, original_timestamp, event NOT IN ('session_start', 'session_end', 'heartbeat', 'app_unclean_exit')) AS last_event,
        argMaxIf(trim(BOTH '"' FROM JSONExtractRaw(properties, 'level')), original_timestamp, event NOT IN ('session_start', 'session_end', 'heartbeat', 'app_unclean_exit')) AS last_level,
        argMaxIf(trim(BOTH '"' FROM JSONExtractRaw(properties, 'step')), original_timestamp, event NOT IN ('session_start', 'session_end', 'heartbeat', 'app_unclean_exit')) AS last_step
    FROM raw_events
    WHERE type = 'track'
        AND channel = 'app'
        AND JSONExtractString(context, 'device') != 'bot'
        AND original_timestamp >= toDateTime({{date_from}})
        AND original_timestamp < toDateTime({{date_to}}) + INTERVAL 1 DAY
    GROUP BY player
)
SELECT
    last_event,
    last_level,
    last_step,
    count() AS players,
    round(count() / sum(count()) OVER (), 4) AS share_of_churned
FROM per_player
WHERE last_seen < toDateTime({{date_to}}) + INTERVAL 1 DAY - INTERVAL 7 DAY
    AND first_seen < toDateTime({{date_to}}) + INTERVAL 1 DAY - INTERVAL 7 DAY
GROUP BY last_event, last_level, last_step
ORDER BY players DESC
LIMIT 30
```

- `channel = 'app'` keeps game events only, so a player who last visited the website still counts
  by their last game event. Drop it for a browser game on the Web SDK without the `app` option.
- A last event of `level_fail` on one level, or `tutorial_step` 3, is a quit point to look at.
  `game_open` as the last event often means a crash or a black screen at start: check the
  Game health template (errors) before you blame the design.
- A crash that kills the game before it sends an event shows the event before the crash.

## 8. Saving charts (only when the user asks)

Never create or change a dashboard unless the user asked. Then:

1. `list_dashboards` (needs `dashboards:read`). Manalens has a built-in **Game health** template
   for crash charts. If a "Game health" board exists, ask whether to add the player charts to it
   or to make a new board. A board holds up to 24 charts.
2. `create_dashboard` with `{"name": "Game health", "description": "Player funnel, retention and playtime"}`
   (needs `dashboards:write`). Use the returned id as `boardId`.
3. Preview each SQL chart with `preview_chart`, then save it with `create_chart`. A chart's SQL
   must use `received_at >= toDateTime({{date_from}}) AND received_at < toDateTime({{date_to}}) + INTERVAL 1 DAY`
   or the same on `original_timestamp`, so it follows the dashboard range. Funnel, retention and
   paths charts have no SQL: `preview_chart` refuses them; save them and open the board.

Funnel chart (works on every plan; joins linked IDs; `funnel_type` `closed` is Sequential,
`open` is Any order; window 60 seconds to 90 days):

```json
{"boardId": "<id>", "title": "Demo funnel", "description": "First open to purchase, 7 days",
 "spec": {"version": 1,
  "query": {"kind": "funnel",
   "steps": [{"type": "track", "value": "game_open"},
             {"type": "track", "value": "tutorial_complete"},
             {"type": "track", "value": "level_complete"},
             {"type": "track", "value": "purchase"}],
   "settings": {"window_seconds": 604800, "funnel_type": "closed",
                "breakdown": "utm_source", "breakdown_touch": "first"}},
  "view": {"mark": "x-funnel"}}}
```

A step can carry `filters` with the `get_analytics` operator shape, for example
`{"type": "track", "value": "level_complete", "filters": [{"field": "properties.level", "op": "eq", "value": "3"}]}`
(at most 10 per step; fields and operators as in `get_analytics` `filters`).

Retention chart (daily periods give D1, D7 and D30; `rolling` or `recurring`):

```json
{"boardId": "<id>", "title": "Install cohorts by source",
 "spec": {"version": 1,
  "query": {"kind": "retention",
   "settings": {"granularity": "day", "retention_type": "recurring",
                "entry_event": {"type": "track", "value": "game_open"},
                "return_event": {"type": "track", "value": "session_start"},
                "breakdown": "utm_source"}},
  "view": {"mark": "x-retention"}}}
```

User paths backward from a fail (what led to it):

```json
{"boardId": "<id>", "title": "Before level_fail",
 "spec": {"version": 1,
  "query": {"kind": "paths",
   "settings": {"anchors": [{"type": "track", "value": "level_fail"}], "direction": "backward",
                "excluded_events": ["session_start", "session_end"]}},
  "view": {"mark": "x-sankey"}}}
```

Tell the user the board name and each chart you added. Do not delete or edit their other charts.
