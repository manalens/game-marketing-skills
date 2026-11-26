---
name: steam-tags
description: >
  Chooses and orders the Steam tags for an indie game: up to 20 tags with the most specific
  sub-genre tags first, compared against 3 to 20 similar games, with a niche read (how crowded each
  genre tag is) and a check for misleading or vague tags. Ties the top tags to the Personal
  Calendar, where Steam shows a game to players whose taste matches its genre. Writes
  launch/steam-tags.md and a plain tag list that a script checks. Use for "pick Steam tags for my
  game", "which tags should come first", "find a niche for my roguelike" or "are my Steam tags
  wrong". Not for the store page text, screenshots or trailer (`steam-page-review`) or capsule art
  (`steam-capsules`).
---

# Steam tags

Pick the tags that tell Steam, and players, what kind of game this is. The skill reads the game's
repo for genre and loop, gathers the tags of similar games, picks and orders 20, checks the list
with a script, and writes `launch/steam-tags.md` (the reasons) and `launch/steam-tags.txt` (the
list to type into the Tag Wizard).

Tags decide which tag pages, filters and recommendations a game shows up in. Valve: only the top
20 are shown and used, the top 5 describe the game, some filters prioritize the first 15, and rare
tags count more than common ones for recommendations. Since June 2026 the Personal Calendar shows
each player upcoming games that players with similar taste wishlist, and players filter it by tag.
So the job is to look like your genre at a glance (HTMAG, 25 June 2026), not to collect traffic
with popular tags.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **The game:** README, design docs, press notes, `marketing/`. Pull the genre label in 3 to 5
   words, the loop verbs, setting, art style, camera, player count, and what is in the build.
2. **Similar games:** 3 to 5 games players will compare it with, including the biggest game in the
   genre. For a full comparison, 10 to 20. Check the design docs for "inspired by" lists first.
3. **Their tags:** the top tags of each similar game, in page order. Ask the user to copy them
   from each store page (the "+" button shows all), or to run the compare mode of the tag analyzer
   (Workflow step 2). Save them as `launch/similar-tags.txt`, one game per line:
   `Slay the Spire: Roguelike Deckbuilder, Deckbuilding, Card Game, ...`
4. **Current tags,** if the page exists: from Steamworks or the store page, in order.
5. **State:** Coming Soon, demo, Early Access, released. Status tags must be true.

## Workflow

1. **Write the label.** One line: "a <sub-genre> <genre> about <hook>". Each word in it should map
   to a tag. If the label needs a tag that does not exist, use the nearest real tag and keep the
   hook for the short description (`steam-page-review`).
2. **Gather similar games' tags** into `launch/similar-tags.txt`. For 10 or more games, ask the
   user to paste store links into the compare mode of the
   [Steam tag analyzer](https://manalens.dev/tools/steam-tag-analyzer?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=steam-tags)
   and report back its "Tags you miss" and "Tag order" tables. Without the tool, the script's
   `--similar` option counts the shares from the file.
3. **Build the pool.** Union of the similar games' tags plus the label's tags. Remove tags that
   do not fit the build. Pick to narrow the genre: if you think "my game might be this", skip
   the tag (Manalens tag guide, after HTMAG and Valve's Tag Wizard).
4. **Read the niche.** For the 3 to 6 genre tags at the top of the pool, run the script once to
   see the bundled benchmark label (Crowded, Mid, Smaller, from games released 2022 to 2025) and
   the share of games that reached 50 reviews. A niche is a specific sub-genre or a pair of tags
   with fewer games where a good share still reached 50 reviews. Check pairs with the niche mode of
   the analyzer, or the benchmark pages at
   [manalens.dev/steam/genres](https://manalens.dev/steam/genres?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=steam-tags).
   Never pick a niche the game does not belong to: the tags must describe the build.
5. **Order the 20.** Write each tag with a one-line reason:

   | Positions | What goes there |
   |---|---|
   | 1 to 5 | The most specific sub-genre tags and the hook mechanic. Together they say the label. |
   | 6 to 15 | Parent genres, second mechanics, setting and theme, camera or art style, player mode. |
   | 16 to 20 | Broad tags (Strategy, Action), Singleplayer, Indie, mood tags. |

   Rare, specific tags weigh more for recommendations; overlap with similar games matters more
   than exact order there. Order matters for the top 5 and for filters (first 15). Tags that
   similar games share build that overlap; a tag only you have must be true and specific.
6. **Check for misleading tags.** For each tag, name the build feature that proves it. Drop
   popular tags that do not fit: a puzzle game tagged City Builder reaches city builder players
   who do not want it (HTMAG, 12 November 2020). Opinion tags (Masterpiece, Great Soundtrack,
   Addictive) are for players to apply, not you. Early Access and Free to Play only when true.
7. **Run the check:**

   ```
   python3 scripts/check_tags.py launch/steam-tags.txt --similar launch/similar-tags.txt
   ```

   It fails on fewer than 5 or more than 20 tags, duplicates (also "Point & Click" vs "point and
   click"), a top 5 with no specific tag, Indie or Singleplayer in the top 5, and opinion tags in
   the top 10. It warns on fewer than 20, broad tags above the specific ones, status tags, and tags
   used by half the similar games that you left out. Unknown tags are info: the bundled list holds
   66 genre tags, not all of Steam's. Fix and run again until it exits 0.
8. **Write the output** (below). Draft only.
9. **Hand off.** Ask the user to open the Tag Wizard (Steamworks: Store Presence, Edit Store Page,
   Basic Info; it needs the Edit App Metadata and Publish App Changes permissions), enter the 20
   in order, then open the "similarly tagged titles" view and report back whether the comparison
   games show up. If they do not, the profile is off: revisit positions 1 to 5. Community notes
   also mention a third-party "Steam Tag Helper"; we have not checked it, so treat its output as
   a second opinion only.

## Output

`launch/steam-tags.txt`: one tag per line, in order, nothing else.

`launch/steam-tags.md`:

```markdown
# Steam tags: <game>
Label: a turn-based tactics roguelike about keeping lighthouses lit
Similar games: Slay the Spire, Into the Breach, Monster Train (launch/similar-tags.txt)

| # | Tag | Why (build proof) | In similar games | Benchmark |
|---|---|---|---|---|
| 1 | Turn-Based Tactics | grid fights each night | 2 of 3 | Mid, 3.0% |
| 2 | Roguelike | runs reset, map is random | 3 of 3 | Crowded, 5.3% |
...
| 20 | Indie | true, lowest weight | 3 of 3 | Crowded |

## Niche read
Turn-Based Tactics + Roguelike: <games, share at 50+ reviews, from the analyzer or /steam/genres>

## Left out
- City Builder: popular, but there is no building. Misleading.

## Check
check_tags.py: 0 failed, 0 warnings (2026-11-26)

## Changes
- 2026-11-26: first set entered (by the user)
```

## Measure

Tags change where Steam shows the game, so watch impressions and click-through by source in the
Steamworks traffic report (tag pages, More Like This, Discovery Queue, search). Log the date of
each tag change under "Changes", then compare the 4 weeks before with the 4 weeks after. Change
one thing at a time: a tag change in the same week as a festival or a trailer cannot be read on
its own. After a demo, a fest or launch, ask the user to export the public top 20 again and rerun
the check: player-applied tags can push yours down. `marketing-retro` reads the change dates next
to the UTM rows from [docs/LINKS.md](../../../docs/LINKS.md).

## Gotchas

- **Players tag too:** non-limited accounts can apply tags, and their weight mixes with yours.
  Remove wrong player tags in the Tag Wizard; Valve says weights tend not to move much.
- **Tags are not the whole algorithm:** Valve's Interactive Recommender learns from playtime and is
  not directly affected by tags. Tags place the game; playtime and sales keep it there.
- **Indie and Singleplayer at the top:** Valve's Suggest Prioritization moves low-information tags
  down. HTMAG calls Indie, Action, Adventure and Casual "empty calorie" tags in the top 5.
- **Benchmark limits:** the bundled list counts a game for a tag only when the tag is in its top 7,
  covers 66 tags and games released 2022 to 2025. Use it to compare crowding, not as Steam's count.
- **Old revenue-by-tag data:** the 2020 and 2021 tag revenue tables are estimates. Use them to
  understand a genre before you build, not to pick tags for a finished game.
- **Next Fest:** Valve sorts the fest by your one or two registration categories and your tags. Check
  your section on the Developer Preview Page before the fest, while you can still fix tags.
- **Clever tags at the top:** a rare tag that is not your genre hides you from the players whose
  calendar and recommendations should show you. Specific, yes; off-genre, no.

## Version notes

- Valve, Steam Tags doc (read 19 November 2026): at least 5 before launch, up to 20 recommended,
  only the top 20 shown and used, first 15 prioritized by some filters, top 5 describe the game,
  rare tags count more.
- Personal Calendar: launched in June 2026 (HTMAG, 25 June 2026), left Steam Labs on
  23 October 2026. Players filter it by tag; the default tag list comes from recently played games.
- Bundled benchmark: Manalens snapshot of 18 November 2026 (`scripts/benchmark_tags.json`).
- More detail and sources: [references/tag-guide.md](references/tag-guide.md).

Last verified 2026-11-26.
