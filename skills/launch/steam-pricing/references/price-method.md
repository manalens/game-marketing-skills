# Price method

Contents:
1. Valve's own guidance
2. The steps, with their basis
3. Genre price norms
4. Reading comps and reviews
5. What the price says
6. Early Access
7. Net revenue per copy

Each line says its basis: **Valve** (a Steamworks rule or suggestion), **Source** (a named, dated
study) or **Ours** (a rule of thumb from the Manalens price picker; disagree and adjust by hand).

## 1. Valve's own guidance

- Valve: price against similar games on length, replay value and multiplayer, and do not
  undercut the competition. Play time is the first factor Valve lists. (Steamworks, Pricing.)
- Valve: many developers set their own price in each currency, and that is fine. Price changes
  wait until 30 days after release, cannot be scheduled, and Valve usually reviews a change in
  one or two business days.
- Valve: the base price in each currency must be at least the Multi-variable conversion of the
  $0.99 tier. `pricing.py check` tests this.

## 2. The steps

| Step | Rule | Basis |
|---|---|---|
| Length | Under 2 h $4.99; 2 to 5 h $9.99; 5 to 10 h $14.99; 10 to 25 h $19.99; 25 h or more $24.99 | Ours |
| Production | Rich art, voice or many systems: one step up. Simple art or a first game: one step down | Ours |
| Genre | See section 3 | Source |
| Soft cap | Above $24.99 is getting harder for a new game that is not deep strategy, because players compare with $10 to $15 indie games | Source (GameDiscoverCo, 21 Nov 2025) |
| Comps | Median US price of the comps x 1.2, snapped to the nearest step | Source (How To Market A Game, 23 Aug 2022) |
| Weighting | 3 or more comps: comps count two thirds, length tier one third. 1 or 2 comps: half each | Ours |
| Evidence | 8+ priced comps strong, 5 to 7 moderate, under 5 limited | Ours |
| Market range | Middle half of the comps' US prices (25th to 75th percentile) | Ours |

Steps on the ladder: $2.99, $4.99, $7.99, $9.99, $12.99, $14.99, $17.99, $19.99, $24.99,
$29.99, $34.99, $39.99. All are in Valve's regional table.

Worked example: a 12 hour pixel-art roguelite, standard production. Length gives $19.99. Genre
moves one step down to $17.99. Five comps have a median of $14.99; x 1.2 = $17.99. Weighted:
$17.99. Range: $14.99 to $19.99.

## 3. Genre price norms

| Genre | What the data says | Source |
|---|---|---|
| All new games | Median Top 50 new Steam game by copies sold cost $15.64 in October 2025, down 20% from $19.50 | GameDiscoverCo, 21 Nov 2025 |
| Roguelike, Survivors-like, online co-op party | Cheaper hits are common; cheap does not mean short. Middle price of 11 well-known roguelikes $9.99, from $4.99 to $29.99 | GameDiscoverCo, 21 Nov 2025; Manalens roguelike pricing count |
| Deckbuilder | Leading games mostly $14.99 to $24.99, middle $19.99 across 9 | Manalens deckbuilder pricing count |
| Cozy | 161 of 300 cozy games with about $100k+ estimated revenue cost $10 to $19.99, median $17.99. Length matters less | Manalens count of games-stats.com data, 18 Nov 2026 |
| Survival crafting | Can charge $25 to $40 if deep enough | GameDiscoverCo, 21 Nov 2025 |
| Strategy (deep) | Exempt from the $25 soft cap | GameDiscoverCo, 21 Nov 2025 |
| Price and revenue | Among new 2024 Steam games, 62% priced at $40 and up reached the top 250 by gross revenue, against 1.7% at $4.99 or less (correlation: bigger games cost more) | Manalens free to play vs premium guide |

## 4. Reading comps and reviews

- Use games released in the last 5 years (ours). Older prices may reflect another market.
  HTMAG is stricter: comps "released in the last 3 years", in the same genre and scale, with
  failures and hidden gems, not only hits; after about 10 games you know what such games sell
  for (Source, 23 Aug 2022). Prefer the last 3 years when you have enough comps.
- Open every comp on Steam yourself, and copy its price and review count from the store page.
  An AI tool asked for comps tends to list famous hits and can name games that do not exist;
  asked for sales, it may state a figure it invented (OpenAI, 5 Sep 2025: models produce
  "plausible but false statements", most often on rare facts such as a small game's sales).
- Leave out free games and games with no US price.
- Valve's GetAppReviews web method works for any app, needs no key and returns up to 100
  reviews per page (Valve, IUserReviewsService). Use it, or the store page, to pull reviews.
- Read the newest 100 English reviews of each comp for price sentences. Sort them into "too
  expensive", "good value" and "wait for a sale". The Steam price picker does this with
  keyword rules.
- A comp with many "good value" reviews at $19.99 is room to stay at $19.99. A comp with many
  "wait for a sale" reviews is at the edge of what players accept.
- Review count tells you how many people bought at that price. A comp with 200 reviews at
  $24.99 is weaker evidence than one with 5,000 at $19.99.

Sales range per comp (Boxleiter method, Source: How To Market A Game, Benchmarks, read
26 Nov 2026). Multiply the review count by sales per review for the comp's release year:

| Release year | Sales per review |
|---|---|
| 2013 to 2017 | 79 down to 43 |
| 2018 | 38 |
| 2019 | 36 |
| 2020 | 31 |
| 2021 | 20 to 55, median 31 |

- Write a low and a high, never one number: one review count can mean sales that differ by more
  than double.
- Valve: only users with recorded playtime can review, and only purchases count toward the review
  score. Key activations are partly missing from the shown totals.
- An AI tool can do the arithmetic once you paste the counts. Start the prompt with "Use only the
  data below. If a value is missing, write unknown." (ours, after OpenAI's note that a model
  allowed to say it does not know guesses less).

## 5. What the price says

| Price | What players tend to read into it |
|---|---|
| $4.99 or less | A small or short game, a toy, an impulse buy. Fine for a 1 to 2 hour game |
| $9.99 | A complete small game. The default for short roguelites and arcade games |
| $14.99 to $19.99 | A full indie game with a few hours of content and polish. The middle of the market |
| $24.99 | A large indie game. The page must show depth: many screenshots, a trailer, systems |
| $29.99 and up | Deep strategy, simulation or survival, or a known studio. Expect "worth it?" reviews |

The table is ours. Check it against the page: the capsule, trailer and screenshots must look
like the price. A low price on a polished page also sends a signal: players may think something
is wrong with the game.

## 6. Early Access

- Valve: most developers start Early Access below the target launch price. Rule of thumb: one
  ladder step below the 1.0 price (ours).
- Valve: the Early Access price must not be higher than on any other store.
- Valve: a price increase blocks discounts for 30 days, including the launch discount at 1.0.
  Raise the price more than 30 days before 1.0. A 1.0 launch discount is not allowed if Early
  Access began less than 30 days before.

## 7. Net revenue per copy

Valve keeps 30% up to $10 million (Steam Distribution Agreement tiers, 30 Nov 2018), after VAT,
refunds and chargebacks. Example: $19.99 with 20% VAT holds $3.33 of tax; the rest is split
70/30. Plan a small game's income on about 70% of net sales. GameDiscoverCo says a developer
receives about 30% to 50% of an optimistic gross estimate after discounts, the Steam cut,
refunds and VAT.
