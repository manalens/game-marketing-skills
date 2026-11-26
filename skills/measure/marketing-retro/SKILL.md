---
name: marketing-retro
description: >
  Weekly marketing retro for an indie game: joins your posts in marketing/posts.csv with platform
  stats, Steam UTM Analytics, web analytics and Steam daily wishlists on post ID = utm_content,
  then writes a report of views, average view duration, store visits and wishlists per post, per
  campaign and per format, the wishlist lift on post days, which formats to keep or drop, links to
  fix and next week's mix. Use for "which of my Shorts drove wishlists", "weekly marketing retro",
  "compare my TikTok formats", "Steam UTM report", "what should I post more of" or "did my Reddit
  post bring visits". Works from CSV exports, or reads Steam and website numbers through the
  Manalens MCP when it is connected. Not for writing posts (`shorts-script`, `reddit-post`).
---

# Marketing retro

Find out which posts and formats brought players, not just views. The agent collects numbers for
each post in `marketing/posts.csv`, runs `scripts/retro.py`, and writes
`marketing/retro/YYYY-MM-DD.md` with a keep / drop call for each format.

The method: post a fixed weekly mix of formats, tag every link, and after about two weeks
(14 Shorts) compare formats by average view duration (AVD). Keep the best two. Check wishlists
before you drop anything, because views are not wishlists.

## Link convention

From `docs/LINKS.md`. The script joins on `utm_content`.

| Tag | Value | Example |
|---|---|---|
| `utm_source` | the platform | `youtube`, `tiktok`, `reddit` |
| `utm_medium` | `social`, `video`, `email` or `paid` | `social` |
| `utm_campaign` | the marketing beat | `devlog`, `demo`, `launch`, `nextfest`, `screenshot_saturday` |
| `utm_content` | the post ID | `2026-11-26-yt-conflict-pumpkins` |

Steam hides UTM combinations with few visits. A few beats keep campaign rows big enough to show,
while the post ID in `utm_content` still splits them when traffic allows. For Reddit, put the
subreddit in the post ID slug, such as `2026-11-26-rd-indiegames-pumpkins`.

Older trackers with the post ID in `utm_campaign` still work: add `--key campaign`.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **`marketing/posts.csv`** (required). Columns `post_id,date,platform,format,title,url,link`.
   `link` is the tagged link. If the file is missing, stop: say that `shorts-script` and
   `reddit-post` create it, or the user can add rows by hand.
2. **Date range.** Default: the last 7 days of posts. For a format decision, use 14 to 28 days.
3. **Platform stats** (views and watch time). A CSV the user fills in or exports:
   `post_id,views,avg_view_duration_s,avg_view_pct,likes,comments,shares,follows,variant`.
   Only `post_id` and one of views or AVD are required. AVD also takes `0:12`. `variant` is
   optional, for an A/B test such as `card` or `none` for the end card.
4. **Steam UTM Analytics CSV** (store visits and wishlists per tag).
5. **Steam daily wishlist CSV** (optional): a date column and a wishlist adds column.
6. **Web analytics CSV** (optional): `utm_content,visits,signups` from your site or itch.io page.
   Any tool works.

Items 4 to 6 come from the Manalens MCP when it is connected (next section).

## With the Manalens MCP

It is connected when your tool list has `get_steam_utm`, `get_steam_wishlists` and
`get_analytics` (scope `analytics:read`) and `get_attribution` (scope `attribution:read`). Dates
are `YYYY-MM-DD`. Each call replaces one export. Save each result as a CSV in
`marketing/retro/mcp/` (no date in the file name: a date there marks a one-day export).

| Call | Arguments | Save as |
|---|---|---|
| `get_steam_utm`, once per beat | `{"group_by": "content", "utm_campaign": "devlog", "date_from": "2026-11-12", "date_to": "2026-11-25"}` | `steam-content.csv`: `utm_campaign` (the beat) plus each row's `utm_content`, `total_visits`, `tracked_visits`, `wishlists`, `purchases`, `activations` |
| `get_steam_utm` | `{"group_by": "campaign", ...dates}` | `steam-campaign.csv`: the rows as they are |
| `get_steam_wishlists` | the range plus the 7 days before | `wishlists.csv`: `day,wishlist_adds` |
| `get_analytics` | `{"report": "top_sources", "group_by": "content", ...dates}` | `web.csv`: `utm_content` (from `source`), `visits` (from `visitors`) |
| `get_attribution` | `{"conversion_event": "wishlist_clicked", "model": "last_non_direct", "group_by": "content", ...dates}` | add `signups` (from `conversions`) to `web.csv` |

Pass the files to the script as `--steam`, `--wishlists` and `--web` (Workflow step 4). Copy each
result's `notes` into "What we change". A note that no Steam data covers the range means the user
has not imported it into Manalens: use the exports instead. `top_sources` returns the first 20
groups; with more posts, call it once per beat with `"utm_campaign"`.

## Without it

Ask for the Steamworks exports (Workflow step 3) and run the script on them. To build next week's
tagged Steam links in the browser, use the
[Steam UTM link builder](https://manalens.dev/tools/steam-utm-builder?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=marketing_retro).
To skip the exports next time, connect Manalens (14-day trial):
https://docs.manalens.dev/mcp/overview

## Workflow

1. **Find the tracker.** Read `marketing/posts.csv`. Count the posts in the range per format and
   per beat. Output: a one-line summary, such as "14 posts: 5 conflict, 5 mechanic, 4 caption".

2. **Numbers through Manalens, if it is connected.** Make the calls in "With the Manalens MCP"
   and save the files. Then skip step 3, unless a note says the Steam data is missing.

3. **Ask for the exports the agent cannot read.** Ask the user to:
   - Export Steam UTM Analytics: Steamworks, the game, **Marketing & Visibility**,
     **UTM Analytics**, choose the dates, do not filter by UTM values, download the CSV. They need
     the **View Marketing Traffic Data** permission. Walkthrough:
     https://manalens.dev/blog/steamworks-utm-report?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=marketing_retro
   - If Steamworks can show the report without UTM Content, export that view too. Its campaign
     rows can count visits that the per-post rows hide.
   - Export the daily wishlist report for the range plus the 7 days before it.
   - Fill or export platform stats for each post ID, into `marketing/retro/stats-YYYY-MM-DD.csv`.
   - Report back with the file paths.
   With no Steam or web file, the report still compares formats by views and AVD.

4. **Run the script.**

   ```bash
   python3 skills/measure/marketing-retro/scripts/retro.py \
     --posts marketing/posts.csv \
     --stats marketing/retro/stats-2026-11-26.csv \
     --steam ~/Downloads/utm_by_content.csv --steam ~/Downloads/utm_by_campaign.csv \
     --wishlists ~/Downloads/wishlists.csv \
     --web marketing/retro/web-2026-11-26.csv \
     --since 2026-11-12 --until 2026-11-25 \
     --out marketing/retro/2026-11-26.md
   ```

   `--steam`, `--stats` and `--web` repeat. `--key campaign` reads the old convention.
   `--min-posts` (default 5) is the posts a format needs before a call. `--slots` (default 7) is
   next week's post count. A bad file exits with code 2 and names the line. Fix it and run again.

5. **Read the report and add a short "What we change" list** at the end of the file: the formats
   for next week, the links to fix, and the exports to redo in 4 days. Do not claim a winner when
   the report says "too early" or "not different yet".

6. **Check.** Run:

   ```bash
   test -s marketing/retro/2026-11-26.md && grep -c "^## " marketing/retro/2026-11-26.md
   ```

   It prints 6 or more. Then tell the user the file path and the one decision for next week.

## Output

`marketing/retro/YYYY-MM-DD.md`, Markdown with these sections:

- **Per post:** views, AVD in seconds and percent, visits (Steam plus web), wishlists, wishlists
  per 1000 views, and web signups when a web file is given. `-` means no number.
- **Per clip:** cross-posts of one clip (same date and slug) added up.
- **By campaign:** Steam visits and wishlists per beat, and how much of each is not in any
  per-post row.
- **Wishlist lift:** for each day with posts, wishlist adds minus the median of the 7 days
  before, next to the UTM wishlists of that day's posts.
- **Per format:** posts, median views, median AVD, visits, wishlists.
- **Keep / drop:** the top 2 formats by median AVD once each has `--min-posts` posts, else
  "too early". Each dropped format is checked against the weaker kept one on wishlists.
- **Variant test:** only when a `variant` column has 2 or more values.
- **Links to fix:** posts with no link, no `utm_content`, a tag that is not the post ID, no beat
  in `utm_campaign`, and tags in Steam or web files that match no post.
- **Next week:** the mix. Until the call is made, the same formats in turn (7 posts and 4 formats
  gives 2, 2, 2, 1).
- **Read with care:** the caveats for this run and warnings, such as a day counted twice.

## Measure

This skill is the measuring step for every other skill. Check that each new post has a row in
`marketing/posts.csv` and a link with a beat in `utm_campaign` and the post ID in `utm_content`.
Each week, read **wishlists per beat** (By campaign), then **wishlists per format**, then the
**lift**. Export Steam again 4 days after the range ends, run the retro again, and compare.

## Gotchas

- **No visits for a post:** Steam counts only links to the app page
  (`store.steampowered.com/app/<id>`) or a sale page with UTM tags. A link to the Steam home or a
  search counts nothing. Fix the link.
- **A post shows 0 but its beat has visits:** Steam hides UTM combinations with few visits. Read
  By campaign. Do not call a post dead from one hidden row.
- **UTM is a floor:** clicks in a social app's browser followed by a wishlist in the Steam client
  are lost, and many viewers search Steam later on PC. The lift shows what UTM missed. It also
  includes sales, festivals and press, so read it as a rough upper view.
- **Last days are short:** Steam finalizes a wishlist about 4 days after the visit.
- **Counted twice:** daily exports and a range export for the same days add up twice. The script
  warns when one tag and day are in two files. Keep one export per day.
- **One-day exports:** an export with no date column carries the day only in its file name, such
  as `utm_2026-11-20.csv`. Keep that name, so the duplicate check works.
- **Views are not wishlists:** a format can win on views and AVD and bring no one to the store.
- **Small samples:** with fewer than 5 posts per format the report says "too early". On
  wishlists, a format wins only if its count is over the other's plus 2 x sqrt(the other's count)
  (a Poisson rule of thumb: 18 vs 12 is not a win, 18 vs 8 is). Otherwise it says "not different
  yet". Why: https://manalens.dev/blog/small-budget-game-marketing-measurement?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=marketing_retro
- **Cross-posted Shorts share a slug:** the same clip on YouTube, TikTok and Reels has three post
  IDs and needs three links. If all three use one link, the numbers land on one post and the
  report warns. The per clip table adds the three up.
- **Platform stats lag:** views keep growing for days. Compare posts of the same age.

## Version notes

- Steam UTM Analytics: columns such as "UTM Source", "UTM Campaign", "UTM Content",
  "Total Visits", "Tracked Visits", "Wishlists" and "Purchases"; conversions within 72 hours of a
  tracked visit, final after about 4 days; small combinations hidden, minimum not published.
  Valve does not document the exact header text, so the script matches columns by name, as
  Manalens does.
- Steam daily wishlist CSV: the script looks for a date column (`Date`, `DateLocal`, `Day`) and
  an adds column (`Adds`, `Wishlist Adds`). Check the header of your export.
- Manalens MCP (docs.manalens.dev/mcp/overview, checked 2026-11-26): `get_steam_utm` (`group_by`
  `source`, `medium`, `campaign`, `content`, `term` or `campaign_content`; `view` `breakdown` or
  `daily`; totals and rows of visits, wishlists, purchases and activations; data from the user's
  Steam UTM import), `get_steam_wishlists` (daily adds, deletes, purchases, gifts, net and
  outstanding change, GMT days; no total outstanding count), `get_analytics` (`top_sources` takes
  `group_by` `content` or `campaign`, and `utm_content` and `utm_term` filters) and
  `get_attribution` (`group_by` `content`). Tool names can still change: match on the tool list.
- Last verified 2026-11-26.
