# Privacy rules for a tracking plan

The skill gives technical controls, not legal advice. The user and their adviser decide what
their game needs. Say that once, then help with the controls.

## Always

- **No personal data in events.** No emails, names, usernames, phone numbers, addresses, IPs,
  birthdays or chat text in event names or properties. `check_plan.py` flags property names that
  look like these, in the plan and on track call lines in code.
- **No free text from players.** A typed name, a chat line or a bug report body can hold anything.
  Send a category (`feedback_sent` with `topic: "bug"`), not the text.
- **A stable pseudonymous ID, not an email.** If the game has sign-in, use `identify()` with your
  own player ID. Do not use an email as the ID: it is personal and it changes.
- **No raw IPs.** Manalens takes the country from the request IP and does not store the IP. With
  another tool, turn on its IP masking or anonymizing option, and never add an IP as a property.
- **No device fingerprints.** No hardware IDs, MAC addresses or GPU serials. The Manalens game SDKs
  send no device ID and no hardware details; an anonymous UUID is stored on the device.
- **Error messages.** Engine errors can contain file paths with the user's account name, such as
  `C:/Users/<name>/...`. Use `set_before_send` (Godot) or `BeforeSend` (Unity) to strip them, or
  drop the error.
- **Dev builds.** Set `build` to `dev` in the editor so the developer's own play does not mix into
  player numbers.

## Consent

- Manalens game SDKs: `consent_required: true` (Godot) or `ConsentRequired = true` (Unity), or
  **Consent Required** (Unreal). Before consent the game sends no events and stores no ID. Call
  `set_consent(true)` from a consent screen. The choice is saved for the next launch.
- `set_consent(false)` deletes the ID, the session and the queue, and writes an opt-out marker.
- Web SDK: `data-require-consent="true"`, then `setConsent(true)` from the banner on each page load.
  Before consent, events are sent without IDs, so they count as page views but not as visitors.
- With consent mode, players who say no are not counted. Installs, retention and funnels then
  cover only players who agreed. Write this into the plan's notes so later reports say it.
- Offer an opt-out in the options menu even when consent is not required. It costs one toggle.

## Kids' games

If the game is made for children or likely to attract them:

- Treat it as needing consent from a parent in many places (for example COPPA in the US for under
  13, and the GDPR age of digital consent in the EU, 13 to 16 by country). Ask the user to check
  with their adviser before shipping analytics.
- Use consent mode. Do not call `identify()`. Do not link the game to the website (`link_url()`).
  Keep only aggregate gameplay events: tutorial, level, session, errors.
- No ads or marketing events tied to a child.
- Apple's Kids Category and Google Play's Families policy restrict third-party analytics in apps
  for children. Read the current text before a mobile release.

## Platform rules

| Platform | Rule for analytics | Do this |
|---|---|---|
| Steam | No Steamworks rule we know of blocks analytics in a game. | Say what you collect in a privacy policy and link it from the store page and the game. |
| itch.io | No rule we know of blocks analytics. | Same: a privacy policy link on the page. |
| Web (your site, portals) | EU and UK cookie rules apply to storage on the device. | Consent banner, or consent mode. Portals (CrazyGames, Poki) can have their own SDK rules: read them. |
| App Store | App privacy details ("nutrition label") must list analytics data; tracking across apps needs App Tracking Transparency. | Fill the privacy details to match the plan. Do not track across other companies' apps. |
| Google Play | The Data safety form must list analytics data. | Fill it to match the plan. |
| Consoles | Each platform holder has its own rules under NDA. | Ask the user to check their platform docs. |

## What to write in the privacy policy

A short, true list made from the plan: the kinds of events (sessions, levels, tutorial steps,
errors, store button clicks), that an anonymous ID is stored on the device, the analytics provider
and where it stores data, how long it keeps it, and how to opt out. The skill drafts this text in
`analytics/privacy-notes.md` only when the user asks. It never publishes it.
