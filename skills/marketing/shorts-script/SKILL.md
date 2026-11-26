---
name: shorts-script
description: >
  Writes YouTube Shorts, TikTok and Instagram Reels scripts for an indie game: the hook for the
  first 3 seconds, the beats, on-screen text, title, description, pinned comment with a tagged
  link, and a weekly plan across the Caption, Mechanic and Conflict formats. Use for "write a Short
  for my game", "TikTok ideas for my indie game", "hooks for my gameplay clip", "devlog Short
  script" or "what should I post this week". Not for finding stories in the git log
  (`devlog-from-git`), cutting the video file (`clip-cut`) or Reddit posts (`reddit-post`).
---

# Shorts script

Turn a game and some footage into short vertical video scripts that a stranger watches past the
first 3 seconds. Writes `marketing/shorts/<post-id>.md` per Short and appends to
`marketing/posts.csv`.

Short-form video is the cheapest channel a new indie game has. A channel with no subscribers can
still reach a large audience, because the feed tests every video on strangers first. What decides
it is the first 1.5 to 3 seconds. Views are not wishlists, though. Links in Shorts descriptions and
comments are not clickable, and TikTok and Reels allow only a bio link, so most viewers who want
the game search its name on Steam later. So the game, the hook and the name on screen all matter. Volume matters too: post often, reuse footage, and expect most posts to do little.

## Inputs

Find these in the repo first (README, store page text, `marketing/`, press kit). Ask only for
what is missing.

1. **The game in one line:** "You are a <who>. You <verb> <what>." The loop or the fantasy.
2. **What makes it different:** 1 to 3 things a stranger gets in 3 seconds (a mechanic, an art
   style, an odd premise).
3. **Footage:** clip paths, or a list of moments the user can record. Ask what is in the current
   build or demo. Our practice: 10 to 20 clips of 5 to 20 seconds each (a big hit, a strange
   mechanic, a close escape, a funny failure), with one line per clip on what happens and how
   long it is. Rank them by how fast a stranger gets them with sound off; post the top three
   first and keep the rest for the next two weeks.
4. **The link target:** Steam app page, demo, itch.io page or site. Before a store page exists,
   point to the demo.
5. **Do-not-say list:** dates, prices, spoilers, names, features that changed. Ask the user once
   and save it to `marketing/rules.md` if the file is missing, one item per line as
   ``- `word or phrase` `` (the check script reads that shape), with the reason after it.

## The three formats

| Format | What it is | Effort | When it works |
|---|---|---|---|
| **Caption** | Real footage plus one caption that states the loop or the fantasy ("You are a cat. You have a boat. Deliver the mail."). | About 1 hour | Trailer cuts and montages. The floor of the weekly mix. |
| **Mechanic** | The mechanic is the hook. It is on screen and working in the first 3 seconds, with no title card before it. | About 2 hours | Anything satisfying or unusual to watch: a puzzle, a physics moment, a before and after. |
| **Conflict** | "In my game about <loop>, <problem>." Then show the problem, then the fix, or ask the viewer to choose. | About 3 hours | Bugs, design problems and cut ideas. The strongest format for solo devs, because it is a story with a person behind it. Use `devlog-from-git` to find true ones. |

Series formats sit on top: a numbered "Update #N" (one visible change a day), a recurring bit
("funny bug reports pt N", "why did I add X?"), or a fixed premise repeated with new content.
A viewer who likes one finds the next.

Read [references/hooks.md](references/hooks.md) for hook templates by format.

## AI help and AI labels

AI may write the words: hooks, captions, titles, scripts, and cut lists. The footage stays real
gameplay from the build. Each platform's rule, read 2026-11-26 (sources in
[references/sources.md](references/sources.md)):

| Content | YouTube | TikTok | Instagram Reels (Meta) |
|---|---|---|---|
| Real gameplay footage | No label ("gameplay footage from video games") | No label unless AI altered it | No label if footage and audio are real |
| AI help with script, title, thumbnail, caption | No label | No label for text | No label for text |
| Realistic AI scene, image, or video | Label required | Label required | Label required (photorealistic video) |
| Realistic AI voice or audio | Label for a generated voice of a real person saying what they did not say, and for AI music that is the main focus | Label required | Label required (realistic-sounding audio) |
| Non-realistic AI animation | No label | Label encouraged | Not named in the policy |

- **Where:** YouTube, under AI use in the Attributes section at upload. TikTok, the
  AI-generated content setting under More options before posting. Instagram, Meta's
  AI-disclosure tool.
- **Reach:** YouTube says a disclosure alone does not limit audience or earnings. TikTok says
  the setting does not affect distribution for posts that follow its Community Guidelines.
- **Skipping it:** Meta may apply penalties. YouTube may add a label, remove content, or suspend
  the channel from the Partner Program for creators who keep skipping. TikTok labels its own AI
  effects and C2PA-tagged files itself, and an automatic label cannot be removed.
- A voice clone of the developer for dubs needs no YouTube label; a generated voice of someone
  else saying things they did not say does.

## With the Manalens MCP

It is connected when your tool list has `campaign_link`. Any Manalens
API key or OAuth connection can call them.

- **Steam links:** call `campaign_link` with
  `{"app": "<App ID>", "utm_source": "youtube", "utm_medium": "social", "utm_campaign": "devlog", "utm_content": "<post ID>"}`.
  Write the returned `url` in the `link` column of `marketing/posts.csv`.
- **Other links** (itch.io, your site): call `campaign_link` with `{"url": "..."}`. Fix each
  `warning` in `issues`, and use `clean_url` when it is given.

## Without it

Write each link by hand from [docs/LINKS.md](../../../docs/LINKS.md), then run the check script
(Workflow step 9). To build tagged Steam links in the browser, use the
[Steam UTM link builder](https://manalens.dev/tools/steam-utm-builder?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=shorts_script).
To build the links from this skill next time, connect Manalens (14-day trial):
https://docs.manalens.dev/mcp/overview

## Workflow

1. **Collect inputs** (above). Write the one-line pitch and the 1 to 3 differences at the top of
   `marketing/shorts/README.md` if it does not exist.
2. **Pick the format and the moment.** One idea per Short. The best moment goes first: no logo,
   no intro, no slow pan.
3. **Write 5 hooks** for the idea, using different templates from `references/hooks.md`. Score
   each 1 to 5 on: true in the build, clear with sound off, opens a question, says it is a game.
   Keep the best. If no hook scores 4 or more, drop the idea. A weak hook means no video.
4. **Write the script** as a beat table (see Output). Rules:
   - 0 to 3 s: the hook line on screen, and the thing it talks about already visible.
   - Say "my game" early in the first line, for Caption and Conflict. Viewers who do not want a
     game leave at once, which costs less than a swipe halfway through.
   - Open a loop in the hook and close it in the last line, not the second. Do not answer your
     own question early.
   - One short line of on-screen text per beat, about 6 words at a time. Assume sound is off;
     captions carry the story.
   - Keep music and game sound. Use the game's own soundtrack where you can (see Gotchas). A
     voiceover is optional and must be the developer's own voice.
   - Length 10 to 60 seconds; 15 to 30 is the usual sweet spot. A longer "how this mechanic
     works" explainer (about 1 minute) has worked for some games on TikTok: test it against short
     clips rather than ruling it out.
   - End on a frame that loops back to the start when possible.
   - End with the game name on screen for the last 1 to 2 seconds, and "Wishlist on Steam" or
     "search <name> on Steam". Most wishlists from short video come from people who search later.
   - Our practice: test two hooks on the same clip on different days, each with its own post
     ID, and keep the winner. Never use a hook the clip does not prove.
   - A spoken or on-screen call to action in the middle of the clip is a test, not a rule. Some
     makers found clips without one held viewers longer; others credit a clear ending CTA for
     their wishlists. Alternate and compare in `marketing-retro`.
5. **Write the post text:** title under 70 characters (often the hook itself), description (one
   sentence with the game's name, 3 to 5 hashtags such as `#indiegame #gamedev` plus genre tags),
   and a pinned comment that names the game and where to find it. Make one post ID per platform
   with [docs/LINKS.md](../../../docs/LINKS.md). Links are not clickable in Shorts descriptions
   or comments, so also:
   - **YouTube:** set the Short's "related video" to a long video (a trailer or devlog) whose
     description has the tagged link at the top, and keep the tagged link first in the channel's
     profile links. Our practice: cut 3 to 5 Shorts from each devlog, each pointing to it.
   - **TikTok and Reels:** the bio link is the only link. TikTok bio links need 1,000 followers or
     a business account. Put the game name in the caption, so people can search for it on a PC.
   See [TikTok vs Shorts vs Reels for games](https://manalens.dev/blog/tiktok-vs-youtube-shorts-vs-reels-for-games?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=shorts_script)
   for how each platform handles links.
6. **Check against `marketing/rules.md`:** no banned words, no spoilers, nothing that is not in
   the build the viewer can play.
7. **Plan the week** when asked: a default mix is 7 a week, 2 Conflict, 2 Mechanic, 2 Caption,
   1 series. Fewer is fine: 2 a week, kept up, beats 7 a week for one week. Cross-post each Short
   the same day to YouTube Shorts, TikTok and Reels (same file, no watermark).
8. **TikTok specifics** (see [references/tiktok.md](references/tiktok.md)): warm the account up,
   post from the phone, use original or allowed sounds, re-cut rather than repost, and turn on the
   "Your brand" disclosure.
9. **Run the check:** `python3 scripts/check_short.py marketing/shorts/<post-id>.md` from this
   skill's folder (or the repo copy). It fails on a hook over 12 words, a missing link, a missing
   post ID or a script over 60 seconds.
10. **Hand off.** Tell the user which footage to cut (or run `clip-cut`), and to post it
   themselves, with the AI label on when the table above says so. Never upload. The user
   replies to comments; AI may group a week of comments into questions, bug reports, and
   requests, and the common questions become the next Short. In GDC's November 2026 survey,
   QA and community support staff were the most negative about generative AI (76%).

## Output

`marketing/shorts/<post-id>.md`:

```markdown
# <title>

- Post IDs: 2026-11-26-yt-conflict-pumpkins, 2026-11-26-tt-conflict-pumpkins, 2026-11-26-ig-conflict-pumpkins
- Format: conflict
- Length: 24 s
- Footage: clips/pumpkin-bug.mp4 (0:03 to 0:11), clips/pumpkin-fixed.mp4

## Hook (0 to 3 s)
In my farming game, the pumpkins started eating the farmer.

## Beats
| Time | On screen | Text |
|---|---|---|
| 0-3 s | Pumpkin swallows the farmer | In my farming game, the pumpkins started eating the farmer. |
| 3-12 s | Three more times, from different angles | It only happened at night. |
| 12-20 s | The collision box drawn in red, too big | The pumpkin's hitbox was the size of a house. |
| 20-24 s | Farmer walks past a normal pumpkin | Now they only eat seeds. |

## Post text
- Title: the pumpkins in my game started eating the farmer
- Description: A bug in my cozy farming game, Pumpkin Patch. #indiegame #gamedev #cozygames
- Pinned comment: The game is Pumpkin Patch. Search it on Steam, or see the related video.
- Related video: the trailer (its description has the tagged link)
- End card (last 2 s): PUMPKIN PATCH, Wishlist on Steam
- Profile link: tagged link with utm_content=2026-11-yt-profile (see docs/LINKS.md)
```

## Measure

Each post ID is the `utm_content` of its link (docs/LINKS.md). Because most viewers cannot click,
UTM rows catch only part of the effect: also watch daily wishlists and Steam search traffic on
the days after a post spikes. A week later, run `marketing-retro` to compare formats by average
view duration and by visits and wishlists per 1,000 views. Expect a wide range: reported cases
run from under 1 to about 18 wishlists per 1,000 views. After 5 or more posts per format, keep
the best two formats. A clip that holds viewers but does not spread is worth one faster re-cut
before you drop it. On Reels, also read sends per reach (shares divided by reach): Instagram's
head Adam Mosseri named it one of the most important numbers in June 2024, above likes and
watch time. Boost (Spark Ads or Meta ads) only a post that already did well on its own, with its
own tagged link (our practice). Method: [from TikTok views to Steam wishlists](https://manalens.dev/blog/tiktok-short-form-video-to-steam-wishlists?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=shorts_script).

## Gotchas

- **Hook is true today, false tomorrow:** games change daily. Check each claim in the current
  build before posting, and never promise a feature that is not in what the viewer can play.
  Valve's Content Survey says you promise Steam that the game matches your marketing.
- **Title card first:** a logo or a title before the action loses most viewers. Put the game name
  in the description, not in the first seconds.
- **Text under the platform UI:** the bottom 20% and the right edge are covered by buttons and
  captions on all three apps. Keep text in the upper middle.
- **Same clip, different hooks:** reusing footage is fine. Posting the identical file twice on the
  same platform is not; change the hook or the cut.
- **New TikTok account gets zero views:** a fresh account that posts at once can be treated as a
  bot. Ask the user to use it normally for about a week first, and post from the phone.
- **Links in Shorts do nothing:** description and comment URLs are not clickable on YouTube
  Shorts. Use the related video and the channel profile link, and show the game name on screen.
- **Music claims:** a Short over 60 seconds with any active copyright claim is blocked worldwide.
  TikTok business accounts can only use the Commercial Music Library. The game's own soundtrack
  avoids both problems.
- **AI voiceover or AI footage without the label:** a realistic AI narrator over real gameplay
  still needs the label on TikTok and Reels. Record the developer's voice or use on-screen text.
- **Reposted clips on Reels:** Mosseri said Instagram wants more value to go to original
  creators than to accounts that repost. Post your own captured footage.
- **Reposting the same clip:** TikTok's guidelines (Sep 2026) keep reused material without
  anything new out of the For You feed. Re-cut: new hook, new order, new length.

## Version notes

- Hook window, format effort and the 7-a-week mix come from creators' own reports (see
  [references/sources.md](references/sources.md)). Treat them as methods to test, not laws.
- YouTube Shorts allow up to 3 minutes (since Oct 2024); Shorts links are not clickable (since
  Aug 2023, YouTube Help).
- TikTok bio links need 1,000 followers or a business account; business accounts get only the
  Commercial Music Library (TikTok help, as of Nov 2026).
- AI label rules: YouTube Help, Disclosing use of GenAI content; TikTok Support, AI-generated
  content; Meta Misinformation policy (7 April 2025). All read 2026-11-26.
- A Short can be square or vertical, up to 3 minutes; up to 15 can be uploaded at once from a
  computer (YouTube Help, read 2026-11-26).

Last verified 2026-11-26.
