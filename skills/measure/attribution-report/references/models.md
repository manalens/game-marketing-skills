# Attribution models, in plain words

Contents: what a model is, the six models, why they disagree, which to use, lookback and
half-life, Steam's own rule, installs, what no model can see.

## What a model is

A player rarely buys after one click. A typical path: a TikTok clip in October, a Reddit post in
November, a newsletter on launch day, then the purchase. Each step that brought them to your site
is a **touch**. A model is a rule that splits the credit for the purchase between those touches.

No model measures cause. Each one answers a different question. That is why the report always
runs at least two.

## The six models (as in Manalens)

Example path: TikTok, Reddit, newsletter, then a purchase of $20.

| Model | Rule | Credit in the example | Answers |
|---|---|---|---|
| `first_touch` | All credit to the first touch | TikTok 1 | Who found this player? |
| `last_touch` | All credit to the last touch, Direct included | newsletter 1 | What happened right before the sale? |
| `last_non_direct` | All credit to the last touch that is not Direct (Direct only if every touch is Direct) | newsletter 1 | Which channel closed it, ignoring "typed the URL"? |
| `linear` | Equal parts to every touch | 0.33 each | Who took part at all? |
| `position_based` | 40% first, 40% last, 20% shared by the middle (2 touches: 50/50) | TikTok 0.4, Reddit 0.2, newsletter 0.4 | Who found and who closed, with a little for the middle |
| `time_decay` | More credit the closer the touch is to the sale; half-life 7 days by default | most to the newsletter | What kept the player moving near the end? |

Revenue is split with the same weights: under `linear`, each touch above gets $6.67.

## Why they disagree, and why it matters

| Kind of channel | Typical job | Wins under | Loses under |
|---|---|---|---|
| Creators, Shorts, TikTok, Reddit, festivals | Discovery: the first time a player hears of the game | first touch, position-based | last touch, time decay |
| Newsletter, wishlist reminder emails, Discord, retargeting ads | The last push to people who already know the game | last touch, last non-direct, time decay | first touch |
| Your website, press, devlogs | The middle: keeping interest | linear | first and last touch |

Steam's own wishlist email at launch does the same closing job, but it carries no UTM tag, so it
shows as Steam traffic, not as a row in any report.

If you judge everything by last touch, the newsletter looks like your best channel and the
creators look useless. Cut the creators and the newsletter has no new readers a month later. If
you judge everything by first touch, you may pay for reach that never converts.

So read the side-by-side:

- **Ahead under both models:** a strong channel. Safe to put more in.
- **Ahead only under first touch:** a finder. Keep it if your closers still have people to close.
- **Ahead only under last touch:** a closer. Do not expect it to grow your audience alone.
- **Low under both, with enough data:** a candidate to cut or change.
- **"too small":** no call yet. Pool more weeks.

## Which model for which question

| Question | Start with | Then compare with |
|---|---|---|
| Which creator or post brought new players? | `first_touch` | `last_non_direct` |
| Is my launch email or Discord worth it? | `last_non_direct` | `first_touch` |
| Is my ad money paying back? | `last_non_direct` | `first_touch` and `linear` |
| Long wishlist-to-launch journeys | `position_based` | `first_touch` |
| A short sale or festival push | `time_decay` (half-life 3 to 7 days) | `last_non_direct` |

`last_non_direct` is the Manalens default and close to what most ad tools report.

Tools differ. Google Analytics 4 now offers data-driven attribution and two last click models.
Google says first click, linear, time decay and position-based are no longer available as of
November 2023. Manalens keeps all six. So a "first touch" number cannot come from GA4: say which
tool and model each number used.

## Lookback and half-life

- **Lookback:** how many days before the conversion to look for touches. A touch older than the
  lookback gets nothing. Wishlists: 30 days is fine. Purchases after a long wishlist period: 90
  to 365 days, or the first touch is often missing and first touch credit falls to whatever came
  later.
- **Half-life** (`time_decay` only): a touch this many days before the sale gets half the weight
  of a touch on the day of the sale. Short half-life: the last days dominate. Long: closer to
  linear.

## Steam's own rule

Steam UTM Analytics is a fixed rule you cannot change: a wishlist, purchase or activation counts
for a tagged visit to the app page by a player signed in to Steam, within 72 hours. That is a
last click model with a 72-hour lookback.

What it misses:

- Phone to PC: a player watches on a phone (often not signed in to Steam there), then searches
  the game on a PC days later. Steam sees search, not your creator.
- Clicks in a social app's browser followed by a wishlist in the Steam client.
- Anything after 72 hours, and small tag combinations, which Steam hides.

So Steam UTM numbers favor channels where people click and act at once (email, Discord) and
undercount discovery channels (Shorts, TikTok, streams). Compare groups with each other, and
read the numbers as a floor. More on blind spots:
https://manalens.dev/blog/game-attribution-blind-spots?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=attribution_report

## Installs

A game build cannot read your website's cookie. Manalens links an install to a website visit by
a certain link (same user ID on site and in game, a handoff link, or a browser game) or by a
network match within 72 hours, with a confidence of high, medium or low. Install attribution has
the single-touch models only: `last_non_direct`, `first_touch`, `last_touch`. Use medium and
high confidence for budget calls.

## What no model can see

- Views without a click (a Short watched, the name remembered, the game searched later).
- Ad impressions and view-through.
- Players who would have bought anyway. Credit is not cause.

To test cause, change one thing and watch the total: pause one channel for 2 weeks, or run it in
one period and not another of the same length, and compare daily wishlists or sales. Note sales,
festivals and press in both periods.

A quick baseline check for one campaign (our practice): compare daily wishlists in the 7 days
after it with the same weekdays of the week before. List every calendar event in both weeks
(sales, festivals, updates, posts). Do not call the campaign the cause unless no other event
explains the change. Attribution shares out credit among the touches you saw; it does not say how
many wishlists would have come anyway.
