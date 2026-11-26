# Sources

Valve pages show no "last updated" date, so each carries the date it was read. Numbers reached
this skill through the Manalens website content (files named below), which cites these pages.

## Valve (primary)

- Steamworks, Pricing: https://partner.steamgames.com/doc/store/pricing (read 2026-11-18)
- Steamworks, About regional pricing (pricing explorer, Multi-variable method, data "as of
  October 2026"): https://partner.steamgames.com/pricing/explorer (read 2026-11-18)
- Steamworks, Supported currencies: https://partner.steamgames.com/doc/store/pricing/currencies
- Valve, "Updates to Pricing Conversion Tools", 27 March 2026:
  https://steamcommunity.com/groups/steamworks/announcements/detail/501722749836722406
- Steamworks, Discounting: https://partner.steamgames.com/doc/marketing/discounts (read 2026-11-18)
- Steamworks, Seasonal Sales: https://partner.steamgames.com/doc/marketing/discounts/seasonalsales
- Steamworks, Daily Deals: https://partner.steamgames.com/doc/marketing/discounts/dailydeal
- Valve, "Upcoming Changes to the Discounts and Events Section on Steam", 29 September 2026:
  https://store.steampowered.com/news/group/4145017/view/676258795703240951
- Steamworks, Upcoming Steam Events: https://partner.steamgames.com/doc/marketing/upcoming_events
- Steamworks, Wishlists: https://partner.steamgames.com/doc/marketing/wishlist
- Steamworks, Early Access: https://partner.steamgames.com/doc/store/earlyaccess
- Steamworks, Bundles: https://partner.steamgames.com/doc/store/application/bundles
- Steamworks, Downloadable Content: https://partner.steamgames.com/doc/store/application/dlc
- Steamworks, Steam Keys: https://partner.steamgames.com/doc/features/keys
- Steamworks, User Reviews: https://partner.steamgames.com/doc/store/reviews (read 2026-11-26):
  reviewers need recorded playtime; only purchases count toward the score.
- Steamworks, IUserReviewsService, GetAppReviews:
  https://partner.steamgames.com/doc/webapi/IUserReviewsService (read 2026-11-26): any app, no
  key, up to 100 reviews per page.
- Valve, revenue share tiers, 30 November 2018:
  https://steamcommunity.com/groups/steamworks/announcements/detail/1697191267930157838

## Studies and articles

- GameDiscoverCo, "Are Steam game prices dropping, and should you care?", 21 November 2025:
  https://newsletter.gamediscover.co/p/are-steam-game-prices-dropping-and
- GameDiscoverCo, "Discount strategy: your key post-launch game discovery tool", 7 January 2021:
  https://newsletter.gamediscover.co/p/discount-strategy-your-key-post-launch
- How To Market A Game, "4 tips to help you price your indie game", 23 August 2022:
  https://howtomarketagame.com/2022/08/23/4-tips-to-help-you-price-your-indie-game/
- How To Market A Game, Benchmarks: https://howtomarketagame.com/benchmarks/ (read 2026-11-26):
  Boxleiter sales per review by release year.
- OpenAI, "Why language models hallucinate", 5 September 2025:
  https://openai.com/index/why-language-models-hallucinate/ (read 2026-11-26)
- How To Market A Game, "Bundling is giving", 14 December 2022:
  https://howtomarketagame.com/2022/12/14/bundling-is-giving/
- How To Market A Game, "Benchmark: How much money can you make from DLC?", 3 March 2026:
  https://howtomarketagame.com/2026/03/03/benchmark-how-much-money-can-you-make-from-dlc/
- GameDiscoverCo DLC posts, 15 October 2019 and 25 July 2022 (newsletter.gamediscover.co).
- itch.io, Open revenue sharing (4 March 2015) and Accepting Payments and Getting Paid:
  https://itch.io/docs/creators/payments

## Manalens content used (read 2026-11-26)

- `steam-regional-prices.ts`: the bundled regional table (`assets/valve-regional-prices.csv`).
- `steam-price-data.ts`: price regions and the review price keyword rules.
- `steam-price-picker.ts`: the price ladder, length bands, genre moves, comp weighting, launch
  discount rule of thumb.
- `steam-events-2027.ts`, `game-tool-data.ts`: seasonal sale dates and fest discount notes.
- `glossary-terms/steam-sales-stores.ts`, `glossary-terms/release.ts`: discount, cooldown,
  launch discount, regional pricing, bundle, DLC and itch.io rules.
- `article-tldr.ts`: roguelike, deckbuilder and cozy price counts, free to play vs premium.
- `guides/ai-game-dev-4.ts` ("How to do game market research with AI", 26 November 2026): the
  3-year comp advice and the Boxleiter table (cited above), the "write unknown" prompt line and
  the store-page-first checks (Manalens practice).
