# Handle rules by platform

`scripts/name_score.py` checks the plain handle form (lowercase letters and digits, no separators)
against these limits. Platforms change them; re-check before relying on a limit.

| Platform | Length | Characters | Source, read 2026-11-26 |
|---|---|---|---|
| X | more than 4, up to 15 (plan on 5 or more) | letters, digits, underscore | X Help Center, as quoted by several handle checkers; X words the minimum two ways |
| Instagram | up to 30 (not published by Instagram) | letters, digits, period, underscore; no period at start or end | Widely reported, enforced by the sign-up form; Instagram Help gives no number |
| TikTok | 2 to 24 | letters, digits, underscore, period; no period at the end | TikTok Support, "Changing your username" |
| YouTube handle | 3 to 30 (Latin script) | letters, digits, underscore, hyphen, period, middle dot; no separator at start or end | YouTube Help, "Learn about YouTube handles" |
| Bluesky | 3 to 18 before `.bsky.social` | letters, digits, hyphen; no underscore or period | Bluesky Support, "What is the suggested user handle format?" (updated 6 Apr 2026) |
| Reddit community | 3 to 21, cannot be changed later | letters, digits, underscore | Reddit Help, "How to create a community" (updated 5 Oct 2026) |
| Discord custom invite | up to 25 | lowercase letters, digits, dashes | Discord Support, "Custom Invite Link"; needs Server Boost Level 3 |
| Domain label | up to 63 | letters, digits, hyphen | RFC 1035 |
| App Store / Google Play name | 2 to 30 / up to 30 | no emoji; Google: no ALL CAPS unless brand, no ranking or price words | Apple and Google help pages, read by Manalens 2026-11-18 |

Profile URLs to open (ask the user to open them if the agent cannot browse):

- `https://www.youtube.com/@<handle>`
- `https://www.tiktok.com/@<handle>`
- `https://x.com/<handle>`
- `https://bsky.app/profile/<handle>.bsky.social`
- `https://www.instagram.com/<handle>/`
- `https://www.reddit.com/r/<handle>` and `https://www.reddit.com/user/<handle>`
- Discord: the custom invite can only be tested inside Server Settings, Boost Perks. Discord
  Support cannot confirm availability in advance.

A page that loads may belong to an inactive or deleted account. Treat "taken" as a hint.
