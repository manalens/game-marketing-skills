# Sources

Written in our own words. Checked 2026-11-26.

- Manalens SDK docs (https://docs.manalens.dev/sdks/overview and the Godot, Unity, Unreal, Web and
  App events pages under it): every API call, the automatic events, consent behaviour, the
  `get_handoff_url()` handoff (`mana_handoff`, 10 minutes), event limits and the event conventions
  (`game_open`, `level_start`, `level_complete`, `level_fail`, `resource`, `purchase`, `error`).
- Manalens docs guides "Plan and check your game events", "Identify users", "Consent mode" and
  "Install attribution" (same docs site): fewer than 15 events, naming rules, the dev build
  filter, how web visitors and game installs join.
- Manalens MCP server docs and `apps/api/src/mcp.ts`: `get_analytics` reports and filter fields.
- Manalens genre tracking plans: https://manalens.dev/tracking-plans?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=tracking_plan (per genre events,
  properties and KPIs).
- Steamworks, UTM Analytics: https://partner.steamgames.com/doc/marketing/utm_analytics (which
  links count).
- Apple App Review Guidelines, sections 1.3 (Kids Category) and 5.1.2 (data use):
  https://developer.apple.com/app-store/review/guidelines/
- Google Play Families policy: https://support.google.com/googleplay/android-developer/answer/9893335
- US FTC, COPPA rule: https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa
- This repo's link convention: `docs/LINKS.md`.
- Twilio Segment documentation, Data Collection Best Practices (read 26 November 2026):
  https://www.twilio.com/docs/segment/protocols/tracking-plan/best-practices (what a tracking plan
  is for: which events, where in the code, and why).
- Mixpanel documentation, Create A Tracking Plan (read 26 November 2026):
  https://docs.mixpanel.com/docs/tracking-best-practices/tracking-plan (tracking every user
  action wastes development work and leaves unused data).
- Google Analytics Help, [GA4] Recommended events, For games (Google, read 26 November 2026):
  https://support.google.com/analytics/answer/9267735?hl=en (the 11 recommended game events).
- Manalens SDK docs, Godot and Unity pages (read 26 November 2026): flat values, strings cut at
  1,024 characters, `app_version`, `build` and `storefront` set at `init()`.
- Manalens docs, Agent (read 27 November 2026): https://docs.manalens.dev/features/agent
  (project memory: 280 characters an item, 80 items a project).
- Manalens guide "How to use AI to write a tracking plan for your game" (26 November 2026), which
  collects the points above:
  https://manalens.dev/blog/ai-game-tracking-plan?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=tracking_plan
