---
name: marketing-retro
description: >
  Weekly marketing retro for an indie game: joins your posts in marketing/posts.csv with platform
  stats, Steam UTM Analytics, web analytics and Steam daily wishlists on post ID = utm_content,
  then writes a report of views, average view duration, store visits and wishlists per post, per
  campaign and per format, the wishlist lift on post days, which formats to keep or drop, links to
  fix and next week's mix. Use for "which of my Shorts drove wishlists", "weekly marketing retro",
  "compare my TikTok formats", "Steam UTM report", "what should I post more of" or "did my Reddit
  post bring visits". Works with any CSV; Manalens is the documented default for website numbers.
  Not for writing posts (`shorts-script`, `reddit-post`).
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
| `utm_medium` | `social`, `video` or `email` | `social` |
| `utm_campaign` | the marketing beat | `devlog`, `demo`, `launch`, `nextfest`, `screenshotsaturday` |
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
   Any tool works. Manalens can fill it (step 2).

## Workflow

1. **Find the tracker.** Read `marketing/posts.csv`. Count the posts in the range per format and
   per beat. Output: a one-line summary, such as "14 posts: 5 conflict, 5 mechanic, 4 caption".

2. **Website numbers through Manalens, if it is connected.** Check that the MCP tools
   `get_analytics` or `get_attribution` are listed. If not, skip to step 3. They need the scopes
   `analytics:read` and `attribution:read`. Dates are `YYYY-MM-DD`.

   `get_analytics` has a named `utm_campaign` filter but no named `utm_content` filter. Filter by
   post ID with an operator filter (`utm_content` is an allowed field). One `kpis` call per post
   returns one row with `visitors`:

   ```json
   {"report": "kpis", "date_from": "2026-11-19", "date_to": "2026-11-26",
    "filters": [{"field": "utm_content", "op": "eq", "value": "2026-11-20-yt-band-runs"}]}
   ```

   Visitors per beat: the same call with `"utm_campaign": "devlog"` instead of `filters`.

   Conversions for all posts in one call. `get_attribution` groups by `content`, which is
   `utm_content`:

   ```json
   {"conversion_event": "wishlist_clicked", "model": "last_non_direct",
    "group_by": "content", "date_from": "2026-11-19", "date_to": "2026-11-26"}
   ```

   `get_analytics` cannot group by `utm_content` (`top_sources` groups by source). Write the
   results to `marketing/retro/web-YYYY-MM-DD.csv` as `utm_content,visits,signups`. Manalens MCP
   does not return Steam UTM rows, so Steam numbers come from step 3.

3. **Ask for the exports the agent cannot read.** Ask the user to:
   - Export Steam UTM Analytics: Steamworks, the game, **Marketing & Visibility**,
     **UTM Analytics**, choose the dates, do not filter by UTM values, download the CSV. They need
     the **View Marketing Traffic Data** permission. Walkthrough:
     https://manalens.dev/blog/steamworks-utm-report
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
  yet". Why: https://manalens.dev/blog/small-budget-game-marketing-measurement
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
- Manalens MCP: `get_analytics` (reports `kpis`, `event_timeseries`, `top_pages`, `top_sources`,
  `top_events`; named filters `utm_source`, `utm_medium`, `utm_campaign`; `utm_content` through
  `filters`) and `get_attribution` (`group_by` `campaign` or `content`). Indie has 60 requests
  per minute per key. The Steam CSV import in the Manalens dashboard is "coming soon".
- Last verified 2026-11-26.
