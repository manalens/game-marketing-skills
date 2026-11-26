---
name: game-name-check
description: >
  Helps pick and check a game name. Brainstorms a shortlist that says the genre or the fantasy, is
  unique enough to find on Steam and Google, is easy to spell after hearing it, and works as a
  hashtag and handle. Then runs or hands the user a checklist: Steam and itch.io search for exact
  and close names, Google, trademark databases (USPTO, EUIPO TMview, WIPO), domains, handles on
  YouTube, TikTok, X, Bluesky, Instagram, Reddit and Discord, app stores, and confusion with
  existing games. Scores each name offline and writes launch/name-check.md. Use for "is my game
  name taken", "help me name my game", "check if this title is searchable". Gives no legal advice.
  Not for the store page text, description or capsules (use steam-page-review).
---

# Game name check

Pick a game name that players can hear once, spell, find and own. The agent drafts a shortlist,
scores it offline with `scripts/name_score.py`, runs the searches it can and asks the user to run
the rest, and writes `launch/name-check.md` with a scored table per candidate. It never registers
a domain, claims a handle or files anything, and it gives no legal advice.

## Inputs

Look in the repo first, then ask only for what is missing.

- **The game:** genre, setting, the fantasy (what the player gets to be or do), 2 or 3 comparable
  games. Look in `README.md`, design docs, `marketing/` and any store page draft.
- **Candidate names**, if the user has some. Also the current working title.
- **Platforms:** PC only, or a mobile or console port later (mobile stores allow 30 characters).
- **Markets:** where they will sell. This decides which trademark offices matter.
- **Stage:** has the Steam store page passed its pre-release review? Valve locks the store name
  after that review, so a late rename needs Valve's approval.

## Workflow

1. **Read the game.** Write down in one line the genre words a shopper would type and the fantasy
   in plain words ("run a haunted inn", "a cozy farming roguelike"). Output: a one-line brief at
   the top of `launch/name-check.md`.
2. **Brainstorm 8 to 15 names**, then cut to 3 to 6. Use [references/brainstorm.md](references/brainstorm.md)
   for patterns. Each name should do at least one of: say the genre, say the fantasy, or be a
   distinct invented word that the capsule and tags explain. Keep the core name within 30
   characters; a subtitle after a colon is optional. Output: the shortlist.
3. **Say it out loud test.** For each name, write how it sounds and the two most likely wrong
   spellings a listener would type. If a wrong spelling is likely, change the name or own both
   spellings. Ask the user to say each name to one person in a noisy room and have them type it
   (Chris Zukowski's test), and report back.
4. **Collect existing titles.** Search Steam for each name and for its main word, and write every
   title from the first page of results to `launch/existing-titles.txt`, one per line. Add the
   comparable games and the biggest games in the genre. If the agent cannot browse, ask the user
   to paste the Steam and itch.io result titles and report back.
5. **Score offline:** `python3 scripts/name_score.py --file launch/candidates.txt --existing
   launch/existing-titles.txt --fail-on-exact`. It scores length, word count, spelling risk,
   search uniqueness, handle fit and similarity to existing titles. It makes no network requests.
   Treat the total as a way to rank a shortlist, not a verdict. Output: the table.
6. **Run the availability checklist** in [references/checklist.md](references/checklist.md) for
   the top 2 or 3 names: Steam (exact and similar), itch.io, Google, app stores, trademark
   databases, domains, handles (YouTube, TikTok, X, Bluesky, Instagram, Reddit, Discord custom
   invite), and clone or confusion risk. The agent runs the web searches it can reach and marks
   each row with who checked it and when. Rows it cannot check say "ask the user to open <link>
   and report back". Never register, claim or buy anything.
7. **Trademark: search, do not advise.** Record what the free searches show (live marks in class 9
   or 41 with the same or a similar name). Do not say a name is "safe" or "clear". Write: "A free
   search is not legal advice. Before you commit to the name for a commercial launch, ask a
   trademark lawyer to clear it in the countries where you sell."
8. **Clone and confusion risk.** Note games with a close name in the same genre, and whether the
   name leans on a famous game ("Hollow", "Souls", "Craft" plus a genre word). For the wider
   question of how easy the game is to copy, run the four signs from
   [references/checklist.md](references/checklist.md#clone-and-confusion-risk), or hand off to the
   [Manalens game clone risk check](https://manalens.dev/tools/game-clone-risk-check?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=game-name-check).
9. **Recommend.** Pick one name and one backup, and say why in two or three sentences. List what
   is still unchecked. Hand off: the [Manalens game name checker](https://manalens.dev/tools/game-name-checker?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=game-name-check)
   runs the store name rules, a live Steam lookup for exact and close names, DNS for .com, .io,
   .gg, .games and .dev, and opens prefilled trademark and handle searches.
10. **Check the file:** `python3 scripts/name_score.py --file launch/candidates.txt --existing
    launch/existing-titles.txt --fail-on-exact` exits 0 for the shortlist, and
    `grep -c "^| " launch/name-check.md` shows a table row per candidate. Fix and rerun on failure.

## Output

`launch/name-check.md`, plus `launch/candidates.txt` and `launch/existing-titles.txt` as inputs:

```markdown
# Name check: <working title>
Brief: a cozy farming roguelike; you run a pumpkin farm that fights back. Checked 2026-11-26.

## Scores (scripts/name_score.py)
| Name | Total | Length | Words | Spelling | Search | Handles | Similarity | Handle | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Brambleborne | 81 | 100 | 100 | 100 | 100 | 100 | 59 | brambleborne | none |

## Availability: Brambleborne
| Check | Result | Who, when |
|---|---|---|
| Steam exact / similar | none / "Bramble: The Mountain King" (horror, different genre) | agent, 2026-11-26 |
| USPTO, TMview, WIPO (class 9, 41) | no live mark found in a free search | user, 2026-11-27 |
| brambleborne.com | taken (parked) | agent |
| @brambleborne on YouTube, TikTok, X, Bluesky, Instagram | free, free, taken, free, free | user |
| r/brambleborne, discord.gg/brambleborne | free / needs Boost Level 3 | user |
| Confusion | low: no game of the same genre with a close name | agent |

## Recommendation
Brambleborne, backup Thornwick Farm. Still unchecked: lawyer clearance, EU marks.
```

## Measure

Before announcing, check that the name returns the game first: a week after the Steam page goes
live, search the exact name on Steam and Google from a logged-out browser and note the rank. In
Steamworks, read the store traffic from Search Suggestions and from Google: these grow when people
hear the name and type it. Log both numbers in `launch/name-check.md`; `marketing-retro` reads
them with the other launch numbers.

## Gotchas

- **Name locked after review:** Valve locks the store name after the pre-release store page
  review. Finish the trademark search before the user submits the page.
- **A free search is not clearance:** the USPTO says a conflict can exist when marks are similar
  in sound, look or meaning and the goods are related. Never call a name "safe". Say what the
  search showed and suggest a lawyer.
- **Descriptive names are weak marks:** "Farm Simulator" says the genre but is hard to protect
  and hard to find. An invented word is easy to protect but says nothing, so the subtitle, capsule
  and tags must carry the genre.
- **Same name, different store:** Steam does not block a duplicate name, but players who type it
  find the other game first. Treat an exact match on Steam or itch.io as a fail.
- **Handle taken by a dead account:** a profile page that loads can belong to an inactive or
  deleted account, and a domain with no DNS records can still be registered. Treat both as hints.
- **Handle variants:** if the exact handle is taken, prefer one consistent variant everywhere
  (`playbrambleborne`, `bramblebornegame`) over a different one per platform.
- **Script blind spots:** the common word list is small, so a rare real word scores as "invented",
  and the homophone list is short. Read the notes column, not only the total.
- **Riding a famous name:** a title built around another game's mark ("...Craft", "...Souls")
  invites confusion and takedowns. Flag it and suggest another name.

## Version notes

- Steam locks the name after the pre-release store review; changes after that need Valve
  (Steamworks "Changing your game's name", read by Manalens 2026-11-18).
- App Store: 2 to 30 characters; Google Play: 30 or fewer, no emoji, no ALL CAPS unless brand,
  no ranking or price words (store help pages, read by Manalens 2026-11-18). No published Steam
  name limit was found.
- Handle rules (lengths and characters per platform) are in [references/handles.md](references/handles.md)
  with sources; they change without notice.
- Title length did not correlate with sales across 94,371 Steam games (How To Market A Game,
  3 Feb 2025). Sources: [references/sources.md](references/sources.md).

Last verified 2026-11-26.
