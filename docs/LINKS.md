# Link and post ID convention

Every skill that writes a post also writes its link with UTM tags, so that `marketing-retro` can
tell which post brought visits and wishlists. Use the same rules everywhere.

## Post ID

`YYYY-MM-DD-<platform>-<slug>`, lowercase, hyphens only, at most 60 characters.
Example: `2026-11-26-yt-conflict-pumpkins`.

Platform codes: `yt` (YouTube Shorts), `tt` (TikTok), `ig` (Instagram Reels), `rd` (Reddit),
`x` (X), `bs` (Bluesky), `th` (Threads), `yl` (YouTube long video), `nl` (newsletter), `dc` (Discord).

A Short cross-posted to three platforms gets three post IDs with the same date and slug. For
Reddit, put the subreddit in the slug: `2026-12-01-rd-indiegames-island-hop`.

## UTM tags

| Tag | Value | Example |
|---|---|---|
| `utm_source` | platform or channel | `youtube`, `tiktok`, `instagram`, `reddit`, `x`, `bluesky`, `threads`, `newsletter`, `discord`, `presskit`, `press` |
| `utm_medium` | `social`, or `video` for long YouTube, `email` for newsletters | `social` |
| `utm_campaign` | the marketing beat, no dates | `devlog`, `demo`, `nextfest`, `launch`, `screenshotsaturday` |
| `utm_content` | the post ID | `2026-11-26-yt-conflict-pumpkins` |

Why the post ID goes in `utm_content`, not `utm_campaign`: Steam hides UTM combinations with very
few visits. With the beat in `utm_campaign`, the campaign totals still add up when single posts
are too small to show, and each post still has its own tag for when it is big enough to matter.

Keep the beat list short and stable (5 to 10 values). Do not invent a new campaign per week.

Example Steam link:

```
https://store.steampowered.com/app/<appid>/?utm_source=youtube&utm_medium=social&utm_campaign=devlog&utm_content=2026-11-26-yt-conflict-pumpkins
```

Steam counts these in Steamworks, "UTM Analytics": visits, wishlists and purchases by tag. Links
must go to the app page or a sale page. A visit gets credit for actions within 72 hours, and the
numbers are final about 4 days later. The same tags work on itch.io and your own site.

UTM numbers are a floor, not the total. Many people watch on a phone and search the game on Steam
later on a PC, which shows up as search or direct traffic. `marketing-retro` also looks at daily
wishlist lift for that reason.

## Tracker

Each post gets one row in `marketing/posts.csv` (create it if missing):

```
post_id,date,platform,format,title,url,link
```

`format` is one of `caption`, `mechanic`, `conflict`, `update`, `series`, `trailer`, `reddit`,
`social`, `other`. `url` is the post's own address, filled in by the person after they post.
`link` is the tagged link above. `marketing-retro` adds the numbers later.

## Where the link can go

| Platform | Clickable link | Do this |
|---|---|---|
| YouTube Shorts | Not in the description or comments | Put the tagged link first in the channel profile links, and set each Short's "related video" to a long video whose description has the link. Show the game name on screen so people can search it. |
| TikTok | Bio link only, and only with 1,000 followers or a business account | Game name on screen and in the caption; "search <name> on Steam". |
| Instagram Reels | Bio link | Same as TikTok. |
| Reddit | Usually the first comment; some subs ban store links | See `reddit-post`. |
| X | First reply works; in the post works too | Test both. |
| Bluesky, Threads | In the post | Link card. |

Since most short-form viewers cannot click, the tagged link on a profile carries a per-platform
post ID such as `2026-11-yt-profile`, and the game name on screen does the rest.

## Short links

Long UTM links look spammy. Use a redirect on your own site (for example `yourgame.com/s/pumpkins`)
that forwards to the tagged link, and keep the mapping in `marketing/posts.csv`.
