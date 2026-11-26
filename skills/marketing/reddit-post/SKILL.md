---
name: reddit-post
description: >
  Plans and drafts Reddit posts for an indie game: picks subreddits for players and for
  developers, writes a title and first comment per subreddit, picks the clip shape (16:9, 4:5 or
  GIF), spaces posts so no subreddit sees the game too often, and writes a 14-day calendar and a
  tracker that logs each post's results and ranks subreddits by what worked. Use for "post my game on Reddit", "which subreddits for my indie game", "Reddit
  calendar", "Screenshot Saturday post", "write a Reddit title for my gameplay GIF". Drafts only;
  never posts. Not for Shorts or TikTok scripts (`shorts-script`) or cutting the clip (`clip-cut`).
---

# Reddit post

Reddit can send a new game thousands of players in a day, or ban the account in an hour. The
difference is fit and spacing: the right clip in the right subreddit, a title that sounds like a
person, the developer saying who they are, and no subreddit seeing the game too often.
Results are uneven: a post that dies in one subreddit can take off in another, or on another day.
So plan many small shots, not one big one.

Writes `marketing/reddit/calendar.md` and `marketing/reddit/tracker.csv`, appends each planned
post to `marketing/posts.csv`, and each week writes `marketing/reddit/scoreboard.md` from the
results.

The subreddit list with each sub's rules (allowed weekdays, gap between posts, flair, link
policy, weekly threads, source and confidence) is
[references/subreddits.csv](references/subreddits.csv). The scripts read it.

## Inputs

1. **The game in one line, its genre and its look** (cozy, horror, roguelike, pixel art, low
   poly, web game). Genre and look decide most subreddits.
2. **Media:** clip and GIF paths, or ask the user to make them with `clip-cut`. Reddit autoplays
   muted, so each clip must start mid-action.
3. **Link target:** Steam page, demo, itch.io or a browser build.
4. **History:** the user's last post per subreddit. Read `marketing/reddit/tracker.csv` if it
   exists; otherwise ask the user to check their Reddit profile.
5. **The account:** its age and karma in the subs you plan to use. Moderators check whether you
   are a redditor with a game or a game that posts to Reddit. A rule of thumb from Reddit's own
   guidance: at most about 1 in 10 of your posts and comments should be about your game.
6. **Time budget:** how many posts a week the user can stay online for. Plan at least 2 hours of
   replies per post, and up to 6 hours if one takes off.
7. **`marketing/rules.md`:** the do-not-say list.

## With the Manalens MCP

It is connected when your tool list has `build_steam_utm_link` and `check_utm_url`. Any Manalens
API key or OAuth connection can call them.

- **Steam links:** call `build_steam_utm_link` with
  `{"app": "<App ID>", "utm_source": "reddit", "utm_medium": "social", "utm_campaign": "demo", "utm_content": "<post ID>"}`.
  Write the returned `url` where Workflow step 3 puts the tagged link.
- **Other links** (itch.io, your site): call `check_utm_url` with `{"url": "..."}`. Fix each
  `warning` in `issues`, and use `clean_url` when it is given.

## Without it

Write each link by hand from [docs/LINKS.md](../../../docs/LINKS.md), then run the check script
(Workflow step 6). To build tagged Steam links in the browser, use the
[Steam UTM link builder](https://manalens.dev/tools/steam-utm-builder?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=reddit_post).
To build the links from this skill next time, connect Manalens (14-day trial):
https://docs.manalens.dev/mcp/overview

## Workflow

1. **Shortlist subreddits** from [references/subreddits.csv](references/subreddits.csv): player
   subs that match the genre and look, developer subs for "how I made it" posts, and weekly
   threads. Niche genre and engine subs often bring more wishlists per click than the big ones.
   Aim for 8 to 15. Skip rows with `promo_allowed` = `no` (use their weekly thread in slot C).
   Rules change and Reddit cannot be read by the agent, so for every sub with `confidence` below
   `high`, ask the user to open the sidebar and confirm: self-promotion allowed? which days?
   flair? links? how often? Update the CSV row with what they find and today's date. Background:
   [Reddit posts and ads for indie games](https://manalens.dev/blog/reddit-ads-and-posts-for-indie-games?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=reddit_post).
2. **Write one post per subreddit.** Rules:
   - Title in the first person, the way a person talks: "I made...", "I spent a year on...",
     "How the sailing feels in my game after a month of tuning". Personal stakes beat feature
     lists. No clickbait, no "please upvote", no all caps.
   - Say you are the developer, in the title or the first comment.
   - Write a different post for each community. Developers want how you built it; players want
     to see the game. The same text pasted into several subs is what Reddit treats as spam.
   - Upload the clip natively (video or GIF, about 30 seconds or less), not a YouTube link.
   - Player subs: lead with the clip. By default the store link goes in your first comment, or
     only in a reply when someone asks. Some subs (r/indiegames among them) remove store links in
     the post; follow the `link_policy` column.
   - Developer subs: the clip plus one thing you learned or how you built it. No store link in
     the post unless the sub allows it; offer it in a reply when asked.
   - Feedback subs: ask a real question you will act on. Never dress promotion up as feedback.
   - One first comment per post: who you are, what the game is, the link, credits (music).
   - Shape: 4:5 fills the phone feed; 16:9 for desktop-heavy and tech subs; GIF where video is
     not allowed or for comment replies. Use `clip-cut` to make them.
3. **Tag each link** (docs/LINKS.md): `utm_source=reddit`, `utm_campaign=<beat>`, and the post ID
   in `utm_content`, with the subreddit in the slug (`2026-12-01-rd-indiegames-island-hop`).
4. **Build the calendar.** One new post a day by default, two at most, and never several subs
   within a few hours (one developer tripped the spam filter by posting in several subs inside
   8 hours; spread a launch over about 3 days). The slot times are defaults, not findings; no
   published data shows a best hour:
   - Slot A, players, about 10:00 US Eastern on a weekday.
   - Slot B, developers, about 14:00, on a different day from a big slot A post.
   - Slot C, comments only: 2 or 3 helpful answers or a comment in a weekly thread. This keeps
     the account from looking like it only promotes. In "suggest a game" threads, suggest other
     games first; mention yours only if it fits, with "I'm the dev".
   Spacing rules (the scripts read them from `subreddits.csv`):
   - Each sub's `gap_days`, or 14 days when the sub has no known rule. Once a month is a safe
     maximum for most small subs.
   - Each sub's `allowed_days`: r/CozyGamers developer posts only on Wednesdays (UTC), r/Games
     only on Indie Sunday, r/playmygame paid games only on Tuesdays, and so on.
   - Never the same clip in two subreddits on the same day.
   - A different clip and title from the day before.
   - Save one post in the strictest subs (often "once a month") for a big moment: store page
     live, demo out, launch day.
5. **Write the tracker** (`marketing/reddit/tracker.csv`), one row per planned post:
   `date,slot,subreddit,post_id,clip,title,flair,status,url,upvotes,comments,views,visits,wishlists,notes`.
   `status` is `planned`; the user changes it to `posted`, `removed` or `skipped` and pastes the
   `url`. A day or two after each post, fill in upvotes, comments and views from Reddit, and
   visits and wishlists from the Steam UTM report or `marketing-retro`.
6. **Run the check:**

   ```bash
   python3 <skill>/scripts/check_calendar.py marketing/reddit/tracker.csv
   ```

   It fails on a post inside a sub's gap, on a weekday the sub does not allow, in a sub that bans
   promotion, a clip used twice on one day, more than two posts a day, or a missing post ID.
   Fix and re-run.
7. **Follow the results** each week, or before planning the next calendar:

   ```bash
   python3 <skill>/scripts/subreddit_report.py marketing/reddit/tracker.csv --out marketing/reddit/scoreboard.md
   ```

   It ranks subreddits by wishlists, visits and upvotes, lists removals, shows the next allowed
   post date for every sub, and lists subs not tried yet. Plan the next calendar from it: more
   posts where visits and wishlists came, fix or drop subs with removals or nothing after 2 or 3
   posts. Judge a sub on wishlists, not upvotes: viral posts often bring few.
8. **Hand off.** The user posts by hand, at the slot time, from their own account, and stays to
   answer comments. Remind them: no second accounts, no asking friends to upvote.

## Output

`marketing/reddit/calendar.md` (a 14-day table: day, slot A, slot B, slot C), the tracker CSV,
and per post a block:

```markdown
### Tue 1 Dec, slot A: r/indiegames (flair: Promotion)
- Post ID: 2026-12-01-rd-indiegames-island-hop (utm_campaign=demo)
- Clip: clips/island-hop-1080x1350.mp4 (4:5, 14 s, uploaded natively)
- Title: I'm making a cozy game where a cat delivers the mail by boat
- First comment: Hi, I'm the solo dev. Ask me anything about the boat. Music: <credit>.
- Link: none in the post (sub rule); reply with the tagged link if someone asks.
```

## Measure

Record upvotes, comments and views per post in the tracker, plus visits and wishlists from the
tagged links (`utm_source=reddit`, post ID in `utm_content`). `subreddit_report.py` turns them into
a per-subreddit scoreboard; `marketing-retro` puts Reddit next to the other channels. Some developers report Reddit posts that went viral but moved few
wishlists, and others report thousands from one post. Measure your own before you spend more
time there.

## Gotchas

- **Removed by automod, no message:** check the post in a private window. If it is gone, message
  the moderators politely and ask what to change. Do not repost the same post elsewhere at once.
- **Account too new or low karma:** many subs filter new accounts, and moderators look at your
  karma in their sub. Spend a week or more commenting helpfully first.
- **Rate limited:** if Reddit says you are posting too much, stop for the day.
- **Big subs are a lottery:** a post in r/gaming can reach tens of thousands and still be
  removed hours later, or bring a handful of wishlists. Save it for your single best clip.
- **Shadow limits on self-promoters:** an account whose history is mostly its own game gets
  filtered site-wide. Keep slot C.
- **Same post, many subs, one hour:** reads as spam to Reddit's filter. Use the calendar.
- **Arguing in comments:** thank critics and move on. A defensive reply costs more than the post
  earns.
- **Promotion dressed as a question:** "What do you think of my game?" with a store link breaks
  the rules of most feedback subs.
- **Video without sound:** the first second decides it. No logo, no fade in.

## Version notes

Subreddit rules, flairs and weekly threads change often. `references/subreddits.csv` was built
from public guides and rule trackers (Reddit itself could not be read), with a source, date and
confidence on each row. It is a starting point, not a source of truth: confirm on the sidebar
and update the row.

Last verified 2026-11-26.
