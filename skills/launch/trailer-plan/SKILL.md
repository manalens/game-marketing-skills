---
name: trailer-plan
description: >
  Plans and scripts a game trailer: the Steam page gameplay trailer (whose clips Steam reuses for
  its microtrailer), announce, release date and launch trailers, and 15 and 30 second social cuts.
  Writes a beat sheet and a shot list from the game's real features, with music licensing, capture
  tips (60 fps, clean HUD option, no debug overlays), export specs for Steam and YouTube, and where
  to send the finished file. A script checks an exported trailer with ffprobe and ffmpeg:
  resolution, frame rate, codec, bit rate, length, loudness, and black frames or silence at the
  start. Use for "plan my game trailer", "shot list for my announcement trailer" or "check my
  trailer export for Steam". Not for short vertical clips or Shorts scripts (`clip-cut`,
  `shorts-script`) or capsule art (`steam-capsules`).
---

# Trailer plan

Plan a game trailer that shows play from the first second, says the genre in five, and ends on
the name and "Wishlist on Steam". The agent reads the repo for the game's features, writes a beat
sheet and a shot list someone can capture from, and checks the exported file. Output:
`launch/trailer/<name>.md`.

The first trailer on a Steam page matters most. It autoplays at the top of the page, the first
two trailers play before any screenshot, and Steam cuts its 6-second microtrailer from six
1-second clips taken across the first trailer. Valve warns that a Discovery Queue viewer may give
it under 10 seconds, often muted.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **The game in one line and its genre:** README, design docs, store text.
2. **Features that are in the build:** design docs, feature lists, level and enemy folders, the
   changelog or git log. Only what a player can see today goes in the shot list.
3. **Trailer type and date:** announce, gameplay (page), release date, launch, or a social cut.
   The beat it serves (`announce`, `launch`, ...) and the release date or window.
4. **Music:** the game's soundtrack and who holds its rights, or a library track and its license.
5. **Capture setup:** engine, debug or cheat commands, a free camera, a HUD toggle, save files.
6. **Do-not-show list:** spoilers, placeholder art, features that may be cut. Check
   `marketing/rules.md` if it exists.

## Workflow

1. **Pick the type and length.** Output: one line at the top of the file. Defaults:

   | Type | Length | Goal | Ends with |
   |---|---|---|---|
   | Gameplay (Steam page, first slot) | 60 to 120 s | Show the game to a visitor who chose to look | Wishlist on Steam |
   | Announce | 45 to 90 s | "This exists, it is your genre" | Wishlist on Steam, window |
   | Release date | 45 to 75 s | Give wishlisters a date | Exact date, Wishlist on Steam |
   | Launch | 60 to 90 s | "Out now, buy it" | Available now on Steam |
   | Social cut | 15 or 30 s | Stop the scroll | Name, Wishlist on Steam |

   Valve sets no length. Derek Lieu suggests 90 to 180 s for a store page trailer; shorter is fine
   with less content. The first trailer on the page should be the gameplay one.

2. **List the features** from the repo, each with where it shows on screen. Output: a feature
   list, ranked by what a genre fan would stop for. Drop anything not in the current build.

3. **Write the beat sheet** from [references/beat-sheets.md](references/beat-sheets.md).
   Output: a beat table. Rules:
   - Gameplay in the first second. No studio, engine or publisher logo, no laurels, no slow pan
     before it. Viewers will not wait 15 to 30 s for play (Simon Carless).
   - Genre clear by about 5 s: camera view, HUD and the core verb on screen. Valve recommends the
     first trailer be "primarily gameplay" with the HUD visible.
   - Play at every point of the timeline. Many viewers skip ahead, and the microtrailer is cut
     from points all through it.
   - Works muted: short on-screen words (about 3 words a caption), results visible in frame.
   - Shots of about 3 to 5 s; nothing shown more than three times (Lieu). Faster for launch and
     social cuts.
   - End card for the last 3 to 5 s: logo, "Wishlist on Steam" (or "Available now on Steam"),
     date or window, platforms. Nothing after it.

4. **Write the shot list.** Output: a table with, per shot, the beat, the feature, the exact
   setup to capture it (level, save, debug command, camera), length, HUD on or off, caption, and
   a capture box. Plan about five times more footage than the cut needs.

5. **Plan the music.** Output: a music section. The game's own soundtrack is simplest. For any
   track, get a written license that names Steam, YouTube, social posts and paid ads, because the
   same trailer ends up in all four. YouTube Audio Library tracks are Content ID safe, but
   Creative Commons ones need credit in the description, and YouTube takes no responsibility for
   "royalty-free" music from other places. Cut on the beat. Keep game sound effects under the
   music where they sell the action.

6. **Write the capture notes.** Output: a capture checklist:
   - 1920 x 1080 or more, 60 fps (Steam accepts 30 or 60), steady frame rate. Record at the
     final frame rate.
   - A capture build with no debug text, FPS counters, version watermarks, dev names or
     placeholder art. Hide the OS cursor unless the game uses it.
   - A clean HUD option: capture key shots twice, HUD on (for the gameplay trailer) and HUD off
     (for the press kit, capsule art and cinematic beats).
   - Debug helpers for the shoot: god mode, spawn commands, free camera, time of day, slow motion.
   - OBS: Game Capture on Windows, record to MKV (a crash does not lose the file), then remux to
     MP4. Put game audio and music on separate tracks.
   - Capture 60 to 90 s of raw gameplay with no music or text for the press kit.

7. **Write the export and delivery plan.** Output: an export table and a send list. Specs in
   [references/export-specs.md](references/export-specs.md): Steam wants .mp4, .mov or .wmv,
   H.264 and AAC preferred, up to 1920 x 1080, 30 or 60 fps, 5,000 Kbps or more, 44.1 or 48 kHz
   audio. YouTube recommends MP4, H.264, AAC-LC 48 kHz, 8 Mbps (30 fps) or 12 Mbps (60 fps) at
   1080p. Send list:
   - **Steam page:** ask the user to upload it days early (Valve converts trailers first in,
     first out, and the game cannot release while one converts), drag it to the first slot, set
     the category, and pick a thumbnail frame with no text. Remove trailers that no longer show
     the game.
   - **YouTube:** the user's channel, with a tagged Steam link first in the description (below).
     Shorts can point to it as their "related video".
   - **Press kit:** a direct 1080p MP4 download plus the raw gameplay. See `press-kit` if present.
   - **Trailer channels, showcases and aggregators:** list the ones that cover the genre and their
     submission rules, and ask the user to send it. For festivals and showcases, start from the
     user's event list. A clear, polished cut matters: aggregators skip games that are hard to
     understand from the trailer.
   - **Social:** 30 and 15 s cuts (16:9 here; vertical through `clip-cut`).
   - **Next Fest:** a public trailer must be on the base game page; Valve pulls trailers for the
     official fest trailer, and you can opt out by a set date.

8. **Run the checks.** Output: check results in the file.
   - On the plan: every shot names a feature from step 2, the first beat starts at 0 s with
     gameplay, and the last beat is the end card.
   - On the export, once the user has one:

     ```bash
     python3 scripts/check_trailer.py launch/trailer/announce.mp4
     python3 scripts/check_trailer.py cut30.mp4 --profile social --max-seconds 30
     python3 scripts/check_trailer.py announce_yt.mp4 --profile youtube
     ```

     It fails on a wrong container, frame rate, bit rate, aspect ratio, sample rate, black frames
     at the start, or a social cut over its length, and warns on codec, resolution, silence at
     the start, black gaps, and loudness away from -14 LUFS or a true peak over -1 dBTP. Exit 0
     means it passes; `--strict` turns warnings into failures.

9. **Hand off.** Draft only. Never upload or submit. Ask the user to upload to Steam and YouTube
   and report back the YouTube URL for `marketing/posts.csv`. For the reasoning behind gameplay
   first and how to measure the change, see
   [Steam trailer best practices](https://manalens.dev/blog/steam-trailer-best-practices?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=trailer_plan);
   for the full capture and edit walkthrough, see
   [How to make a game trailer](https://manalens.dev/blog/how-to-make-a-game-trailer?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=trailer_plan).

## Output

`launch/trailer/<name>.md`, for example `launch/trailer/announce.md`:

```markdown
# Announce trailer: <game>

- Type: announce. Length: 75 s. Beat: announce. Date: 2027-03-10 (with the Coming Soon page).
- Post ID: 2027-03-10-yl-announce-trailer
- YouTube link: https://store.steampowered.com/app/<appid>/?utm_source=youtube&utm_medium=video&utm_campaign=announce&utm_content=2027-03-10-yl-announce-trailer

## Beat sheet
| Time | Beat | On screen | Text | Music |
|---|---|---|---|---|
| 0-5 s | Cold open | Boss splits into 8 slimes | none | drop |
| 5-15 s | Premise | Farm at dawn, player plants | You farm by day. | verse |
| ... | | | | |
| 71-75 s | End card | Logo on key art | Wishlist on Steam. 2027. | final hit |

## Shot list
| # | Beat | Feature | Setup | Length | HUD | Caption | Captured |
|---|---|---|---|---|---|---|---|

## Music
Track, composer, license (Steam, YouTube, social, ads: yes/no), credit line.

## Capture checklist
## Export and send list
## Checks
```

Append the YouTube upload to `marketing/posts.csv` with format `trailer`.

## Measure

Steam does not report trailer views. Measure what visitors do: the page wishlist rate (wishlist
adds divided by store page visits) for about 14 days before and 14 days after a new first
trailer, leaving out days with a sale, a festival or a big creator video. Change only the trailer
in that window. For the YouTube upload, the tagged link above shows visits and wishlists in
Steamworks UTM Analytics (counted within 72 hours, final after about 4 days), and
`marketing-retro` reads it by post ID. Note the change date in `marketing/posts.csv`.

## Gotchas

- **Logo first:** a studio or engine logo before play costs viewers and can land in the
  microtrailer. Put logos on the end card or leave them out.
- **Cinematic first trailer:** a story or CG trailer in slot one hides the game. Put it second.
- **Trailer stack:** old trailers pile up on the page. Keep one or two that show today's game.
- **Upload on launch day:** processing is a queue, and the game cannot release while a trailer
  converts. Upload days early. Re-uploading puts it at the back of the queue.
- **Odd sample rate or resolution:** the most common reason a Steam upload fails. Export 48 kHz
  and 1920 x 1080.
- **Debug text in the footage:** FPS counters and version stamps show up in press coverage for
  years. Check every shot at full screen.
- **Music claims:** an unlicensed or "royalty-free" track from a random channel can get the
  YouTube upload claimed. Get the license in writing before the edit.
- **Promising cut features:** every shot must be in the build players will get.
- **Quotes and laurels in the trailer:** allowed in a trailer (Valve's no-quotes rule covers
  capsules), but they belong at the end, never before gameplay.

## Version notes

- Steam file specs, microtrailer, slot order, thumbnails and processing: Steamworks Trailers
  documentation, as read by Manalens on 18 and 24 November 2026.
- YouTube 1080p bit rates (8 and 12 Mbps) and 48 kHz AAC-LC: YouTube Help, recommended upload
  encoding settings, as of November 2026.
- Next Fest trailer pull dates: February 2027 fest, Valve pulls trailers 18 January 2027,
  opt-out by 11 February 2027; June 2027 fest, pull 3 May 2027, opt-out by 3 June 2027 (Manalens
  Next Fest checklist, from Valve). Check the current fest page.
- The -14 LUFS loudness target is our practice, not a Valve or YouTube rule.
- Lengths and shot timing are trailer editors' advice (Derek Lieu 2021, GameDiscoverCo 2022), not
  platform rules. See [references/sources.md](references/sources.md).

Last verified 2026-11-26.
