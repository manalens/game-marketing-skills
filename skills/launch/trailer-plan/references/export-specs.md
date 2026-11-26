# Trailer export specs

As of 26 November 2026. `scripts/check_trailer.py` checks these.

## Steam (Valve, Steamworks Trailers page)

| Setting | Valve guidance | Script level |
|---|---|---|
| Container | .mov, .wmv or .mp4 | fail |
| Codec | H.264 video, AAC audio preferred | warn |
| Resolution | The highest you have, up to 1920 x 1080 | warn above 1920 x 1080 or below 1280 x 720 |
| Aspect ratio | 16:9 preferred, 4:3 accepted | fail otherwise |
| Frame rate | 30 / 29.97 or 60 / 59.94 fps | fail otherwise |
| Bit rate | 5,000 Kbps or more | fail below |
| Audio sample rate | 44 kHz or 48 kHz. Odd rates are a common cause of failed uploads | fail otherwise |
| Audio channels | Steam mixes down to stereo | not checked |
| Valve's Adobe Media Encoder preset | H.264 at 20 Mbps, AAC stereo at 192 Kbps | reference only |
| Custom thumbnail | A 1920 x 1080 frame from the video (.jpg or .png), unique content, no text. Steam otherwise makes a 600 x 380 poster and a 232 x 130 thumbnail | not checked |
| Length | No limit | only with `--max-seconds` |

Processing: Valve converts trailers first in, first out. Deleting and re-uploading puts the file at
the back of the queue. You cannot release the game while a trailer is still converting. Upload
days before you need it.

Microtrailer: Steam builds a 6-second loop from six 1-second clips taken from various points of
the first visible trailer, for quick-view places such as category hubs, sale pages and the home
page during seasonal sales. You cannot edit it. Black frames, menus and logos anywhere in the first
trailer can end up in it.

Order: the first two valid trailers play before the screenshots. Categories: Gameplay, General or
Cinematic, Teaser, Interview or Dev Diary. Each trailer can be limited to languages or countries.

## YouTube (YouTube Help, recommended upload encoding settings)

| Setting | Recommendation | Script level (`--profile youtube`) |
|---|---|---|
| Container | MP4 | warn |
| Video | H.264, progressive, High Profile, 4:2:0 | warn on codec |
| Audio | AAC-LC, 48 kHz | warn |
| Frame rate | The rate you recorded | warn on odd rates |
| Bit rate, 1080p SDR | 8 Mbps at 24 to 30 fps, 12 Mbps at 48 to 60 fps | warn below |
| Aspect ratio | 16:9 on a computer | warn |

## Social cuts (`--profile social --max-seconds 15` or `30`)

Same file rules as Steam, plus a hard length cap. Horizontal 16:9 for X, Bluesky and YouTube.
For vertical 9:16 and 4:5 versions, use `clip-cut`; this script checks 16:9 and 4:3 only.

## Loudness (our practice)

The script aims at -14 LUFS integrated, plus or minus 2, with true peak at or under -1 dBTP. That
matches `clip-cut`. Neither Valve nor this skill's sources set a loudness target for Steam; YouTube
turns loud uploads down on playback, so a hot master gains nothing. Treat the loudness check as a
warning, and trust your ears and a phone speaker test.

## Start of file

- Black frames from 0 s: fail. The trailer autoplays on the page and a Discovery Queue viewer may
  give it under 10 seconds (Valve).
- Silence of 1 s or more at the start: warning. Start sound with the first shot.
- A black gap of 1 s or more inside the trailer: warning, because of the microtrailer.
