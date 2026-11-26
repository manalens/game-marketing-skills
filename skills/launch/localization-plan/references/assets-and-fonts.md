# Assets with text, store page only, and fonts

## Store page only or full game

Valve treats store page localization and in-game localization as two separate types; you can
use either one alone (Steamworks, Localization and Languages).

| | Store page only | Full game |
|---|---|---|
| What | Short and long description, capsules and screenshots with text, trailer captions | All in-game text, plus the store page |
| Cost | Store words x rate (often a few hundred words) | All unique words x rate, plus testing |
| Steam language table | Tick nothing for that language | Tick Interface (and Subtitles or Full Audio if true) |
| Use it for | Testing demand: compare wishlists by country 4 weeks before and after | Languages with demand and payback |
| Be honest | Say at the top of the page that the game is not translated yet, and that the languages with the most wishlists come first (How To Market A Game, 5 Oct 2022) | Release a new language as an update for all customers, with an announcement (Valve) |

## Assets that need text changes

| Asset | When it needs work | Note |
|---|---|---|
| Short and long description | Every localized language | Enter each language from the language menu in the Steamworks text editor |
| Game name | Only if you localize the name | Valve keeps the base name as the search fallback |
| Capsules (header, small, main, vertical, library) | When the logo or any word is in the art | Valve lets you upload localized images; the small capsule must stay readable |
| Screenshots | When UI text is large or central | Retake in the target language after the game is translated |
| Trailer | Captions or on-screen text | Subtitled versions or a version without text; voice-over is rarely worth it for an indie game |
| Events and announcement art | Only for big beats | Optional |
| In-game textures with words | Signs, UI images, comics | Count these words by hand; the script cannot see them |

Base capsules may show only game art, the game name and an official subtitle (Valve graphical
asset rules, since 1 September 2022). A localized logo follows the same rule.

## Fonts

- Name the font for each script: Latin with accents (French, German, Polish, Czech, Turkish,
  Vietnamese), Cyrillic (Russian, Ukrainian, Bulgarian), CJK (Chinese, Japanese, Korean), Thai,
  Arabic (right to left: check your engine supports it before you promise it).
- A pixel or display font rarely has CJK glyphs. Plan a fallback for CJK and a matching weight.
- Noto Sans CJK (Google and Adobe, SIL Open Font License) is a common free fallback. Check the
  license of any font you ship.
- CJK fonts are large. Subset to the characters the game uses, or use a dynamic font atlas.
  Rerun the subset after each text update, or new characters show as boxes.
- Valve's Steam Deck guideline: the smallest on-screen character at least 9 pixels high at
  1280x800. Dense CJK glyphs need more than that to stay readable; test on the device or at
  that resolution.
- Engine notes: Godot uses font fallbacks on the theme or the font resource; Unity's TextMesh Pro
  uses fallback font assets (the Unity Localization package handles locales and string tables);
  Unreal uses composite fonts with sub-font ranges for CJK.
- German and French strings often run longer than English. Leave room in buttons, or test with a
  pseudo-localized build (each string padded and accented) before the vendor starts.
