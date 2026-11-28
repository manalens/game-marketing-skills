---
name: tracking-plan
description: >
  Designs the analytics event plan for an indie game, its demo, its store page and its website,
  then adds the tracking calls to the code. Detects the engine (Godot, Unity, Unreal, web), proposes
  about 10 snake_case events of its own (fewer than 15) from site visit and wishlist click to
  install, tutorial, levels, settings and purchase, links web visitors to game players, writes
  analytics/tracking-plan.md and a CSV, instruments the code, and checks that every planned
  event is sent and nothing else is.
  Use for "what events should I track in my game", "add analytics to my Godot game", "set up a
  tracking plan for my demo", "track tutorial drop-off", "instrument my Unity game" or "is my
  analytics set up right". Works with any analytics tool; Manalens SDKs are the documented default.
  Not for reading the results (`player-funnel`, `attribution-report`, `marketing-retro`).
---

# Tracking plan

Plan the few events that answer a marketer's questions, then send them. The agent reads the repo,
writes `analytics/tracking-plan.md` and `analytics/tracking-plan.csv`, adds the calls to the game
and site code, and runs `scripts/check_plan.py` to prove the code matches the plan.

The questions the plan must answer: which links bring players who play, where new players stop,
whether they come back, whether the build is stable, and who pays. Every event maps to one of them.
An event with no question gets cut.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **Engine and platforms.** Detect from files (step 1). Ask only if two engines are present.
2. **Game type and core loop.** From the README, store page text or scene names. Levels, runs,
   matches or days decide the play events.
3. **What ships.** Demo, early access or full game; Steam, itch.io, web, mobile. From
   `export_presets.cfg`, `steam_appid.txt`, CI config, or ask.
4. **Analytics tool.** Grep for an existing SDK (see `references/sdk-calls.md`, section 1). Manalens
   if none and the user agrees; else their tool through a stub.
5. **Website repo or folder,** if the site is in scope. Its wishlist and demo buttons are events too.
6. **Audience.** Is the game for children? It changes the plan (`references/privacy.md`).

## Workflow

1. **Detect the engine and platforms.** Run from the repo root:

   ```bash
   ls project.godot ProjectSettings/ProjectVersion.txt *.uproject package.json export_presets.cfg steam_appid.txt 2>/dev/null
   grep -h "config/features\|m_EditorVersion\|EngineAssociation" project.godot ProjectSettings/ProjectVersion.txt *.uproject 2>/dev/null
   ```

   Output: one line, such as "Godot 4.3, Windows and Web exports, Steam demo, no analytics yet".
   Godot 3 has no Manalens addon: use the HTTP path or a stub.

2. **Find the hooks.** Grep for the moments the plan needs: tutorial steps, level or run start
   and end, death, win screen, options menu apply, store or wishlist buttons, `OS.shell_open` /
   `Application.OpenURL` / `LaunchURL`, quit. Output: a list of `file:line` per moment. A moment with
   no clear hook gets a TODO in the plan, not a guess.

3. **Propose the plan.** Start from `assets/tracking-plan.csv` (18 rows: 11 events your code
   sends, the rest sent by an SDK or counted by Steam) and cut or rename to fit. Keep about 10
   events of your own and fewer than 15 (owner `game`, `web` or `server`; automatic SDK events
   and Steam rows do not count). Manalens docs say most games need fewer than 15, and Google lists
   11 recommended events for games. `check_plan.py` warns at 15. Mixpanel warns that tracking
   every action a user can take leads to wasted development work and unused data, so add an
   event later, when a question needs it. The funnel steps, in order:

   | Step | Events (defaults) | Sent by |
   |---|---|---|
   | `visit` | `page_view` with UTM tags; `store_page_visit` | Web SDK; Steam UTM Analytics |
   | `wishlist` | `wishlist_clicked` (`store`, `placement`) on site and in game | Your code |
   | `install` | `demo_download` on the site; `game_open` with `is_first_open` | Your code; game SDK |
   | `tutorial` | `tutorial_step` (`step`, `step_name`), `tutorial_complete` | Your code |
   | `play` | `level_start`, `level_complete`, `level_fail` (`level`, `attempt`, `score`); one `feature_used` | Your code |
   | `return` | `session_start`, `session_end` (`duration_s`) | Game SDK |
   | `purchase` | `purchase` (`amount_cents`, `currency`, `store`) for in-game or own-site sales | Your code or server |
   | `identity` | `website_opened` from the game with a handoff link; `identity_handoff` on the site | Your code; web SDK |
   | `health` | `settings_changed` (`setting`, `value`); `error`; `game_crash` | Your code; game SDK |

   - Runs, not levels: `run_start` and `run_end` with `outcome`. Matches: `match_start`,
     `match_end`. Genre plans with properties: https://manalens.dev/tracking-plans?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=tracking_plan
   - `settings_changed` only for settings that hint at a problem: graphics quality down, difficulty
     down, subtitles or text size up, controls rebound. Send the new value from a fixed list.
   - A Steam premium sale happens on Steam, not in the game. Read it from Steamworks, not `purchase`.
   - Show the table to the user and wait for a yes before step 4.

4. **Name things by the rules.**
   - `object_action` in snake_case, past tense from the player's side: `tutorial_step`,
     `wishlist_clicked`, `level_fail`. Reserved single words: `purchase`, `resource`, `error`.
   - One event, many values: `level_complete` with `level: 3`, never `level_3_complete`.
   - Two to five properties per event. Numbers as numbers. The same property name means the same
     thing on every event.
   - Flat properties only: strings, numbers, booleans or null. The Manalens SDKs drop lists and
     nested objects and cut strings at 1,024 characters.
   - No `build`, `platform`, `storefront` or `app_version` property. The game SDKs put them in the
     context of every event from `init()`; a hand-set copy can disagree with the real build after
     a patch.
   - Check names against Google's 11 recommended events for games in GA4 (`tutorial_begin`,
     `tutorial_complete`, `level_start`, `level_end`, `level_up`, `post_score`, `unlock_achievement`,
     `earn_virtual_currency`, `spend_virtual_currency`, `join_group`, `select_content`). Use them as
     a naming reference, not a plan: a premium game with no currency needs no currency events.
   - No personal data and no free text (`references/privacy.md`).
   - Use the same name on the site and in the game (`wishlist_clicked` in both, with `placement`).
   - Manalens reads the standard names (`game_open`, `level_*`, `purchase`, `error`) in its game
     dashboards, so keep them where they fit.

5. **Write the plan.** Two files:
   - `analytics/tracking-plan.csv` with `event,description,properties,trigger,funnel_step,owner`.
     `properties` is `;`-separated. `owner` is `game`, `web`, `server`, `sdk` (sent by the SDK on
     its own) or `external` (counted elsewhere, such as Steam UTM Analytics); `web;game` for both.
   - `analytics/tracking-plan.md`: the questions, the table, the hook (`file:line`) per event, the
     UTM convention (`docs/LINKS.md`: `utm_source` = platform, `utm_campaign` = beat,
     `utm_content` = post ID; in-game buttons use `utm_source=ingame`, no `utm_medium`, and a
     placement with underscores in `utm_content`, such as `demo_end`), consent choice, and what the plan cannot show.

   Run `python3 skills/measure/tracking-plan/scripts/check_plan.py analytics/tracking-plan.csv`
   and fix every ERROR before writing code.

6. **Instrument.** Add the calls at the hooks from step 2, with the exact API in
   `references/sdk-calls.md` (Godot `Manalens.track()`, Unity `Manalens.Track()`, Unreal
   `UManalensSubsystem::Track()`, web `analytics.track()`). Docs:
   https://docs.manalens.dev/sdks/overview
   - SDK setup: `init()` once at boot with `build` set to `dev` in the editor. Never paste a Secret
     key; the Publishable key (`mana_pk_`) is the only one that goes in a build. Leave a
     `YOUR_PUBLISHABLE_KEY` placeholder if the user has not given one.
   - Do not send `game_open`, `session_*`, `error` or `game_crash` by hand: the game SDKs do.
   - Every link from the game to the site goes through `Manalens.link_url(url)` (Godot),
     `Manalens.LinkUrl(url)` (Unity) or `LinkUrl` (Unreal), so the web visit joins this player.
   - Store buttons send `wishlist_clicked` first, then open the tagged store URL.
   - Consent: if needed, `consent_required: true` and a call to `set_consent()` from a consent
     screen. Kids' games: consent mode, no `identify()`, no `link_url()`.
   - No Manalens? Add the stub wrapper from `references/sdk-calls.md` section 7 and call it
     everywhere. Never call two tools from game code directly.
   - Show the diff. Do not commit.

7. **Check.** Run against the game and, if present, the site:

   ```bash
   python3 skills/measure/tracking-plan/scripts/check_plan.py analytics/tracking-plan.csv \
     --code . --code ../my-site
   ```

   It exits 0 when every `game`, `web` and `server` event is sent and every sent event is planned.
   Use `--owner game` to check only the game when the site lives elsewhere, and `--require` to change
   the required funnel steps (a game with no store page yet: `--require install,tutorial,play`).
   A game that already sends Title Case names (`Level Completed`, Segment style) keeps them:
   pass `--names title` rather than renaming events that have history.
   Fix each ERROR and run again. Read each WARN and say in the plan why it stays.

8. **Ask the user to play a dev build and report back.** Then confirm events arrive (Measure).

## Output

- `analytics/tracking-plan.csv`: one row per event, the six columns above.
- `analytics/tracking-plan.md`: questions, event table with hooks, UTM rules, consent and privacy
  notes, the check command, and a "cannot show" list.
- Code changes: the SDK init, the track calls, the handoff links, and (without Manalens) one
  analytics wrapper file. Shown as a diff, not committed.

## Measure

- After a dev play-through, check every planned event arrived once with the right properties. With
  Manalens connected (scope `analytics:read`), call `get_analytics`:

  ```json
  {"report": "top_events", "date_from": "2026-11-26", "date_to": "2026-11-26",
   "filters": [{"field": "app_build", "op": "eq", "value": "dev"}]}
  ```

  `top_events` lists the first 20 events only. For one event, use `report: "kpis"` with
  `{"field": "event", "op": "eq", "value": "tutorial_complete"}`. No Manalens? Read the tool's
  live event view or debug log (Manalens SDKs print each event with `debug: true`).
- A week after release, the plan feeds `player-funnel` (tutorial and level drop-off),
  `attribution-report` (`wishlist_clicked` and installs by `utm_campaign`) and `marketing-retro`.
- The number to watch first: share of `game_open` with `is_first_open` that reach
  `tutorial_complete`.
- With Manalens, add each event and what it means to the Agent's project memory (an item holds
  up to 280 characters, a project up to 80 items), so Agent questions use the plan's names. Keep the
  same text next to the plan, so both change when an event is renamed.

## Gotchas

- **Events from the developer's machine fill the reports:** dev and live share one project. Set
  `build` to `dev` in the editor and filter it out.
- **`check_plan.py` says "never sent" for a call that exists:** the name comes from a variable or a
  constant. The script warns about non-literal names. Use literals at the call site, or check by
  hand and note it in the plan.
- **Unreal Blueprints:** calls in `.uasset` files are binary and the grep cannot see them. List the
  Blueprint graphs by hand in the plan.
- **Names split history:** renaming `level_complete` later breaks every chart. Agree on names before
  code. Add a property instead of a new name.
- **`tutorial_step` that fires twice:** a replayed tutorial or a reloaded scene double counts. Send
  on the step's first completion per save, or add `attempt`.
- **Too many events:** a `button_clicked` on every button floods the queue and answers nothing. Track
  completed actions. Never send an event every frame or every second (such as player position).
- **UTM on Steam is a floor:** many players search Steam later. `store_page_visit` numbers come from
  Steam UTM Analytics, not from game code.
- **Consent hides people:** with consent mode, players who decline are not counted at all.
- **Web export on a portal gets 403:** add the portal host in Manalens **Allowed origins**
  (`*.itch.zone` is allowed by default).

## Version notes

- Manalens SDKs (docs read 2026-11-26): Godot 4 addon (`init`, `track`, `identify`, `set_consent`,
  `link_url`; automatic `game_open`, `session_start`, `session_end`, `error` on 4.5+,
  `game_crash`), Unity (`Init`, `Track`, `LinkUrl`), Unreal (settings, `Track` with three
  maps, `LinkUrl`), web SDK (`track`, automatic page views and UTM, `identity_handoff`). Handoff
  links expire after 10 minutes. Event limits: names 1 to 128 characters, at most 50 properties and
  8 KB, string values cut at 1,024 characters. Events older than 7 days are refused. Platform,
  storefront, app version, build and engine travel in each event's context.
- Google GA4 recommended events for games: 11 names (Google Analytics Help, read 2026-11-26).
- Manalens MCP: `get_analytics` reports `kpis`, `event_timeseries`, `top_pages`, `top_sources`,
  `top_events`; filter fields include `event`, `app_build` and `properties.<key>`.
- Platform rules in `references/privacy.md` change. Re-read Apple, Google and console rules before a
  mobile or console release.
- Last verified 2026-11-26.
