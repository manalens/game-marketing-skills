---
name: clip-cut
description: >
  Cuts a gameplay clip into ready-to-post video files with ffmpeg: vertical 9:16 for YouTube
  Shorts, TikTok and Instagram Reels, 4:5 and 16:9 for Reddit and X, and a looping GIF. Burns in
  hook text for the first seconds, adds an end card, speeds up, and normalises loudness. Use for
  "cut a vertical clip for Shorts/TikTok/Reels", "make a GIF for Reddit", "add hook text to my
  gameplay clip", "turn my trailer into a 9:16 video" or "crop my footage for Instagram". Not for
  writing the script or the hook line (`shorts-script`) or picking subreddits and writing the
  post (`reddit-post`).
---

# Clip cut

Turn one gameplay recording into the files each platform wants, from a single command. The agent
needs a footage path, an in and out point, and the hook line. It writes `.mp4` and `.gif` files
into `marketing/clips/` and prints each path, size and duration.

The script is `scripts/clip_cut.py`. It uses Python 3 (standard library only) and calls `ffmpeg`
and `ffprobe`. It is tested on Linux; macOS and Windows should work but their font paths are untested
(pass `--font` if auto-detection fails). Hook and end card text need ffmpeg's `drawtext` filter.
Some builds, such as the default Homebrew ffmpeg on macOS, leave it out; the script stops early
and says so. Then install a build with it or use `--end-card` with an image and no text. Text is drawn with ffmpeg `drawtext`, so no
image editor is needed.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **Footage path.** Ask the user for it. Check `marketing/`, `videos/`, `footage/` and `trailer/`
   folders for `.mp4`, `.mov` or `.mkv` files first, and offer what you find.
2. **In and out points.** Seconds (`12.5`) or `m:ss` (`1:02.5`). If the user has none, suggest one
   (step 1 below).
3. **Hook text.** From `marketing/shorts/<post-id>.md` if `shorts-script` wrote one. Otherwise ask.
   It must be true in the current build.
4. **Platforms.** Which of Shorts, TikTok, Reels, Reddit, X. This decides the shapes.
5. **End card.** An image (`press/`, `marketing/`, store capsule art) or a short line plus a short
   URL. Use the redirect from `docs/LINKS.md` ("Short links"), not a long UTM link.
6. **Post ID.** `YYYY-MM-DD-<platform>-<slug>` from `docs/LINKS.md`. Use the slug as the file name.

## Workflow

1. **Pick the moment.** Ask the user for the footage path. Suggest a cut where the hook is on screen
   within the first 1.5 to 3 seconds: the mechanic, the surprise, or the problem. Cut out logos,
   title cards, menus and slow intros. Aim for 10 to 60 seconds for vertical video and about 1 minute for X; keep Reddit clips to about 30 seconds. If the user is unsure, open the
   file with `ffprobe` to get its length, and propose two or three in and out pairs with one line
   on what each shows. Output: chosen `--start` and `--end`.

2. **Choose shapes per platform.** Output: the `--shape` list.

   | Platform | Shape | Notes |
   |---|---|---|
   | YouTube Shorts, TikTok, Instagram Reels | `9x16` (1080x1920) | One file for all three. |
   | Reddit, X feed | `4x5` (1080x1350) | Takes more feed height than 16:9. |
   | Reddit, X, YouTube, Bluesky | `16x9` (1920x1080) | Safe default for desktop. Use MP4, not GIF, on Bluesky. |
   | Reddit (GIF subs), Discord, press kit, Steam page | `gif` | Silent, looping, small. A press kit also wants 3 to 5 GIFs and 60 to 90 s of raw gameplay with no text or music (`--mute`, no `--hook`). |

3. **Choose the fit.** `--fit crop` (default) fills the frame and cuts the sides. Use `--crop-x PX`
   when the action is off centre (left edge of the window, in source pixels). Use `--fit blur`
   when HUD, subtitles or UI text would be cut: the whole picture sits on a blurred copy of itself.

4. **Run the script.** Draft only: the files stay local. Example for one Short and its Reddit
   versions:

   ```bash
   python3 skills/marketing/clip-cut/scripts/clip_cut.py footage/run3.mp4 \
     --start 41.2 --end 58 --shape 9x16 4x5 16x9 gif \
     --hook "This boat can fly. Hold jump." \
     --end-text "Wishlist on Steam" --end-url "yourgame.com/s/fly" \
     --speed 1.15 --out-dir marketing/clips --name 2026-11-26-yt-boat-fly
   ```

   Useful flags: `--hook-seconds 3`, `--end-card art.png`, `--end-seconds 3`, `--mute`,
   `--font path.ttf`, `--text-scale 0.9`, `--gif-width 720`, `--gif-max-mb 8`, `--fps 30`.
   Add `--dry-run` to print the ffmpeg commands without running them. Run `--help` for all.

   What it does: trims, forces a constant frame rate, crops or blur-fits, draws the hook in the
   safe area (on 9:16 it stays out of the right edge, the top 14% and the bottom 35%), draws the end card over
   the last seconds, applies the speed to video and audio, and normalises the audio to about
   -14 LUFS with the music kept. The GIF uses a generated palette, loops forever, and shrinks
   (width and frame rate) until it is under `--gif-max-mb`.

5. **Look at it.** Grab one frame from the hook and one from the end card, and show them to the
   user or ask them to watch the files:

   ```bash
   ffmpeg -v error -ss 1 -i marketing/clips/<name>-9x16.mp4 -frames:v 1 /tmp/hook.png
   ffmpeg -v error -sseof -1 -i marketing/clips/<name>-9x16.mp4 -frames:v 1 /tmp/end.png
   ```

   Check that the hook is readable, not cut, and not over the action.

6. **Hand over.** Tell the user which file goes where. Ask the user to upload and report back with
   the post URLs. Never upload or post. Add one row per post to `marketing/posts.csv` (see
   `docs/LINKS.md`) with `url` left empty.

7. **Verify (final check).** Run this and confirm each file has the right size, a duration near
   the expected one, `h264` plus `aac` for video (no audio if `--mute`), and `gif` for the GIF:

   ```bash
   for f in marketing/clips/<name>-*; do
     echo "$f: $(ffprobe -v error -show_entries stream=codec_name,width,height:format=duration -of csv=p=0 "$f" | tr '\n' ' ')"
   done
   ```

## Output

Files in `--out-dir` (default: current folder), named `<name>-<shape>.<ext>`:

```
marketing/clips/2026-11-26-yt-boat-fly-9x16.mp4   1080x1920  H.264 + AAC 48 kHz, 30 fps
marketing/clips/2026-11-26-yt-boat-fly-4x5.mp4    1080x1350
marketing/clips/2026-11-26-yt-boat-fly-16x9.mp4   1920x1080
marketing/clips/2026-11-26-yt-boat-fly-gif.gif    720 px wide, 15 fps, loops
```

The script prints one line per file: path, size, duration, audio or not, and MB. It exits 1 if
any shape failed, and 2 on bad arguments.

## Measure

Name each file after its post ID from `docs/LINKS.md` (`--name <post-id>`). One clip posted to
three platforms gets three post IDs with the same date and slug. The end card URL is the short
redirect that forwards to the UTM-tagged store link for that post ID.

A week after posting, read for each post ID: views, average view duration (or percent viewed),
and store visits and wishlists by `utm_content` (the post ID) in Steamworks UTM Analytics. Note which hook
and which shape held viewers. `marketing-retro` reads `marketing/posts.csv` for the rest.

## Gotchas

- **Text hidden under platform UI:** on 9:16 the right edge has buttons and the bottom has the
  caption, channel name and progress bar. The script keeps text out of those areas. Do not move
  key action or text there with `--crop-x` either. Check a frame before posting.
- **Reddit feeds usually autoplay muted:** the hook must work as text and picture alone. Never
  rely on voice for the first seconds there. Shorts, TikTok and Reels viewers often have sound on,
  so keep the music.
- **GIF too big:** sites cap GIF uploads and the caps change. Check the current limit on the
  upload page, then set `--gif-max-mb` under it. Long or busy clips (particles, water, camera
  pans) grow fast: cut to 3 to 8 seconds, or post MP4 instead.
- **Variable frame rate footage from OBS or phone captures:** audio drifts or frames stutter. The
  script forces a constant rate (`--fps 30`). If sync is still off, set OBS to constant frame rate
  or record to MKV and remux. The warning about variable frame rate is a hint, not a full check.
- **Music licensing:** your own or licensed music only. Credit the composer in the description
  if the licence asks for it. Stock or game-licensed tracks may not cover social posts; check the
  licence. Platform music libraries are added in the app, not here.
- **Hook not true any more:** the game changes. Recheck the hook against the current build before
  each post.
- **Text too long:** the script wraps and shrinks the font, but more than about 6 words on screen
  at once will not be read in 3 seconds. Split the line or shorten it.
- **No font found:** pass `--font /path/to/Bold.ttf`. On Linux install `fonts-dejavu-core`.
- **`ffmpeg` missing or without `drawtext`:** install a full build (`brew install ffmpeg`,
  `apt install ffmpeg`, `winget install ffmpeg`).
- **Speed:** above about 1.3 the music sounds wrong. Use `--mute` and add music in the app, or
  keep the speed low.

## Version notes

- Shapes: 9:16 1080x1920, 4:5 1080x1350, 16:9 1920x1080. These are the common upload sizes for
  the platforms above. Recheck if a platform changes its feed crop.
- YouTube Shorts accept a square or vertical video of up to 3 minutes (YouTube Help, Upload
  YouTube Shorts, read 2026-11-26: https://support.google.com/youtube/answer/12779649).
  The 10 to 60 second aim in step 1 is a habit for holding viewers, not a platform limit.
- Safe area: 9:16 keeps text out of the right 16%, the top 14% and the bottom 35%. The top and
  bottom come from Meta's Reels ad safe zone, the only published number; the right edge is a rule
  of thumb from the visible buttons. Recheck when a platform redesigns its player.
- Loudness: -14 LUFS integrated, -1.5 dBTP, one-pass `loudnorm`. Measured result on test clips
  was -14.0 to -14.1 LUFS.
- Tested with ffmpeg 6.1.1 and Python 3.13 on Linux.

Last verified 2026-11-26.
