---
name: localization-plan
description: >
  Decides which languages to localize an indie game into, and in what order: Steam language
  shares and review languages of comparable games, word counts from the game's own string files
  (Godot, Unity, Unreal, gettext .po, JSON), cost per language, store page only or full game,
  which capsules, screenshots and trailers need new text, CJK fonts, and a brief for the
  translation vendor. Writes launch/localization.md, and checks returned translation files for
  missing keys, untranslated strings and broken placeholders. Use for "which languages should I
  translate my game into", "how many words is my game", "how much will localization cost" or
  "check my translation files for missing strings". Not for writing or reviewing the store page
  text itself (`steam-page-review`).
---

# Localization plan

Pick the languages that pay back, in order, and give the translator what they need. Count the
words in the repo, price each language, decide store page only or full game, list every asset
that has text, and write `launch/localization.md`. When translations come back, check them.

Valve says over 60% of Steam users run Steam in a language other than English, that Steam has
full official support for 29 languages, and that the less a language looks like English, the
higher the expected return. Valve also writes that Steam favors localized products, judged by the
game's own language settings, not the store page. A store page translation is
cheap and doubles as a test: translate the page first, watch wishlists by country, then translate
the game for the languages that respond.

## Inputs

Find these in the repo first (string files, README, store page text in `launch/` or
`marketing/`, `launch/pricing.md`). Ask only for what is missing.

1. **String files and source language.** The script finds them (below). Also ask where text
   lives outside them: hardcoded strings, images, subtitles, voice.
2. **Genre and 3 to 10 comparable games** (Steam App IDs), for review languages.
3. **Price and a sales or wishlist estimate** for English-language players, for payback.
4. **Store page text**, for the store-page-only cost.
5. **Assets with text:** capsules with a logo, screenshots with UI, trailer captions, the key art.
6. **Engine and fonts** used for UI text.
7. **Budget and deadline**, and whether voice is in scope (usually not for an indie game).

## Workflow

1. **Count the words.** From the game repo (`<skill>` is this skill's folder):
   `python3 <skill>/scripts/count_words.py count . --store-text launch/store-page.md`.
   It reads gettext `.po`/`.pot` (Godot, Unreal and plain gettext), Godot translation CSV,
   Unity Localization CSV exports, Unreal string table CSV and JSON key/value files. It skips
   keys, placeholders (`{name}`, `{0}`, `%s`, `%1$d`, `{{var}}`) and markup (`<b>`, `[color]`,
   `</>`), counts CJK characters one by one, and prices unique strings. Then grep for text the
   script cannot see: hardcoded strings in code, text baked into images. Add those words by hand.
2. **Rank languages by demand.** Use two signals, in
   [references/languages.md](references/languages.md):
   - Steam survey share (October 2026): English 39.04%, Simplified Chinese 21.98%, Russian
     10.14%, Spanish (Spain) 4.83%, Portuguese (Brazil) 4.46%, German 2.89%, Japanese 2.47%,
     French 2.41%, Polish 1.73%, Korean 1.36%. The survey swings month to month.
   - Genre fit: the share of each comp's Steam reviews in each language, median across comps.
     If you can make web requests, ask Steam's public reviews API per comp and language (method
     in `references/languages.md`); otherwise ask the user or use the tool linked in step 9.
     Rule of thumb: a median share of 5% or more, full localization; 1% to 5%, store page only;
     under 1%, skip for now.
3. **Price each language.** Cost = unique words x rate. The script's default rates are the
   midpoints of a published vendor price list (Allcorrect Games, 5 March 2026) in USD; replace
   them with real quotes (`--rates schinese=0.11,japanese=0.14`). Payback, using the Manalens
   planner's assumption that a translated game sells to each language's users at the English
   rate: extra copies = English copies x language share / 39.04; copies to pay back = cost /
   (price x 0.7). Show the arithmetic.
4. **Decide the tier and order** for each language: full game, store page only, or later. Put
   languages with a payback multiple of 1 or more and a genre share of 5% or more first. When the
   numbers are close, prefer languages least like English (Valve's guidance), such as
   Simplified Chinese, Japanese and Korean. Write the
   order as waves: wave 1 at launch, wave 2 as a post-launch update.
5. **List assets that need text changes** (see [references/assets-and-fonts.md](references/assets-and-fonts.md)):
   store description and short description, capsules with the logo (Valve allows a localized
   game name and localized images), screenshots with UI text, trailer captions or subtitles,
   the game name if you localize it, in-game images with words, and the Steam language table
   (Interface, Full Audio, Subtitles). Tick only what is done.
6. **Check fonts and length.** For each target script (CJK, Cyrillic, Thai, Arabic), name the
   font and confirm it has the glyphs. For CJK, plan a fallback font and its file size, and test
   the smallest text at 1280x800 for Steam Deck. Before any translation, turn on
   pseudolocalization (in Godot, an `expansion_ratio` of 0.3 makes each string 30% longer) and
   fix overflows and hard-coded strings. See
   [references/assets-and-fonts.md](references/assets-and-fonts.md#pseudolocalization-before-any-translation).
7. **Write the vendor brief** from [references/vendor-brief.md](references/vendor-brief.md):
   word counts per file, file formats to return, glossary, character list, placeholders and
   tags that must stay, length limits, context screenshots, tone, and the deadline. If the team
   drafts with an AI tool, use the context table, prompt and review order in the same file
   ([AI or machine translation drafts](references/vendor-brief.md#ai-or-machine-translation-drafts)):
   glossary, context, plurals, placeholders and length limits go in; flagged lines, a script
   check and a native speaker who plays the build come after.
8. **Write `launch/localization.md`** (shape below).
9. **Hand off.** For live review-language shares of comps, point to
   [Steam reviews by language](https://manalens.dev/tools/steam-review-languages?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=localization_plan).
   For cost and payback with charts, the
   [Steam localization planner](https://manalens.dev/tools/steam-localization-planner?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=localization_plan).
   Never send files to a vendor or buy anything: ask the user to send the brief and report back.
10. **Check returned translations:** `python3 <skill>/scripts/count_words.py check .` (or
    `--targets fr,de`). It fails on missing keys, empty strings and placeholder mismatches, and
    warns on strings equal to the source, markup changes, fuzzy `.po` entries and stale keys.
    Fix every FAIL before the build ships; send each WARN to the translator to confirm.

## Output

`launch/localization.md`:

```markdown
# Localization plan: <game>

- Source language: English. Words: 18,400 total, 15,900 unique (count_words.py, <date>).
- Store page: 640 words. Wave 1 (launch): schinese, japanese, german. Wave 2: ...

## Words by file
| File | Format | Strings | Words |

## Languages
| Language | Steam share | Comps' review share | Tier | Rate | Game cost | Store cost | Copies to pay back | Wave |

## Why this order
## Store page only languages (and the note on the page)
## Assets with text
| Asset | Text in it | Languages | Owner |
## Fonts
## Vendor brief (or a link to launch/localization-brief.md)
## Open questions
```

## Measure

Before a store page translation goes live, note wishlist adds per day by country for 4 weeks.
Compare the 4 weeks after. For a game language, compare units and reviews in that language for
the 6 months before and after, against the game's overall trend. Tag the announcement post for
each new language with `utm_campaign=update` and the post ID in `utm_content`
([docs/LINKS.md](../../../docs/LINKS.md)), so `marketing-retro` can see it.

## Gotchas

- **Language is not geography:** players pick their Steam language. A Portuguese (Brazil) player
  may live anywhere. Read reviews by language, wishlists by country, and keep both.
- **Strings the script cannot see:** hardcoded UI text, text in textures, subtitles in video
  files. Grep the code for quoted text in UI calls before you send a word count to a vendor.
- **Concatenated strings:** `"You have " + n + " coins"` cannot be translated well. Turn it into
  one string with a placeholder first.
- **Placeholders renamed:** a translator who writes `{{ville}}` for `{{town}}` breaks the game.
  The check catches it; say in the brief that placeholders never change.
- **Store page promises:** a page in a language the game does not support yet must say so at the
  top. Do not tick Interface for a language that only has a store page.
- **CJK fonts are big:** a full CJK font can add tens of megabytes. Subset it or use a dynamic
  atlas, and test that no glyph shows as a box.
- **One survey month:** Simplified Chinese moved 9.41 points in October 2026. Look at a few
  months before you rank two close languages.
- **AI translation is a draft:** a word such as Close can be a button or a distance, and AI makes
  the same context mistakes as a person without context, only faster. Send context with every
  batch and have a native speaker play the build.
- **Disclose AI translation on Steam:** the Content Survey covers AI content that ships with the
  game and that players consume, and names localization. Tools that only speed up your own work
  are not its focus. Valve reviews AI content like any other, so a wrong or offensive line is
  yours to fix.
- **English fields left blank:** English is the store's default and only fallback language, so
  its fields cannot be empty, even if the game launches in another language first.

## Version notes

- Steam language shares: Steam Hardware and Software Survey, October 2026, read 2026-11-23.
- Default rates: Allcorrect Games price list dated 5 March 2026, EUR converted at the ECB rate
  of 23 November 2026 (1.0939). Quotes vary a lot by vendor and text type.
- Tier thresholds (5% and 1% of comps' reviews) and the payback assumption are rules of thumb
  from the Manalens tools, not Valve rules.
- Valve localization rules (store page and game localized separately, localized name and
  images, release a language as an update for all customers): Steamworks Localization and
  Languages docs, read 2026-11-18. 29 fully supported languages, QA by a second company or by
  players, and "Steam favors products that are localized": same page, read 2026-11-26.
- AI localization counts in the Steam Content Survey; English is the only fallback for store
  fields: Steamworks Content Survey and Store Page Written Description, read 2026-11-26.
- Pseudolocalization (`expansion_ratio`) and PO template regeneration: Godot 4.7 docs, read
  2026-11-26.
- Sources: [references/sources.md](references/sources.md).

Last verified 2026-11-26.
