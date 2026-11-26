# Languages: demand, genre fit, cost and payback

Contents:
1. Steam survey shares (October 2026)
2. Review languages of comparable games
3. Example: roguelike deckbuilders
4. Default rates per word
5. Payback arithmetic
6. One real case

## 1. Steam survey shares

Steam Hardware and Software Survey, October 2026, Language table (all platforms), share of
respondents, read 2026-11-23. The change is from September 2026, in points.

| Steam id | Language | Share | Change |
|---|---|---|---|
| english | English | 39.04% | +4.84 |
| schinese | Simplified Chinese | 21.98% | -9.41 |
| russian | Russian | 10.14% | +1.09 |
| spanish | Spanish (Spain) | 4.83% | +0.75 |
| brazilian | Portuguese (Brazil) | 4.46% | +0.76 |
| german | German | 2.89% | +0.41 |
| japanese | Japanese | 2.47% | +0.06 |
| french | French | 2.41% | +0.33 |
| polish | Polish | 1.73% | +0.24 |
| korean | Korean | 1.36% | -0.01 |
| turkish | Turkish | 1.35% | +0.26 |
| tchinese | Traditional Chinese | 1.30% | +0.03 |
| latam | Spanish (Latin America) | 0.89% | +0.14 |
| thai | Thai | 0.83% | +0.01 |
| ukrainian | Ukrainian | 0.73% | +0.07 |
| italian | Italian | 0.64% | +0.08 |
| czech | Czech | 0.58% | +0.08 |
| hungarian | Hungarian | 0.39% | +0.07 |
| portuguese | Portuguese (Portugal) | 0.36% | +0.05 |
| swedish, dutch | Swedish, Dutch | 0.27% each | +0.04 |

Smaller languages (Danish, Vietnamese, Indonesian, Finnish, Romanian, Norwegian, Greek,
Bulgarian, Arabic, Malay) are each under 0.25%. `count_words.py` holds the full list.

Valve (Localization and Languages): over 60% of Steam users use Steam in a language other than
English; the less a language looks like English, the higher the expected return. How To Market
A Game (5 October 2022) reports that Valve recommends Japanese, Korean and Chinese first.

## 2. Review languages of comparable games

The survey says who is on Steam. Reviews of similar games say who plays your genre. Steam's
public reviews API returns the exact review total per language:

```
https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/?input_json={"appid":<APPID>,"num_per_page":1,"languages":["<language>"]}
```

Read `response.query_summary.total_reviews`. Use `"all"` for the total, then each language id:
`english, schinese, tchinese, russian, spanish, latam, brazilian, german, french, japanese,
koreana, polish, turkish` (reviews use `koreana` for Korean). URL-encode the JSON. Only send
numeric App IDs. Counts are Steam purchases (the API default).

Share of a comp = reviews in the language / reviews in all languages x 100. Take the median
across 3 to 10 comps; leave out a comp whose count did not come back rather than counting zero.

Rule of thumb (Manalens review languages tool): median share 5% or more, full localization;
1% to 5%, store page only; under 1%, skip for now.

## 3. Example: roguelike deckbuilders

Review totals by language from Valve's Web API on 23 November 2026:

| Game | All | English | Simpl. Chinese | Russian | Spanish | Brazilian | German | French | Japanese | Korean |
|---|---|---|---|---|---|---|---|---|---|---|
| Balatro | 163,266 | 105,877 | 20,034 | 4,665 | 9,811 | 4,371 | 2,533 | 3,387 | 883 | 2,240 |
| Slay the Spire | 193,496 | 77,538 | 76,664 | 5,197 | 4,488 | 2,551 | 2,555 | 3,029 | 2,062 | 9,670 |
| Inscryption | 136,619 | 77,277 | 24,285 | 9,054 | 3,981 | 5,115 | 2,432 | 2,000 | 1,478 | 3,559 |
| Monster Train | 19,982 | 12,267 | 4,346 | 584 | 190 | 268 | 481 | 405 | 106 | 238 |

Simplified Chinese is far above 5% for all four (12% to 40%), so it is a full localization
language in this genre. Japanese sits between 0.5% and 1.1% (median about 0.8%), so this genre
data says "skip for now" for Japanese, even though Valve's general advice favors it.
That is why the plan uses both signals and says which one decided.

## 4. Default rates per word

Allcorrect Games price list (English source, page dated 5 March 2026), EUR per word. The script
uses the midpoint converted at the ECB rate of 23 November 2026 (1 EUR = 1.0939 USD).

| Languages | EUR range | USD midpoint |
|---|---|---|
| French, German, Spanish, Portuguese, Italian, Polish, Greek, Hungarian, Romanian, Czech, Japanese | 0.10 to 0.14 | 0.131 |
| Spanish (Latin America), Portuguese (Brazil), Korean, Traditional Chinese | 0.09 to 0.14 | 0.126 |
| Arabic, Turkish, Indonesian, Vietnamese, Simplified Chinese | 0.09 to 0.12 | 0.115 |
| Dutch, Swedish, Danish, Finnish, Norwegian | 0.10 to 0.17 | 0.148 |
| Russian | 0.06 to 0.09 | 0.082 |
| Malay | 0.12 to 0.13 | 0.137 |

Thai, Ukrainian and Bulgarian have no default: pass `--rates thai=0.12` with a quote. Ask the
vendor whether the rate includes proofreading and LQA (in-game testing); Allcorrect lists LQA as
required for Arabic. Repetitions are often charged less; the script prices unique strings.

## 5. Payback arithmetic

Assumption from the Manalens localization planner: a translated game sells to the Steam users of
a language at the same rate per user as it sells to English users.

- extra copies = English copies x language share / 39.04
- net per copy = price x 0.7 (Valve keeps 30% up to $10 million; VAT and refunds ignored here)
- copies to pay back = ceil(cost / net per copy)
- payback multiple = extra copies x net per copy / cost

Example: 20,000 unique words, Simplified Chinese at $0.115 = $2,300. Price $15, net $10.50.
Copies to pay back: 220. With 5,000 English copies: extra = 5,000 x 21.98 / 39.04 = 2,815
copies, multiple 12.9. Treat it as an upper bound: genre fit, price and marketing in that
language decide the real number.

## 6. One real case

Squeaky Wheel added eight languages to Academia: School Simulator in March 2021 and compared
revenue 6 months before and after (Game Developer, 1 December 2021). Total revenue fell 17% over
the same periods as the game aged. Thai +331%, Turkish +8%, Polish +8%, Brazilian Portuguese -6%,
Latin American Spanish -13%, Russian -20%, Italian -25%, Indonesian -34%. Only Thai clearly paid
back within 6 months; the studio expected Turkish and Polish to pay back within a year.
