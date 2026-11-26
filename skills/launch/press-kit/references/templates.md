# Press kit templates

Contents:

1. `press/factsheet.md`
2. `press/index.md` (presskit() order)
3. `press/assets.csv`
4. Folder layout
5. HTML instead of Markdown

Replace every value. The check script fails on anything left in square brackets, on TODO and TBD,
and on "Your Game".

## 1. press/factsheet.md

The check reads each field as `- **Label:** value`. Keep the labels exactly.

```markdown
# Pumpkin Patch: fact sheet

Last updated: 2026-11-26

- **Developer:** Gourd Games, Lyon, France
- **Publisher:** Self-published
- **Release date:** 12 March 2027 (or a window: "Q1 2027", "Spring 2027")
- **Platforms:** Windows, macOS, Steam Deck Verified pending
- **Price:** 14.99 USD (or "Free", or "To be announced")
- **Website:** https://pumpkinpatch.example/?utm_source=presskit&utm_medium=press&utm_campaign=launch
- **Steam:** https://store.steampowered.com/app/480/?utm_source=presskit&utm_medium=press&utm_campaign=launch&utm_content=factsheet
- **Socials:** Bluesky @gourdgames.bsky.social, YouTube @gourdgames, Discord invite link
- **Languages:** English, French, German
- **Genre:** Cozy farming sim
- **Press contact:** Ana Lopez, press@gourdgames.example
```

(The `.example` domains above are placeholders for this template; the script rejects
`example.com`. Use real addresses.)

## 2. press/index.md

Section order follows presskit() by Rami Ismail. The `##` names are what the check looks for.

```markdown
# Pumpkin Patch: press kit

Last updated: 2026-11-26. [Fact sheet][factsheet]. [Download everything (ZIP, 180 MB)][zip]

## Fact sheet

- Developer: Gourd Games, Lyon, France
- Release date: 12 March 2027
- Platforms: Windows, macOS
- Price: 14.99 USD
- Steam: https://store.steampowered.com/app/480/?utm_source=presskit&utm_medium=press&utm_campaign=launch&utm_content=index
- Press contact: Ana Lopez, press@gourdgames.example

## Description

### One sentence

A cozy farming game where your pumpkins grow legs and you herd them to market.

### One paragraph

(40 to 120 words: who you play, what you do, what is different, when it comes out.)

### Long

(150 to 500 words: the loop, the setting, the systems, the tone. Facts a writer can check.)

## Features

- 40 pumpkin breeds, each with its own walk and its own fear.
- Herd up to 200 pumpkins at once; they follow light, not you.
- (4 to 6 bullets, each a concrete thing a player does or sees, at most 25 words.)

## History

(How the game started, how long it took, the turning points. Dates.)

## Videos

- Trailer: https://www.youtube.com/watch?v=...
- Download the trailer (MP4, 1920x1080): [trailer.mp4][trailer]

## Images

- [Screenshots folder][shots]: 8 shots at 1920x1080, no text on them
- [GIFs][gifs]

## Logo and key art

- [Logo, transparent PNG][logo]
- [Key art with logo][keyart-logo], [key art without logo][keyart-clean]

## Awards

- Finalist, Example Festival 2026: https://festival.site/finalists-2026
(Or the single line "None yet." Never list an award without a link a writer can check.)

## Team

- Ana Lopez: design, code
- Ben Ortiz: art, animation

## About Gourd Games

(Two sentences: where you are, how many people, what you made before.)

## Streaming and monetisation

Gourd Games allows you to stream, record and publish videos of Pumpkin Patch, and to monetise them.
You do not need to ask first. The soundtrack is ours and safe to use.

## Keys

Press and creators: email press@gourdgames.example from the business address on your outlet or
channel page. Steam curators: we send copies through Curator Connect.

## Embargo

Reviews and videos: 10 March 2027, 17:00 UTC, the same for everyone.
(Or "No embargo: play and post when you like.")

## Contact

Ana Lopez, press@gourdgames.example

## Download

[Everything in one ZIP][zip]: fact sheet, screenshots, GIFs, key art, logos, trailer.

[factsheet]: factsheet.md
[zip]: pumpkin-patch-press-kit.zip
[trailer]: videos/trailer.mp4
[shots]: images/screenshots/
[gifs]: images/gifs/
[logo]: images/logo/logo.png
[keyart-logo]: images/keyart/keyart-logo.png
[keyart-clean]: images/keyart/keyart-clean.png
```

The links use reference style (`[text][label]` plus `[label]: path` at the end). Inline links
(text in brackets, then the path in parentheses) work as well; the check reads both.

## 3. press/assets.csv

One row per file. `with_logo` matters for key art; `text_free` must be `yes` for screenshots.

```csv
path,kind,with_logo,text_free,alt
images/screenshots/01-herd.png,screenshot,no,yes,A farmer leads 50 pumpkins across a bridge at dusk
images/keyart/keyart-logo.png,keyart,yes,no,Key art with the Pumpkin Patch logo
images/keyart/keyart-clean.png,keyart,no,yes,Key art without logo
images/logo/logo.png,logo,yes,no,Pumpkin Patch logo on transparent background
images/gifs/stampede.gif,gif,no,yes,Pumpkins stampede when the lantern goes out
videos/trailer.mp4,trailer,yes,no,
```

Minimum sizes the check uses (our practice unless a source is named):

| Kind | Minimum | Why |
|---|---|---|
| screenshot | 1920x1080 | Writers ask for full size with no watermark (Manalens press kit mistakes guide). |
| keyart | 1920x1080 | Used as an article header; 1200x675 crops from it. |
| logo | 1000 px wide, transparent | Writers place it on their own thumbnails. |
| icon | 256x256 | Our practice. |
| gif | 480 px wide | Our practice; a smaller GIF looks broken in an article. |
| trailer | 1280x720, MP4 | Warns below 1920x1080. Valve takes up to 1920x1080, H.264 with AAC. |

## 4. Folder layout

```
press/
  index.md
  factsheet.md
  assets.csv
  images/screenshots/  images/keyart/  images/logo/  images/gifs/
  videos/trailer.mp4
  <game>-press-kit.zip   (built by check_press_kit.py --zip)
```

## 5. HTML instead of Markdown

If the user hosts the kit as a web page, write `press/index.html` with the same `<h2>` headings
and `<h3>` description lengths. The check reads either file. A trailer can be an `<iframe>` from
YouTube. Or hand the text to the Manalens press kit builder, which exports a finished HTML page.
