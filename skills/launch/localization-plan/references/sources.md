# Sources

## Valve (primary)

- Steamworks, Localization and Languages: https://partner.steamgames.com/doc/store/localization
  (read 2026-11-18): over 60% of users run Steam in another language; less like English, higher
  return; store page and game localized separately; localized name and images; release new
  languages as an update for all customers; language is not geography.
- Steamworks, Localization and Languages, read again 2026-11-26 (via the Manalens guide "AI game
  localization: what to translate and what to check"): full official support for 29 languages;
  localization QA by a second company or by players through a feedback forum; "Steam favors
  products that are localized", judged by in-game language settings.
- Steamworks, Content Survey: https://partner.steamgames.com/doc/gettingstarted/contentsurvey
  (read 2026-11-26): AI content that ships with the game and that players consume, localization
  included; efficiency tools are not the focus; AI content reviewed like other content.
- Steamworks, Store Page Written Description:
  https://partner.steamgames.com/doc/store/page/description (read 2026-11-24, via the Manalens
  guide "Using AI to write Steam store copy"): English is the default and only fallback language.
- Steamworks, Events and Announcements Tools:
  https://partner.steamgames.com/doc/marketing/event_tools (read 2026-11-26): missing languages
  fall back to English; all translations can be uploaded as a CSV.
- Steam Hardware and Software Survey, October 2026, Language:
  https://store.steampowered.com/hwsurvey/?platform=combined (read 2026-11-23)
- Steamworks, IUserReviewsService (GetAppReviews, language filter):
  https://partner.steamgames.com/doc/webapi/IUserReviewsService
- Steamworks, Graphical asset rules (since 1 September 2022):
  https://partner.steamgames.com/doc/store/assets/rules
- Valve, revenue share tiers, 30 November 2018:
  https://steamcommunity.com/groups/steamworks/announcements/detail/1697191267930157838

## Engines

- Godot documentation, Localization using gettext (PO files), Godot 4.7:
  https://docs.godotengine.org/en/stable/tutorials/i18n/localization_using_gettext.html
  (read 2026-11-26): msgctxt, msgid_plural, translator comments, regenerate the template.
- Godot documentation, Pseudolocalization, Godot 4.7:
  https://docs.godotengine.org/en/stable/tutorials/i18n/pseudolocalization.html (read
  2026-11-26): expansion_ratio, accents, double vowels.

## Rates and studies

- Allcorrect Games, "Localization pricing", page dated 5 March 2026:
  https://allcorrectgames.com/localization-pricing/
- European Central Bank, euro reference rates, USD rate of 23 November 2026 (1.0939):
  https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
- Chris Zukowski, "Should I translate my Steam page?", How To Market A Game, 5 October 2022:
  https://howtomarketagame.com/2022/10/05/should-i-translate-my-steam-page-and-other-effects-on-steam-traffic/
- Squeaky Wheel, Academia: School Simulator localization case study, Game Developer,
  1 December 2021 (as quoted in the Manalens localization guide).
- Noto CJK fonts (SIL Open Font License): https://github.com/notofonts/noto-cjk

## Manalens content used (read 2026-11-26)

- `localization-planner.ts`: survey shares, rate groups, EUR to USD rate, payback method,
  default target languages.
- `steam-review-languages.ts`: review language codes, the 5% and 1% thresholds, the
  roguelike deckbuilder example counts (23 November 2026).
- `guides/wishlists-2.ts` (Steam page localization guide): store page test, survey numbers,
  the 2022 wishlist survey, the Academia case.
- `article-tldr.ts`: Steam Deck smallest font guideline (9 pixels at 1280x800).
- `guides/ai-game-dev-3.ts` ("AI game localization", 26 November 2026): the AI context table,
  the translation prompt, the review order and the blind two-tool test are Manalens practice.
