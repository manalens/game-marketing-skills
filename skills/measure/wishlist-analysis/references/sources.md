# Sources

Written in our own words. Checked 2026-11-26. "Claim" marks one source's number.

- Steamworks, Wishlists: https://partner.steamgames.com/doc/marketing/wishlist (wishlist emails at
  release, EA to 1.0, discounts of 20% or more over 8 hours, one demo email; 1 to 2 week cooldown;
  no formula predicts sales from wishlists).
- Steamworks, Personal Calendar:
  https://partner.steamgames.com/doc/marketing/visibility/personalcalendar (exact date 60 days
  ahead for the calendar page, 3 weeks for the front page).
- How To Market A Game, "Wishlist inflation is real, but they are still important", 13 Oct 2026:
  https://howtomarketagame.com/2026/10/13/wishlist-inflation-is-real-but-they-are-still-important/
  (0.22 vs 0.45 units per wishlist in month one, 160 games; R² 0.72 total, 0.70 velocity). Also
  Inven Global, 15 Oct 2026.
- How To Market A Game, "How the Steam Personal Calendar affects your launch", 25 Jun 2026:
  https://howtomarketagame.com/2026/06/25/how-the-steam-personal-calendar-affects-your-launch/
  (Popular Upcoming threshold, calendar benchmarks, about 7,000 as a floor).
- How To Market A Game, Next Fest October 2026 report, 21 Oct 2026; GameDiscoverCo, "Who won
  October 2026's Steam Next Fest", 27 Oct 2026:
  https://newsletter.gamediscover.co/p/who-won-october-2026s-steam-next (demo count, median and
  top 10% wishlists).
- How To Market A Game, "Games that used momentum for Steam Next Fest success", 14 Jul 2026:
  https://howtomarketagame.com/2026/07/14/games-that-used-momentum-for-steam-next-fest-success/
- GameDiscoverCo, "The state of Steam wishlist conversions: 2024-2025", 17 Oct 2025:
  https://newsletter.gamediscover.co/p/the-state-of-steam-wishlist-conversions (0.15 median,
  0.10 above $10, 25k+ wishlists).
- Melos Han-Tani, "Wishlist woes and post-cozy problems: Danchi Days", 8 Nov 2026:
  https://buttondown.com/melodicambient/archive/wishlist-woes-and-post-cozy-problems-danchi-days/
  (wishlist-only week-one rate 2.2%, cohorts 1.0% to 7.4%; one game).
- Manalens docs, Steam integration: https://docs.manalens.dev/integrations/steam (Steam UTM import
  and Steamworks Financial API wishlist sync with adds, deletes, purchases and gifts per day in
  GMT; dashboard setup "coming soon"; early access).
- Manalens docs, MCP server: https://docs.manalens.dev/mcp/overview (`get_steam_wishlists` daily
  adds, deletes, purchases, gifts, net and outstanding change; `get_steam_utm`; `get_analytics`
  reports; `get_attribution` groups; checked 2026-11-26).
- Manalens tools: Steam wishlist CSV analyzer (header `DateLocal,Game,Adds,Deletes,
  PurchasesAndActivations,Gifts`; lines above the header skipped) and wishlist quality forecaster.
