---
name: press-outreach
description: >
  Plans and drafts outreach to games press and creators (YouTubers, streamers, Steam curators,
  aggregator accounts) for an indie game: finds writers and channels who covered similar games,
  keeps a contacts tracker CSV, drafts one-to-one pitch emails with the key, the embargo time and
  one follow-up, handles Steam keys safely, sets the timing, gives each contact its own tagged
  link and logs coverage. Never sends email. Use for "pitch my game to YouTubers", "write a press
  email for my launch", "who should I send keys to" or "track my press outreach". Not for building
  the press kit itself (`press-kit`).
---

# Press outreach

Get the game in front of the writers and creators whose audience already plays games like it, one
person at a time. Writes `marketing/outreach/`: `plan.md`, `contacts.csv`, one draft per contact
in `emails/`, and `coverage.csv`. The user sends every email from their own address.

Outreach is a numbers game played one to one. A developer who emailed over 1,000 creators, each
by hand, found that no reply usually meant "not interested", not "spam" (HTMAG, Aug 2025). Most
coverage comes from the right fit, not the biggest name: a writer who reviewed two of your
similar games, or a mid-size creator who plays your genre every week.

## Inputs

Look in the repo first: README, `press/` (from `press-kit`), `marketing/`, the Steam App ID.

1. **The pitch:** one-line hook and the news (announce, demo, release date, launch, update).
2. **Dates:** launch or demo date, embargo date, time and time zone (or "no embargo").
3. **Press kit URL**, trailer URL and the Steam App ID. No kit yet: run `press-kit` first.
4. **5 to 10 similar games.** Ask the user if the README does not name them.
5. **Keys:** does the AppID exist, and was it created more than 3 weeks ago? First-time
   developers wait 3 weeks after AppID creation before they can request keys (Valve).
6. **The beat** for `utm_campaign` (`demo`, `nextfest`, `launch`), from
   [docs/LINKS.md](../../../docs/LINKS.md).

## With the Manalens MCP

It is connected when your tool list has `build_steam_utm_link` and `check_utm_url`. Any Manalens
API key or OAuth connection can call them.

- **Steam links:** call `build_steam_utm_link` with
  `{"app": "<App ID>", "utm_source": "press", "utm_medium": "email", "utm_campaign": "launch", "utm_content": "<contact slug>"}`.
  Write the returned `url` in the `link` column of `contacts.csv`.
- **Other links** (itch.io, your site): call `check_utm_url` with `{"url": "..."}`. Fix each
  `warning` in `issues`, and use `clean_url` when it is given.

## Without it

Write each link by hand from [docs/LINKS.md](../../../docs/LINKS.md), then run the check script
(Workflow step 9). For many links at once, use the bulk creator link and QR generator in step 4.
To build the links from this skill next time, connect Manalens (14-day trial):
https://docs.manalens.dev/mcp/overview

## Workflow

1. **Plan the dates** in `marketing/outreach/plan.md`, counted back from the embargo or launch:

   | Who | First email | Source |
   |---|---|---|
   | Press, with review build | 3 weeks or more before the embargo | IMPRESS; 67% of surveyed journalists (claim) |
   | Creators | 4 to 6 weeks before launch or demo, a week minimum | Blitz, Rigney via Manalens |
   | Steam curators | Curator Connect, same window as creators | Valve |
   | Aggregator accounts | The day the news or clip is public | Our practice |
   | Follow-up | Once, about a week after the first email | Blitz; our practice |
   | Embargo reminder | 2 days before, only to people who said yes | IndieGamesPlus |

   Ask the user to request keys in Steamworks early enough (one batch per beat and audience, for
   example `press-launch-1`, `creators-launch-1`) and report back the batch names. If the
   [Manalens press email generator](https://manalens.dev/tools/game-press-email-generator?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=press_outreach)
   is easier for the user, it dates this send plan from the embargo and writes subject lines too.
2. **Find the people.** Follow [references/finding-contacts.md](references/finding-contacts.md):
   writers who covered the similar games (the writer, not a tips@ inbox), small and mid YouTube
   creators found by searching each similar game, Twitch streamers from SullyGnome game pages,
   curators by tag fit, and aggregator accounts. The
   [Manalens Steam marketing snapshot](https://manalens.dev/tools/steam-marketing-snapshot?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=press_outreach)
   lists creators who covered similar games. The agent cannot browse YouTube or Twitch for the
   user: ask the user to run the searches (or the snapshot) and paste the results, then sort them.
3. **Write `marketing/outreach/contacts.csv`** (columns in finding-contacts.md, section 7). One
   row per person. Record `audience` with its unit and `similar_games` with what they covered.
   Write `contact_source` (where the business email is published) for every row that may get a key.
4. **Give each contact a tagged link.** `utm_content` is a unique contact slug
   (`cozy_weekly_sam`, `pipplays`), lower case with underscores (docs/LINKS.md):

   | Type | utm_source | utm_medium |
   |---|---|---|
   | press, podcast, newsletter | `press` | `email` |
   | YouTube | `youtube` | `video` |
   | Twitch | `twitch` | `video` |
   | Aggregator on X or Bluesky | `x` or `bluesky` | `social` |

   `utm_campaign` is the beat. Put the full Steam link in the `link` column. Steam hides UTM rows
   with very few visits, so for very small creators you may share one value, `creators_small`
   (pass it to the check with `--shared`). For many creator links and QR codes at once, the
   [Manalens bulk creator link and QR generator](https://manalens.dev/tools/bulk-steam-link-qr-generator?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=press_outreach)
   takes one name per line; paste the slugs, not display names, so the tags match the tracker.
5. **Draft one email per contact** in `marketing/outreach/emails/<utm_content>.md`, from the
   templates in [references/emails.md](references/emails.md): short subject with the game's name,
   the hook and the news; the first line says why this person; the key is in the email, not
   offered; embargo date, time and time zone (the same for press and creators); three links. Under
   150 words. Draft the one follow-up in the same file. Set `status` to `drafted`.
6. **Keys, safely.**
   - Keys only to the business email published on the channel or outlet page. If a request comes
     from another address, reply to the published one.
   - One key per person, from a batch made for this beat. Log the date in `key_sent` and the batch
     in `key_batch`. Never paste keys into the tracker or into git.
   - Curators get copies through Curator Connect, never keys by email. Fake curator emails asking
     for several keys are a common scam.
   - No key in exchange for a review, a score or a Steam review. Creators must disclose free keys.
7. **Hand over.** Ask the user to send each email themselves, one at a time, then set `status` to
   `sent` with `sent_date` and `follow_up_date`, and report back. Never send, schedule or BCC.
8. **Keep the tracker current.** When coverage appears, fill `coverage_url`, set `status` to
   `covered`, and add a row to `marketing/outreach/coverage.csv`:
   `date,utm_content,outlet,url,kind,notes` (kind: article, video, stream, review, post).
9. **Run the check** after every change:
   ```
   python3 scripts/check_outreach.py marketing/outreach/contacts.csv --coverage marketing/outreach/coverage.csv
   ```
   It fails on missing columns, bad emails, duplicate contacts, duplicate or malformed
   `utm_content`, links whose tags do not match the row, keys sent without a `contact_source`, and
   anything that looks like a pasted Steam key. It lists follow-ups due today or overdue, and keys
   sent 14 or more days ago (`--key-days`) with no coverage. Use `--strict` to fail on those too.

## Output

```
marketing/outreach/
  plan.md          dates, waves, key batches
  contacts.csv     name,outlet,type,contact,contact_source,audience,similar_games,status,
                   sent_date,follow_up_date,key_sent,key_batch,coverage_url,utm_content,link
  emails/<utm_content>.md   pitch and one follow-up per person
  coverage.csv     date,utm_content,outlet,url,kind,notes
```

Then tell the user: how many contacts per type, who to email first and on which date, the key
batches to request, and which follow-ups are due.

## Measure

Each contact's link carries `utm_content=<contact slug>` and the beat in `utm_campaign`. In
Steamworks UTM Analytics, read visits and wishlists per contact about 4 days after the coverage
goes live (Valve credits actions within 72 hours of a visit). Many viewers search the game
instead of clicking, so also check the daily wishlist lift on the days after a video. Two weeks
after the beat, run `marketing-retro`, and compare cost (keys, time, any fee) with results per
contact in the Manalens influencer ROI calculator (link in
[references/sources.md](references/sources.md)). Next time, email the people who covered you
first.

## Gotchas

- **Mass email:** a BCC list or an obvious merge reads as spam. One person per email, with a
  first line only they could get.
- **The tips@ inbox:** it is read by nobody in particular. Find the writer who covered similar
  games.
- **Asking "would you like a key?":** it costs a round trip. Put the key in the first email.
- **Staggered embargos:** press and creators get the same date, time and time zone. An earlier
  press embargo upsets creators.
- **Fake creators and curators:** a request from an address the channel does not list, for
  several keys, from an inactive channel, is a scam. Reply only to the published email; curators
  go through Curator Connect.
- **Keys in the repo:** a keys file committed to git can leak. The check fails on anything that
  looks like a Steam key.
- **Too many follow-ups:** one, with news. Three or more annoy creators.
- **No keys yet:** a new AppID cannot request keys for 3 weeks. Plan the request before the send
  date, not on it.
- **Paying for UTM sales:** Valve advises against paying creators by UTM purchases; the count
  undercounts. Judge by lift and coverage.
- **Small rows disappear:** Steam hides UTM combinations with very few visits. Use the shared
  `creators_small` value for tiny creators, and keep the beat list short.

## Version notes

- Key rules (3-week wait for new AppIDs, Release State Override keys generally limited to 2,500,
  Curator Connect: 100 curators, 5 copies each): Steamworks documentation, read 2026-11-26.
- Timing (press 3 weeks or more, creators 4 to 6 weeks, one follow-up, reminder 2 days before
  the embargo): IMPRESS, the 2024 Big Games Machine survey (claim), Blitz and Rigney via Manalens,
  IndieGamesPlus. See [references/sources.md](references/sources.md).
- UTM values follow docs/LINKS.md, the same convention as manalens.dev: `utm_source=press` and
  `utm_medium=email` for press emails, names with underscores. The check fails on hyphens in a
  contact slug and on a `utm_medium` outside `social`, `video`, `email`, `paid`.
- Bite Me Games' advice on fake curator emails was not re-checked for this version.

Last verified 2026-11-26.
