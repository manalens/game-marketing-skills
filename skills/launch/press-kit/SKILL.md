---
name: press-kit
description: >
  Writes and assembles an indie game press kit from the game's repo: a fact sheet (developer,
  publisher, release date or window, platforms, price, website, socials, press contact),
  descriptions in three lengths, 4 to 6 concrete features, history, team, verifiable awards,
  trailer embed and MP4, 6 to 12 clean screenshots, key art with and without logo, a transparent
  logo, GIFs, a streaming and monetisation line, a key request route, embargo details and one
  ZIP, in a press/ folder with an asset manifest, then checks it. Use for "make a press kit for my
  game", "write my game's fact sheet" or "what goes in an indie press kit". Not for pitch emails,
  contact lists or key handling (`press-outreach`).
---

# Press kit

Build the one page a writer or creator needs to cover the game without emailing you: facts,
text in three lengths, images they can use, the trailer, and how to get a key. Writes `press/`:
`index.md` (or `index.html`), `factsheet.md`, `assets.csv` and one ZIP of everything.

Writers are short of time. In a 2024 Big Games Machine survey of over 150 games journalists, 62%
got 11 to 50 pitches a day (claim, via the Manalens press kit mistakes guide). A kit that forces a
follow-up question often loses to the next pitch. So every item below answers a question before it
is asked.

## Inputs

Look in the repo first: `README.md`, design docs, `marketing/`, store page text, `CREDITS`,
`assets/` or `Art/` folders, builds and trailer exports. Ask only for what is missing.

1. **Facts:** developer, publisher (or "Self-published"), studio location, release date or window,
   platforms, price (or "Free", or "To be announced"), website, socials, press contact email.
2. **The game:** the one-line pitch, the loop, what is different. From the README or design doc.
3. **History and team:** from git history (first commit date), credits, the user.
4. **Awards and press quotes:** only ones with a public link. Ask the user for the URL of each.
5. **Media:** trailer (YouTube or Vimeo link plus the MP4 file), screenshots, key art (both
   versions), logo PNG, GIFs. Ask where the source files live.
6. **Key route and embargo:** who answers key requests, and the embargo date, time and time zone,
   or "no embargo".
7. **The beat:** the `utm_campaign` value for this round (`announce`, `demo`, `nextfest`,
   `launch`), from [docs/LINKS.md](../../../docs/LINKS.md).

## Workflow

1. **Collect the facts** above into `press/factsheet.md` (shape in
   [references/templates.md](references/templates.md)). Add `Last updated: YYYY-MM-DD` at the top.
   A wrong date in a kit becomes a wrong date in an article.
2. **Write the three descriptions** from the repo, in plain words, with only facts true in the
   current build:
   - one sentence, at most 240 characters (the Manalens builder's limit): the line a writer pastes
     into a headline or a list;
   - one paragraph, 40 to 120 words;
   - long, 150 to 500 words.
   The word ranges are our practice. Say what the player does before how it feels.
3. **Write 4 to 6 features.** Each is concrete and checkable: a number, a verb, a thing on screen
   ("Herd up to 200 pumpkins at once"), not "stunning visuals" or "deep gameplay". At most 25 words.
4. **Write history, team and about.** History: how it started, how long, turning points, with
   dates. Team: name and role. About: two sentences on the studio.
5. **Awards:** list only awards and selections with a public page, each with its link. If there
   are none, write "None yet." Never pad this section.
6. **Media.** Ask the user to export, or find in the repo:
   - 6 to 12 screenshots at 1920x1080 or more, PNG, with no text, logo or watermark baked in. Mix
     gameplay with the interface and clean art shots. Writers want shots that show how it plays.
   - Key art at full size, once with the logo and once without. Writers crop logos off key art.
   - The logo as a PNG with a transparent background (a light and a dark version if one fails on
     either background).
   - 1 to 3 GIFs of the core loop.
   - The trailer: the YouTube or Vimeo link for the embed, and the MP4 for download. Gameplay first.
   Put files under `press/images/` and `press/videos/`. Do not upscale small images; ask for a new
   capture instead. `clip-cut` can make the GIFs from a clip.
7. **Write `press/assets.csv`**: one row per file with kind, `with_logo`, `text_free` and alt text.
8. **Write the permission, key and embargo lines.**
   - Streaming and monetisation, by default: "<Developer> allows you to stream, record and publish
     videos of <Game>, and to monetise them. You do not need to ask first." Add a line on music
     if any track is licensed. Creators check this before they cover a game.
   - Keys: one route (an email address or form), and say requests must come from the business
     email on the outlet or channel page. Curators get copies through Curator Connect.
   - Embargo: date, time and time zone, the same for everyone, or "No embargo".
9. **Assemble `press/index.md`** in the presskit() order by Rami Ismail (template in
   [references/templates.md](references/templates.md)). For a web page, write `index.html` with
   the same `<h2>` headings instead.
10. **Tag every link to the game.** Steam, itch.io and website links get
    `utm_source=presskit&utm_medium=press&utm_campaign=<beat>&utm_content=<page>` (for example
    `index` or `factsheet`). Social links and the trailer embed need no tags.
11. **Build the ZIP and check:**
    ```
    python3 scripts/check_press_kit.py press --zip <game>-press-kit
    ```
    It builds the ZIP from every file in `press/`, then fails on a missing section or fact,
    descriptions outside their limits, not 4 to 6 features, awards without links, leftover
    placeholders (TODO, TBD, `[Your name]`), untagged game links, missing or small assets
    (ffprobe), no transparent logo, no clean key art, no MP4, or no ZIP link. Fix and rerun until it
    prints `ok`. It needs ffmpeg; `--no-assets` checks only the text.
12. **Hand off.** Ask the user to host the folder (their site, itch.io HTML project, GitHub Pages,
    Netlify) and report back the URL. If they want a styled page fast, they can paste the fact
    sheet and text into the
    [Manalens press kit builder](https://manalens.dev/tools/press-kit-builder?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=press-kit),
    which imports the Steam page and exports one HTML page plus image ZIPs. Read the
    [press kit mistakes list](https://manalens.dev/blog/indie-game-press-kit-mistakes) once as a
    last pass. For pitching the kit, use `press-outreach`.

## Output

```
press/
  index.md            presskit() order, the 14 sections the check reads
  factsheet.md        - **Label:** value lines, Last updated date
  assets.csv          path,kind,with_logo,text_free,alt
  images/ videos/
  <game>-press-kit.zip
```

Then tell the user: the kit's sections, the asset count, what is still missing, and the hosting
step.

## Measure

Each link to the game in the kit carries `utm_source=presskit` and the beat in `utm_campaign`
(docs/LINKS.md). In Steamworks UTM Analytics, the `presskit` rows show visits and wishlists from
people who opened the kit and clicked through. Expect small numbers: most coverage traffic comes
through the article's own link, which `press-outreach` tags per contact. Also count ZIP and
trailer downloads in the host's analytics if it has any. `marketing-retro` reads the UTM rows a
week after each beat.

## Gotchas

- **Kit behind a sign-up or a cloud folder that asks for access:** writers leave. Public page,
  direct file links, one ZIP.
- **Old dates and prices:** update the fact sheet, the Last updated line and the ZIP the same day
  the Steam page changes, then rerun the check (it rebuilds the ZIP).
- **Text in screenshots:** marketing shots with captions or logos cannot be used as article
  images. Keep those for social posts; the kit gets clean captures.
- **Logo on a white box:** a JPEG or an RGB PNG has no transparency. The check reads the pixel
  format with ffprobe and fails it.
- **Awards that cannot be checked:** "award-winning" with no link reads as padding. Link the
  festival page or drop it.
- **Vague features:** "a rich story" tells a writer nothing. Name the number, the verb or the
  thing on screen.
- **Huge ZIP:** a 2 GB ZIP with raw 4K captures puts off writers on slow links. Keep the trailer
  at 1080p and screenshots as PNG at 1920x1080 to 2560x1440.
- **Placeholders that look real:** an embargo line with no time zone or a price of "TBD" gets
  printed as is. The check fails both.
- **Mismatched tags:** Manalens tools use other `utm_source` values for press (`press`, or
  `presskit`). Pick one for the whole kit and keep it.

## Version notes

- Kit contents (fact sheet, three description lengths, 4 to 6 features, trailer embed plus MP4,
  6 to 12 clean screenshots, key art with and without logo, transparent logo, verifiable awards,
  key route, embargo, one ZIP): getplaytests.dev guide (12 Nov 2026) and presskit() by Rami
  Ismail (dopresskit.com). See [references/sources.md](references/sources.md).
- 240-character one-sentence limit, the 9-item checklist and the default streaming line: Manalens
  press kit builder source, checked 2026-11-26.
- Screenshot minimum 1920x1080 and the Last updated line: Manalens press kit mistakes guide
  (practice, citing writers). Trailer: Valve accepts up to 1920x1080, H.264 and AAC preferred
  (Steamworks trailer docs).
- Description word ranges, logo, icon and GIF minimums are our practice.

Last verified 2026-11-26.
