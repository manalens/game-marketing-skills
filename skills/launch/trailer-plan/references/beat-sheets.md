# Beat sheets by trailer type

Contents:
- Rules for every cut
- Gameplay trailer (Steam page, first slot)
- Announce trailer
- Release date trailer
- Launch trailer
- 30 s and 15 s social cuts
- Shot list template

Times are starting points, not rules. Valve sets no length. Derek Lieu suggests 90 to 180 s for a
simple store page trailer, shots of about 3 to 5 s, and nothing shown more than three times.

## Rules for every cut

- Gameplay in the first second. No studio logo, publisher logo, engine logo, laurels or slow pan
  before it. Viewers do not wait 15 to 30 s for play (Simon Carless), and many skip through the
  progress bar to find it (Chris Zukowski), so every point on the timeline shows play.
- The genre is clear by about 5 s: the camera view, the HUD and the core verb on screen.
- Works muted: short on-screen words, the result of each action visible in frame.
- End card: game name (logo), platform, "Wishlist on Steam" (or "Play now on Steam" at launch),
  the date or window if known. 3 to 5 s. Nothing after it.
- One idea per shot. Cut on the music.

## Gameplay trailer (Steam page, first slot), 60 to 120 s

| Beat | Time | What |
|---|---|---|
| Cold open | 0 to 5 s | The most striking gameplay moment, HUD on. No text, or one short line |
| Core loop | 5 to 30 s | What the player does again and again, shown once in full (or several times for a short loop) |
| Variety | 30 to 70 s | New areas, enemies, tools, modes. Each feature gets a 3 to 5 s shot and at most a 3 word caption |
| Hook or twist | 70 to 90 s | The thing no similar game has |
| Peak | 90 to 105 s | The biggest moment, music at its highest |
| End card | last 3 to 5 s | Logo, "Wishlist on Steam", date or window |

Category in Steamworks: Gameplay. Drag it to the first slot.

## Announce trailer, 45 to 90 s

Goal: tell genre fans this game exists and get the wishlist. Released with the Coming Soon page,
capsule and press kit on the same day.

| Beat | Time | What |
|---|---|---|
| Cold open | 0 to 5 s | Gameplay that shows the genre and the hook at once |
| Premise | 5 to 15 s | One or two lines of on-screen text: who you are, what you do |
| Loop | 15 to 40 s | The core loop |
| Tease | 40 to 60 s | Two or three bigger moments, not all of them |
| End card | last 4 s | Logo, "Wishlist on Steam", release window ("2027"), platforms |

## Release date trailer, 45 to 75 s

Goal: give wishlisters a date. Reuse the gameplay trailer's best shots plus one new feature.

| Beat | Time | What |
|---|---|---|
| Cold open | 0 to 5 s | A new shot not seen in earlier trailers |
| Recap | 5 to 30 s | The core loop, fast |
| What is new | 30 to 50 s | Features added since the announce, demo feedback acted on |
| Date | last 5 s | Logo, the exact date in large type, "Wishlist on Steam" |

The exact date also feeds Steam's Personal Calendar: Valve wants it set 60 or more days ahead.

## Launch trailer, 60 to 90 s

Goal: "it is out, buy it". Fastest pace, most content, a reason to buy now.

| Beat | Time | What |
|---|---|---|
| Cold open | 0 to 5 s | The biggest moment in the game that is not a spoiler |
| Montage | 5 to 60 s | Everything: modes, biomes, bosses, co-op, at 1 to 3 s a shot |
| Proof | 60 to 75 s | Optional: player or press quotes from the demo. Quotes are fine in a trailer, not on capsules |
| End card | last 5 s | Logo, "Available now on Steam", launch discount if any |

## 30 s and 15 s social cuts (16:9)

Cut from raw gameplay, not by trimming the trailer opening. A 6 s 4:5 cut with 0.75 s shots beat
a full trailer as a Reddit ad for one indie (Melos Han-Tani, April 2026).

| Cut | Beats |
|---|---|
| 30 s | 0 to 3 s hook moment, 3 to 22 s loop and two features, 22 to 27 s peak, 27 to 30 s end card |
| 15 s | 0 to 2 s hook moment, 2 to 11 s loop, 11 to 15 s end card |

Vertical 9:16 and 4:5 versions: hand the cut to `clip-cut`.

## Shot list template

| # | Beat | Feature shown | Setup to capture (level, save, debug command) | Length | HUD | Caption | Captured |
|---|---|---|---|---|---|---|---|
| 1 | Cold open | Boss splits into 8 slimes | Level 3 save, `spawn boss_slime`, god mode on | 4 s | on | none | [ ] |
| 2 | Loop | Plant, water, harvest | Farm save day 12, morning | 5 s | on | Grow | [ ] |
| 3 | Loop | Sell at the market | Market save | 4 s | on | Sell | [ ] |
| ... | | | | | | | |
| N | End card | Logo | Logo PNG on key art | 4 s | off | Wishlist on Steam | [ ] |

Every feature in the list must be in the build. Write the setup so the person capturing can
reproduce the shot without asking.
