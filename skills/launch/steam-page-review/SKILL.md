---
name: steam-page-review
description: >
  Reviews and drafts a Steam store page from the game's own repo: the short description (genre
  word, player verbs, about 300 characters, no time-based text), the About This Game section with
  headers and GIFs, the screenshot set (count, size, 16:9, gameplay first, no baked text), the
  trailer opening, supported languages, system requirements, Coming Soon timing and the reasons
  Valve rejects pages. Checks local screenshots and text with a script and writes
  launch/steam-page.md with the draft and a fix list. Use for "review my Steam page", "write my
  Steam short description", "why did Valve reject my store page" or "are my screenshots right for
  Steam". Not for capsule art (`steam-capsules`) or choosing and ordering tags (`steam-tags`).
---

# Steam page review

Draft and check a Steam store page before the person pastes it into Steamworks. The skill reads
the game's repo (README, design docs, press notes, `marketing/`), writes the text in the shape
Steam wants, checks the local screenshots and text with a script, and writes
`launch/steam-page.md`: the draft, a fix list in priority order, and the steps only the person
can do.

Shoppers see the page in this order: capsule, tags, short description, trailer, screenshots, then
the About section. A visitor from the Discovery Queue may give the page under 10 seconds (Valve,
Trailers doc). So the first two lines of text and the first four screenshots do most of the work.
Valve also reviews the page before it goes live, and a rejection costs days.

## Inputs

Look in the repo first. Ask only for what is missing.

1. **What the game is:** README, `docs/` or design docs (GDD, pitch, one-pager), press notes,
   `marketing/` (pitch lines, `marketing/rules.md` do-not-say list). Pull the genre, the hook,
   the core loop verbs and the content that is in the build today.
2. **Local store assets:** a folder of screenshots (look for `marketing/steam/`, `store/`,
   `press/screenshots/`), GIFs for the About section, the trailer file or its link.
3. **Live page, if any:** the store URL or App ID. If the page is public, grade it (Workflow
   step 9).
4. **State and dates:** Coming Soon, demo, Early Access or released; the planned release date;
   whether the Steamworks account is new (first game).
5. **Languages:** locale folders or string tables in the repo (`Localization/`, `locales/`,
   `*.po`, `*.csv` string tables). Note which have full audio.
6. **System requirements:** the lowest PC the team has tested on. Ask the user if no test notes
   exist. Never guess a spec.
7. **Tags:** `launch/steam-tags.md` if `steam-tags` ran. Otherwise note "tags not reviewed" and
   suggest that skill.

## With the Manalens MCP

It is connected when your tool list has `review_steam_page`. Any Manalens API key or OAuth
connection can call it. One call can send any mix of the inputs below; the result has a section
for each.

- **Live page:** `review_steam_page` with `{"app": "<App ID or store link>"}`. Each check has a
  `status`, `detail`, `fix` and `ours` (true when the rule is Manalens practice, not Valve's).
  Put each `fail` with `ours` false under **Blocks review**, other `fail` and `warn` checks under
  **Costs wishlists**, and use `fix` as the fix. List `could_not_check` as checks for the user.
- **Short description:** `review_steam_page` with `{"short_description": "<draft>"}`. Each failed
  check is a fix list line. Rewrite and call again until all pass.
- **Screenshots:** `review_steam_page` with `{"screenshots": [{"width": 1920, "height":
  1080, "file_type": "png"}, ...]}`, in store order. Send sizes only, not images. Read each size
  with `ffprobe -v error -show_entries stream=width,height -of csv=p=0 <file>`.

Still run the check script (Workflow step 7): it also checks About text and media sizes. Write the
grade's `score`, `band` and `checked` date in the Check section, with the `tool_url`.

## Without it

Run the check script on the local files (Workflow step 7). If the page is public, ask the user to
run the
[Steam page grader](https://manalens.dev/tools/steam-page-grader?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=steam_page_review)
on the live URL and report back the failed checks. To grade the page from this skill next time,
connect Manalens (14-day trial): https://docs.manalens.dev/mcp/overview

## Workflow

1. **Collect facts** into a short fact table at the top of `launch/steam-page.md`: name, genre in
   3 to 5 words, hook in one line, 3 to 5 player verbs, content at launch (levels, modes, hours
   only if measured), platforms, languages, state. Mark each fact with the file it came from. Any
   feature that is planned but not in the build goes on a separate "not at launch" list: Valve
   rejects pages that list content the game will not have at launch.
2. **Write the short description.** Formula: genre (and setting), then the hook, then 2 or 3
   player verbs in loop order. Write the 3 to 5 word label first; if you cannot, the positioning
   is the problem, not the text. Plain text, about 300 characters or fewer, no "Now available",
   no dates, no Early Access promises, no links, no line breaks. Write 3 versions, pick one, and
   save it alone to `launch/steam-short-description.txt` for the check.
3. **Write About This Game.** Short blocks with bold headers, each opening with what the player
   does, with a GIF slot between blocks. Lead with the core loop, then the systems, then the
   content at launch, then what is different. No jargon a newcomer to the genre would miss. No
   links, no fake Steam buttons, no ads for other games. If the game is in Early Access, add
   Valve's Early Access answers in their own field, not here. Template:
   [references/page-rules.md](references/page-rules.md#about-this-game).
4. **Plan the screenshots.** List the files in store order with one line each: what it shows and
   its job. First 4 = core action, second system, reward or progress, variety (the store hover
   shows the first 4, not the trailer). Gameplay with the HUD visible. No baked-in text, logos,
   awards or feature captions. At least 5 categorized as gameplay. Mark at least 4 "suitable for
   all ages" when the content allows.
5. **Review the trailer opening.** Ask the user for the first 10 seconds as a shot list, or read
   it from the trailer edit notes. Fail it if the first seconds are logos, a studio card or a slow
   pan. Steam builds the 6-second microtrailer from six 1-second clips of the first trailer, so
   menus and logos there make a weak loop. Gameplay trailer first; at most one or two trailers
   before the screenshots.
6. **Languages, requirements and timing.** List supported languages (interface, full audio,
   subtitles) only where the build has them. Draft minimum requirements per platform from tested
   hardware, with the OS line starting at Windows 10. Work out the timing plan: page review at
   least 7 business days before it must be live, a public Coming Soon page at least 2 weeks before
   release, a first game waits 21 days after the app fee, an exact release date 60 or more days
   ahead for the Personal Calendar page. See
   [references/page-rules.md](references/page-rules.md#timing).
7. **Run the check** (draft only, nothing is uploaded):

   ```
   python3 scripts/check_store_assets.py --screenshots <folder> \
     --short launch/steam-short-description.txt --about launch/steam-about.txt --about-media <gif folder>
   ```

   It fails on fewer than 5 usable screenshots, any under 1920x1080 or not 16:9, odd file types,
   a short description over 300 characters, time-based text, links, markup, and description media
   over 5 MB each or 15 MB in total. It warns on missing genre word or verb. It needs `ffprobe`
   for image sizes and exits 2 if it is missing. Paste its summary into the fix list.
8. **Write the fix list** in `launch/steam-page.md`, three levels: **Blocks review** (breaks a
   Valve rule; see the rejection table in
   [references/page-rules.md](references/page-rules.md#why-valve-rejects-a-page)), **Costs
   wishlists** (weak opening, no genre word, menus in the first 4), **Polish**. One line per item:
   what, where, the fix.
9. **Grade the live page**, if it is public: `review_steam_page` with `app` (With the Manalens MCP), or the
   grader link (Without it). Merge the failed checks into the fix list. Before submitting for
   review, ask the user to go through the
   [Steam page review check](https://manalens.dev/tools/steam-page-review-check?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=steam_page_review).
10. **Stop at the draft.** Ask the user to paste the text into Steamworks, upload the files, mark
   the page ready for review themselves, and report back Valve's answer. If Valve rejected the
   page, paste the reviewer's note into the fix list and map each point to a rule.

## Output

`launch/steam-page.md`, plus `launch/steam-short-description.txt` (and `launch/steam-about.txt`
when the About text is long enough to check):

```markdown
# Steam page: <game>  (state: Coming Soon, target release 2027-05-12)

## Facts (source)
| Fact | Value | From |
|---|---|---|
| Label | turn-based tactics roguelike | README.md |
| Verbs | command, trade, defend | docs/gdd.md |
| Not at launch | online co-op | docs/roadmap.md |

## Short description (191 characters)
A turn-based tactics roguelike set in a sinking lighthouse town. Command three keepers, ...

## About This Game
**Hold the light for 12 nights** ... [GIF: lamp defense, 6 s]

## Screenshots (store order)
| # | File | Shows | Job | Check |
|---|---|---|---|---|
| 1 | shot-01.png | three keepers fight on the pier, HUD on | core action | pass |

## Trailer, languages, requirements, timing
...

## Fix list
### Blocks review
- [ ] About lists online co-op; not in the build. Remove until it ships.
### Costs wishlists
- [ ] Trailer opens on a 4 s studio logo. Start on the pier fight.
### Polish
- [ ] Only 3 screenshots marked suitable for all ages.

## Check
check_store_assets.py: 0 failed, 1 warning (2026-11-26)
```

## Measure

Valve's traffic report in Steamworks shows visits and wishlists for the page. Write the date of
each page change in `launch/steam-page.md` ("Changes" list), then compare the page's visit to
wishlist rate for the 14 days before and after, with no festival or big post in either window.
A Manalens survey of 56 festival games (2020) put the median page view to wishlist rate at 8.9%;
use it as a rough floor, not a target. Every link you post to the page uses the UTM tags in
[docs/LINKS.md](../../../docs/LINKS.md), so `marketing-retro` can split page conversion by source.

## Gotchas

- **300 is not Valve's number:** Valve says "a few hundred characters". 300 is where the
  Steamworks editor stops by community report. The editor's counter wins.
- **Two Valve pages disagree on screenshots:** the assets doc says gameplay only; the
  3 November 2026 announcement allows menus, concept art and in-game cinematics if categorized
  correctly, with at least 5 as gameplay. Follow the newer rule, and keep non-gameplay out of the
  first 4 anyway.
- **Feature on the page, not in the build:** the most common avoidable rejection. Also covers
  controller support, languages and platforms ticked in Steamworks.
- **Text in images:** a GIF or screenshot with words needs a new version per language, and
  marketing text in screenshots breaks Valve's rule. Keep images textless.
- **Date regex false positives:** the script flags "May 3" even in "you may 3x your score". Read
  what it matched before you rewrite.
- **Delay inside the last 2 weeks:** moving the date by more than 24 hours then drops the game off
  the Personal Calendar until release. Set a date you can keep.
- **Trailer queue:** Valve transcodes trailers first in, first out, and a re-upload goes to the
  back. You cannot release while one is still converting. Upload early.
- **The grader cannot see everything:** the grader and `review_steam_page` cannot judge capsule
  readability, screenshot content or the trailer's opening. The local check and your eyes cover those.

## Version notes

- Screenshots: at least 5, 1920x1080 or larger, 16:9, at least 5 categorized as gameplay (Valve
  assets doc and announcement of 3 November 2026).
- Description images under 5 MB each, 15 MB in total; no links; no time-based text in the short
  description (Valve, Store Page Written Description, read 19 November 2026).
- Review: submit 7 business days ahead; build review took up to 12 business days on
  3 November 2026. First game: 21 days after the app fee, Coming Soon for 2 weeks.
- Personal Calendar left Steam Labs on 23 October 2026; exact date 60+ days ahead.
- Manalens MCP game marketing tools (`review_steam_page`), checked 2026-11-26: new, so names can still change. Match on the
  tool list.
- Full list with sources: [references/sources.md](references/sources.md).

Last verified 2026-11-26.
