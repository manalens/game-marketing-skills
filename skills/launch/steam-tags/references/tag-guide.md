# Steam tag guide

Valve's rules in its own words, the niche method, the Personal Calendar link, and sources.

Contents:

1. What Valve says
2. Tag tiers and examples
3. Finding a niche
4. The Personal Calendar
5. After the tags go live
6. Sources

## What Valve says

From the Steamworks "Steam Tags" page (read 19 November 2026), as quoted in the Manalens tag
compare tool:

- "We began requiring at least 5 tags be applied to a title before its launch on Steam, but we
  recommend you add up to 20."
- "Only the top 20 are visible to users and used by Steam to influence visibility of your title
  in the store."
- "Some store filters prioritize the first 15 tags, so be sure that these are sorted in order of
  relevance to your title."
- "Your title's top 5 tags should paint a fairly clear picture of your game as those tags will
  also be used to describe your game."
- "Some of Steam's recommendation algorithms also factor in less-frequently used tags more than
  really common ones."
- Tags and weights can change as players apply them; you can revisit the Tag Wizard at any time.

For recommendations, overlap matters more than order: a game with Open World and Fantasy is more
likely to be recommended to players of games with both. The Tag Wizard sits under Store Presence,
Edit Store Page, Basic Info.

## Tag tiers and examples

Our sorting, used by `check_tags.py`:

| Tier | Examples | Where |
|---|---|---|
| Specific sub-genre | Roguelike Deckbuilder, Colony Sim, Farming Sim, Souls-like, Metroidvania, Turn-Based Tactics, Bullet Hell, Automation | Top 5 |
| Second mechanic, theme, style | Deckbuilding, Base Building, Pixel Graphics, Dark Fantasy, Co-op | 6 to 15 |
| Parent genre | Strategy, Simulation, RPG, Puzzle, Arcade, Shooter, Platformer | Below the specific tags |
| Empty calorie (HTMAG) | Indie, Action, Adventure, Casual | Not top 5 |
| Low information | Singleplayer, 2D, 3D | Bottom |
| Status | Early Access, Free to Play | Only if true |
| Opinion | Masterpiece, Great Soundtrack, Addictive, Replay Value | Leave to players |

Worked example from the Manalens tag compare tool (made-up games): 10 roguelike deckbuilders all
share Roguelike Deckbuilder, Deckbuilding and Card Game, and 9 of 10 have Strategy. A new game whose
list has Cozy in place of Deckbuilding misses a shared tag and adds one none of them have; the
tool flags both.

## Finding a niche

1. Take the label's 2 or 3 genre tags.
2. Look up each in the benchmark (script output or manalens.dev/steam/genres): games in 2022 to
   2025, share of all games (Crowded at 5% or more, Smaller under 2%), share that reached 50+
   reviews against 25.6% for all games.
3. Look up the pair (the analyzer's niche mode shows pairs from the same snapshot). A pair with
   fewer games and a share at 50+ reviews near or above all games is a niche worth naming in the
   top 5.
4. Confirm with similar games: if games in the pair sold, players exist for it.
5. Only keep the niche if the build is in it. A niche label that a player does not recognize in
   the screenshots loses the visit.

Examples from the snapshot of 18 November 2026: Roguelike Deckbuilder had 370 games (0.7%,
Smaller) and 55.1% reached 50+ reviews; Casual had 17,830 games (31.4%, Crowded) and 17.7%.

## The Personal Calendar

- HTMAG (25 June 2026): with the Personal Calendar, Steam shows a game to players with matching
  taste, so lean into the genre's look and tropes. Popular Upcoming now needs far more wishlists,
  and the calendar became the first rung.
- Valve: the calendar finds players with similar tastes from what they play, shows games those
  players wishlisted, and places each on its release date. Players can filter it by store tag; by
  default the tag list comes from games they played recently. It needs a specific release date.
- So: the top tags should be the tags that the players of your comparison games already see.
  A tag no one in your genre uses does not put you in their calendar.

## After the tags go live

- Check the "similarly tagged titles" view in Steamworks. Valve notes it is a tag comparison, not
  the More Like This result.
- Recheck the public top 20 after a demo, a festival or launch.
- Remove wrong player tags (Valve's example: family friendly on a horror game).
- Next Fest: one or two categories at registration plus your tags decide your fest sections.

## Sources

- Valve, Steamworks documentation, Steam Tags. https://partner.steamgames.com/doc/store/tags
  (read 19 November 2026)
- Valve, Steamworks documentation, Steam Personal Calendar.
  https://partner.steamgames.com/doc/marketing/visibility/personalcalendar (read 18 November 2026)
- Steam News, "Steam's Personal Calendar Full Release", 23 October 2026.
- Valve, Steam blog, "Introducing The Steam Interactive Recommender", 18 March 2020.
- Valve, Steamworks documentation, Steam Next Fest tips (categories and tags).
- Chris Zukowski, How To Market A Game, "Steam 101: How to tag your game", 12 November 2020.
  https://howtomarketagame.com/2020/11/12/steam-101-how-to-tag-your-game/
- Chris Zukowski, How To Market A Game, "How the Steam Personal Calendar affects your launch",
  25 June 2026.
  https://howtomarketagame.com/2026/06/25/how-the-steam-personal-calendar-affects-your-launch/
- Simon Carless, GameDiscoverCo, "Analyzing the top Steam tags", 7 January 2020 (old revenue
  estimates; context only).
- Manalens Steam tag benchmark snapshot, 18 November 2026: 56,800 games released 2022 to 2025,
  a tag counted when in a game's top 7, 66 tags. Bundled as `scripts/benchmark_tags.json`.
- Manalens tag guide "Steam tags: how to choose them, with data" and the tag compare tool rules
  (common in set at 50% or more; 10 to 20 games suggested). Read 26 November 2026.
