# Steam launch rules table

`scripts/timeline.py` parses the three tables below. Keep the column order and the `key` values.
Edit a value here, not in the script, when Valve changes a rule. Every row has a source and the
date it was read.

Contents:

1. Rules (numbers the plan counts with)
2. Steam events (seasonal sales and Next Fest dates)
3. Next Fest editions (Valve deadlines)
4. Claims (one source's numbers, shown as claims, never used as hard deadlines)
5. Notes on the rules

## Rules

`basis` is `valve` for a Valve rule or `practice` for a lead time we chose. Only `valve` rows can
make a hard deadline.

| key | value | unit | rule | basis | source | checked |
|---|---|---|---|---|---|---|
| app_fee_usd | 100 | usd | Steam Direct fee per game, paid back after the game earns 1,000 USD in adjusted gross revenue | valve | https://partner.steamgames.com/doc/gettingstarted/appfee | 2026-11-19 |
| app_fee_wait_days | 21 | days | Wait between paying the app fee and releasing that game (first titles on an account) | valve | https://partner.steamgames.com/doc/gettingstarted/onboarding | 2026-11-19 |
| tax_check_days | 30 | days | Tax verification "may take up to 30 days" | valve | https://partner.steamgames.com/doc/gettingstarted/onboarding | 2026-11-19 |
| page_review_business_days | 7 | business_days | Submit the store page at least 7 business days before you want it live (review typically 3 to 5) | valve | https://partner.steamgames.com/doc/store/review_process | 2026-11-19 |
| build_review_business_days | 7 | business_days | Plan at least 7 business days for build review (typically 3 to 5) | valve | https://partner.steamgames.com/doc/store/review_process | 2026-11-19 |
| build_backlog_business_days | 12 | business_days | Build review "taking up to 12 business days" (Valve announcement, 3 Nov 2026) | valve | https://steamcommunity.com/groups/steamworks/announcements/detail/696528162820984746 | 2026-11-19 |
| coming_soon_min_days | 14 | days | A new product needs a public Coming Soon page for at least two weeks before release | valve | https://partner.steamgames.com/doc/store/coming_soon | 2026-11-19 |
| calendar_page_days | 60 | days | Exact release date set at least 60 days ahead to be eligible for the dedicated Personal Calendar page | valve | https://partner.steamgames.com/doc/marketing/visibility/personalcalendar | 2026-11-18 |
| calendar_front_days | 21 | days | Exact release date set at least three weeks ahead to be eligible for the Personal Calendar on the front page | valve | https://partner.steamgames.com/doc/marketing/visibility/personalcalendar | 2026-11-18 |
| date_lock_days | 14 | days | The release date can change until two weeks before it, then it locks | valve | https://partner.steamgames.com/doc/store/release_dates | 2026-11-19 |
| late_delay_hours | 24 | hours | A delay of more than 24 hours inside the last two weeks removes the game from the Personal Calendar until release | valve | https://partner.steamgames.com/doc/marketing/visibility/personalcalendar | 2026-11-18 |
| launch_discount_max_pct | 40 | percent | Launch discount at most 40%, set up before release | valve | https://partner.steamgames.com/doc/marketing/discounts | 2026-11-19 |
| launch_discount_min_days | 7 | days | Launch discount runs at least 7 days | valve | https://partner.steamgames.com/doc/marketing/discounts | 2026-11-19 |
| launch_discount_max_days | 14 | days | Launch discount runs at most 14 days | valve | https://partner.steamgames.com/doc/marketing/discounts | 2026-11-19 |
| release_cooldown_days | 30 | days | No discount for 30 days after release; a game on this cooldown cannot discount in a seasonal sale | valve | https://partner.steamgames.com/doc/marketing/discounts | 2026-11-19 |
| demo_notify_window_days | 14 | days | The demo notification to wishlisters can be sent once, within 14 days of the demo's first release | valve | https://partner.steamgames.com/doc/store/application/demos | 2026-11-19 |
| wishlist_notify_gap_days | 14 | days | Valve suggests at least 14 days between the demo notification and other wishlist notifications such as the release | valve | https://partner.steamgames.com/doc/store/application/demos | 2026-11-19 |
| next_fest_preview_weeks | 5 | weeks | Submit the Next Fest demo no later than 5 weeks before the fest to be in the Press Preview | valve | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest | 2026-11-19 |
| next_fest_fest_weeks | 3 | weeks | Submit every Next Fest item no later than 3 weeks before the fest | valve | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest | 2026-11-19 |
| first_keys_wait_days | 21 | days | First-time developers wait 3 weeks after app ID creation to request keys | valve | https://manalens.dev/blog/track-steam-key-activations-creators | 2026-11-26 |
| review_score_min | 10 | reviews | Steam shows a review label from 10 reviews by Steam buyers; key activations do not count | valve | https://partner.steamgames.com/doc/store/reviews | 2026-11-26 |
| announce_weeks | 26 | weeks | Announce and post the Coming Soon page about six months before launch | practice | https://manalens.dev/tools/game-marketing-timeline | 2026-11-19 |
| page_before_nf_registration_days | 14 | days | Coming Soon page public at least two weeks before a Next Fest registration deadline | practice | https://manalens.dev/tools/game-marketing-timeline | 2026-11-19 |
| demo_weeks | 8 | weeks | Without Next Fest, release the demo eight weeks before launch | practice | https://manalens.dev/tools/game-marketing-timeline | 2026-11-19 |
| creator_outreach_weeks | 6 | weeks | Start creator emails 4 to 6 weeks before launch, one week minimum (YouTuber Blitz, via Manalens) | practice | https://manalens.dev/blog/creator-email-templates-indie-games | 2026-11-26 |
| press_keys_weeks | 4 | weeks | Review keys to press four weeks before launch, with the embargo | practice | https://manalens.dev/tools/game-marketing-timeline | 2026-11-19 |
| creator_keys_weeks | 2 | weeks | Keys to creators two weeks before launch | practice | https://manalens.dev/tools/game-marketing-timeline | 2026-11-19 |
| review_request_days | 10 | days | Ask your own list for an honest review about ten days after launch | practice | https://manalens.dev/tools/game-launch-email-templates | 2026-11-26 |

## Steam events

Seasonal sales have no registration. A game discounts in one only if it released at least
`release_cooldown_days` before the start. `TBD` means Valve has not announced dates.

| name | kind | start | end | source | checked |
|---|---|---|---|---|---|
| Steam Winter Sale 2026 | Seasonal sale | 2026-12-17 | 2027-01-04 | https://partner.steamgames.com/doc/marketing/upcoming_events | 2026-11-18 |
| Steam Next Fest: February 2027 | Next Fest | 2027-02-22 | 2027-03-01 | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest/feb_2027 | 2026-11-18 |
| Steam Spring Sale 2027 | Seasonal sale | 2027-03-18 | 2027-03-25 | https://partner.steamgames.com/doc/marketing/upcoming_events | 2026-11-18 |
| Steam Next Fest: June 2027 | Next Fest | 2027-06-14 | 2027-06-21 | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest/june_2027 | 2026-11-18 |
| Steam Summer Sale 2027 | Seasonal sale | 2027-06-24 | 2027-07-08 | https://partner.steamgames.com/doc/marketing/upcoming_events | 2026-11-18 |
| Steam Next Fest: October 2027 | Next Fest | TBD | TBD | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest | 2026-11-18 |
| Steam Autumn Sale 2027 | Seasonal sale | TBD | TBD | https://partner.steamgames.com/doc/marketing/upcoming_events | 2026-11-18 |
| calendar_announced_until | meta | 2027-07-08 | 2027-07-08 | https://partner.steamgames.com/doc/marketing/upcoming_events | 2026-11-18 |

## Next Fest editions

All times are Pacific. Registration is from the base game, not the demo.

| id | name | start | end | register_by | press_preview_submit | all_items_submit | press_preview | source |
|---|---|---|---|---|---|---|---|---|
| feb-2027 | Steam Next Fest: February 2027 | 2027-02-22 | 2027-03-01 | 2027-01-10 | 2027-01-18 | 2027-02-01 | 2027-02-11 | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest/feb_2027 |
| june-2027 | Steam Next Fest: June 2027 | 2027-06-14 | 2027-06-21 | 2027-04-25 | 2027-05-10 | 2027-05-24 | 2027-06-03 | https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest/june_2027 |

## Claims

Shown in the plan as context with their date. Not Valve rules.

| key | value | unit | claim | source | date |
|---|---|---|---|---|---|
| claim_new_account_days | 47 | days | Queue for a new Steamworks account to clear onboarding "right now" | How To Market A Game, howtomarketagame.com/2026/11/19/3-new-steam-tools/ | 2026-11-19 |
| claim_build_review_days | 15 | days | Build review queue "right now" | How To Market A Game, howtomarketagame.com/2026/11/19/3-new-steam-tools/ | 2026-11-19 |
| claim_demo_live_days | 19 | days | Top 25 October 2026 Next Fest demos had been live about 19 days on average before the fest | How To Market A Game, 21 Oct 2026 | 2026-10-21 |
| claim_press_build_weeks | 3 | weeks | 67% of 150+ journalists want review builds 3 weeks or more ahead (2024 survey) | Big Games Machine survey via trapster.gg | 2026-11-18 |

## Notes on the rules

- **Fee wait is 21 days, not 30.** Older guides say 30 days. Valve's onboarding page (read
  19 Nov 2026) says 21 days for first titles. Tax verification can take up to 30 days and runs
  in parallel, so start both early.
- **Seasonal sales are exempt from the normal discount cooldown**, but not from the 30-day
  release cooldown or a 30-day price increase cooldown. Themed fests follow the cooldowns with no
  exception (Valve Discounting page).
- **Next Fest:** one edition per game, ever. The game must not release before the edition ends.
  The base game page must be public to register. A demo must be public when the fest starts.
  Cancelling a registration before the fest frees the game for a later edition.
- **Weekend releases** show on the Personal Calendar on the next Monday. Valve's date picker hides
  weekends and Valve does not recommend them.
- **Wishlist emails Steam sends:** at release (and at leaving Early Access), once for the demo
  (within 14 days of its first release), and for a discount of 20% or more that lasts over 8 hours,
  with about a two-week gap between discount emails (Valve, via Manalens, Nov 2026).
