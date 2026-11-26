# Finding the right people

Contents:

1. Start from similar games
2. Press: writers, not inboxes
3. YouTube creators
4. Twitch streamers
5. Steam curators
6. Aggregator accounts
7. What to write in the tracker
8. Who to drop

## 1. Start from similar games

Pick 5 to 10 games a player of yours also plays: same genre, similar size, released in the last
few years. Steam's "More like this" on your own page and on the closest hit are good places to
look. Every search below starts from this list. A person who covered two or more of them is a
strong lead; one who covered none is a cold contact, however big.

The [Manalens Steam marketing snapshot](https://manalens.dev/tools/steam-marketing-snapshot?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=press_outreach)
does the YouTube part for you: it takes the similar games from Steam and lists the creators who
posted videos about them.

## 2. Press: writers, not inboxes

- Search `"<similar game>" review`, `"<similar game>" preview` and the outlet names you know.
  Note the byline, not just the site.
- Find the writer's own published contact: the outlet's staff or contact page, their personal
  site, or the email in their social bio. A `tips@` inbox is the last resort.
- Small and niche sites, newsletters and podcasts in your genre often answer more than large
  sites. Add them.
- Note in `similar_games` which of your games they covered, with the article link. You will use
  it in the first line of the email.

## 3. YouTube creators

- Search YouTube by hand for each similar game with words like `gameplay`, `first look`, `demo`,
  `let's play`. Sort or filter by upload date to find people active now. Do not scrape YouTube;
  its terms forbid it.
- Open each channel. Keep it when it uploads regularly, plays games like yours, and its recent
  videos have real views and comments.
- Small and mid creators who play the genre are the main list. They answer more often, and their
  viewers came for that genre. Rank by how many games like yours a channel covered recently, not
  by subscribers. Gamesight's Adam Lieb told Game Developer (30 Aug 2021) that a generic email to
  the top 50 streamers is unlikely to work, and that the share of a creator's audience that
  watches games like yours matters most. Hydroneer's developer sent about 30 emails; two
  creators with about 1.5 to 2 million subscribers each picked it up, and wishlists went from
  about 1,000 to about 60,000 by release (GameDiscoverCo, 27 Jun 2022). One mid-size creator can be the first domino: in one case a single
  video pulled other creators in (HTMAG, Aug 2025).
- Take the email from the channel's About page ("View email address"). That is the business
  email. YouTube shows it only if the channel owner added one (YouTube Help, Business Inquiry
  Emails). Write in `contact_source` where you found it.

### Using AI on the list

An AI tool can suggest search terms and comparable games, and sort the list you built: group by
genre, size and platform from your own notes, and rank by recent coverage of similar games. It
cannot find the people or their emails. Language models produce "plausible but false
statements" (OpenAI, 5 Sep 2025), and a channel name or email address that looks right may not
exist. Open every channel yourself, and copy every email from the channel or outlet page
(Manalens practice).

## 4. Twitch streamers

- On SullyGnome (sullygnome.com), open the page of each similar game. It lists the channels that
  streamed it, with hours streamed and average viewers. Pick channels that streamed the game for
  several hours, not one test stream.
- Many streamers have no public email. Look in the channel's About panels. If there is none,
  send a Whisper from your own Twitch account, and log the channel URL as `contact`.
- Record average viewers as `audience`, not followers.

## 5. Steam curators

- Use Curator Connect in Steamworks. It sends a copy through Steam to a curator, with no key to
  leak or resell. Up to 100 curators, at most 5 copies each (Valve).
- Pick curators by tags and language fit, not follower count alone (Valve says the same).
- Curator emails asking for keys are a known scam. See the Gotchas in SKILL.md.

## 6. Aggregator accounts

Accounts that repost indie games on X and Bluesky (for example IndieGameJoe, Indie Games Hub) can
bring real wishlists. They want one polished, clear clip, about a minute, that makes sense without
sound. IndieGameJoe has said he skips games that look unpolished or are hard to understand from
the trailer (HTMAG, May 2026). Pitch them by their published contact, with the clip attached or
linked. `utm_source` is the platform (`x`, `bluesky`).

## 7. What to write in the tracker

| Column | Example | Notes |
|---|---|---|
| name | Sam Writer | The person, not the site |
| outlet | Cozy Weekly | Site, channel or account |
| type | press | press, youtube, twitch, curator, aggregator, podcast, newsletter |
| contact | sam@cozyweekly.net | Email, or an https link for a Twitch page or contact form |
| contact_source | cozyweekly.net/about | Where the email is published; required before a key |
| audience | 85k subscribers | Subscribers, average viewers or monthly readers, with the unit |
| similar_games | Ooblets; Moonstone Island | Semicolons inside the field |
| status | todo | todo, drafted, sent, followed-up, replied, declined, covered, no-reply, skipped (we chose not to pitch; `declined` means they said no) |
| sent_date | 2026-11-10 | YYYY-MM-DD |
| follow_up_date | 2026-11-17 | About a week after sent |
| key_sent | 2026-11-10 | Date, or empty. Never the key itself |
| key_batch | press-launch-1 | The Steamworks batch the key came from |
| coverage_url | https://... | Filled when it goes live |
| utm_content | cozy_weekly_sam | Unique contact slug, lower case with underscores |
| link | https://store.steampowered.com/app/... | The tagged link in this contact's email |

## 8. Who to drop

- No activity in months, or view counts that are suspiciously even.
- Never covers games like yours (only one AAA series, only Minecraft).
- Only reachable through a free email that the channel page does not list.
- Asked you for several keys "for the team" or "for giveaways".
