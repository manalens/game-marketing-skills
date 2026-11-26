---
name: social-post
description: >
  Writes X (Twitter), Bluesky and Threads posts for an indie game: a GIF or short clip with one
  line of text, alt text, a reply with the tagged link, and a weekly plan around game dev hashtag
  days such as #ScreenshotSaturday. Adapts one idea per platform (length limits, link handling,
  hashtags). Use for "tweet about my game", "Bluesky post for my devlog", "what to post for
  Screenshot Saturday", "social media plan for my indie game". Drafts only; never posts. Not for
  vertical video scripts for Shorts, TikTok or Reels (`shorts-script`) or Reddit (`reddit-post`).
---

# Social post

X, Bluesky and Threads reward a moving picture and one line. A GIF of the game doing something
odd or satisfying, with a sentence that says what it is, beats a feature list or a press-release
tone. These feeds move fast, so volume matters: post often, reuse clips, and expect most posts to
do little and a few to do a lot.

Writes `marketing/social/<YYYY-MM-DD>.md` (the week's posts) and appends to `marketing/posts.csv`.

## Inputs

1. **The game in one line** and what makes it different (see `shorts-script`; reuse its notes).
2. **Media:** GIFs and short clips. Make them with `clip-cut` (16:9 or 4:5 for these feeds; a GIF
   for the reply chain).
3. **Accounts:** which platforms the user is on, and the handles.
4. **Link target:** Steam page, demo or site.
5. **`marketing/rules.md`:** the do-not-say list.

## With the Manalens MCP

It is connected when your tool list has `campaign_link`. Any Manalens
API key or OAuth connection can call them.

- **Steam links:** call `campaign_link` with
  `{"app": "<App ID>", "utm_source": "bluesky", "utm_medium": "social", "utm_campaign": "screenshot_saturday", "utm_content": "<post ID>"}`.
  Write the returned `url` in the post and in the `link` column of `marketing/posts.csv`.
- **Other links** (itch.io, your site): call `campaign_link` with `{"url": "..."}`. Fix each
  `warning` in `issues`, and use `clean_url` when it is given.

## Without it

Write each link by hand from [docs/LINKS.md](../../../docs/LINKS.md), then run the check script
(Workflow step 6). To build tagged Steam links in the browser, use the
[Steam UTM link builder](https://manalens.dev/tools/steam-utm-builder?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=social_post).
To build the links from this skill next time, connect Manalens (14-day trial):
https://docs.manalens.dev/mcp/overview

## Workflow

1. **Pick the week's ideas.** One idea per post: a mechanic, a before and after, a bug, a piece of
   art, a question. Pull from `devlog-from-git` and from clips already made for Shorts.
2. **Write the post** for each platform. Shared rules:
   - First line: what is happening in the clip, said like a person. "My cat delivers the mail by
     boat. Today she learned to steer by the wind." Not "Introducing our new wind system!"
   - Say it is your game, and its name, in the text. People often look it up later on a PC.
   - Media in the first post, always. Attach the file natively; do not post a YouTube link.
   - Alt text on every image and GIF: one sentence describing what moves on screen.
   - **Link placement on X is a test.** X says links are not deboosted, but link posts still
     tend to get fewer reactions, and many devs put the link in the first reply. Alternate and
     compare wishlists in `marketing-retro`. On Bluesky and Threads, a link in the post is fine.
   - 1 or 2 hashtags at most. On X they no longer help reach, but day tags such as
     #ScreenshotSaturday still gather devs who reply. On Bluesky, put keywords like "gamedev",
     "indiedev" and your engine in the text and the alt text: custom feeds read both.
   - What travels on X: a feeling (funny, creepy, cute, satisfying) and clips of about a minute
     cut from the trailer, strongest moment first. Post clips of trailers, not whole trailers.
   - End with nothing, or a real question. No "please RT".
3. **Fit each platform's limits** (characters, media, link handling) from `references/platforms.md`.
   Write one version per platform; do not cross-post identical text with `@` handles that only
   exist on one network.
4. **Plan the week** around the hashtag days in [references/platforms.md](references/platforms.md)
   (for example a GIF on Saturday). A sustainable default: one post a day on your main platform,
   cross-posted to the others the same day. Bluesky feeds are chronological, so repost your best
   post a few hours later and again on another day. Pin the best post of the month.
5. **Tag links:** each platform gets its own post ID (`x`, `bs`, `th` codes in
   [docs/LINKS.md](../../../docs/LINKS.md)) and `utm_source` (`x`, `bluesky`, `threads`).
6. **Check:**

   ```bash
   python3 <skill>/scripts/check_social.py marketing/social/<date>.md
   ```

   It fails on a post over the platform limit, a missing alt text, a missing post ID, or more
   than 2 hashtags. It notes X posts with the link in the main post (fine for the link test).
7. **Hand off.** The user posts by hand or with a scheduler, and replies in the first hour. For
   tools and timing, see [scheduling social posts for games](https://manalens.dev/blog/schedule-social-posts-for-games?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=social_post).

## Output

`marketing/social/<YYYY-MM-DD>.md`, one block per post:

```markdown
## Sat 28 Nov: wind steering (GIF)

### x
- Post ID: 2026-11-28-x-wind-steering
- Media: clips/wind-steering.gif
- Alt: A small boat turns as its sail fills with wind at sunset.
- Text: My cat steers her mail boat by the wind now. Took three tries to make it feel right. #ScreenshotSaturday
- Reply: Wishlist it here: <tagged link>

### bluesky
- Post ID: 2026-11-28-bs-wind-steering
- Media: clips/wind-steering.gif
- Alt: A small boat turns as its sail fills with wind at sunset.
- Text: My cat steers her mail boat by the wind now. Took three tries to make it feel right. <tagged link> #ScreenshotSaturday
```

## Measure

Each post ID is the `utm_content` of its link (docs/LINKS.md). `marketing-retro` compares
platforms and post types by visits and wishlists. Expect small numbers: in one informal survey X
sent well under 2% of a game's traffic, and a reported median was about 7 wishlists per 1,000
video views on X (one creator's posts). Judge over 4 weeks, by wishlists, not likes. More:
[social posts that bring wishlists](https://manalens.dev/blog/social-posts-that-bring-wishlists?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=social_post).

## Gotchas

- **Untested link placement on X:** do not assume either way. Run a few weeks with the link in
  the reply and a few with it in the post, then compare wishlists, not likes.
- **GIF on Bluesky:** some reports say an uploaded .gif shows only its first frame. Upload an MP4
  loop instead (`clip-cut --shape 16x9` or `4x5`). MP4 also looks better on X.
- **Same text everywhere:** each network has its own tone. Bluesky and Threads read as more casual
  and conversational than X.
- **Posting at 3 a.m. for the audience:** post when you can reply in the first hour; replies
  matter more than the minute you post.
- **Only promotion:** reply to other devs, share their work, join the hashtag threads. An account
  that only posts its own game grows slowly everywhere.

## Version notes

Character limits, media limits and how each feed treats links change often. Keep the numbers in
`references/platforms.md`, with a date on each.

Last verified 2026-11-26.
