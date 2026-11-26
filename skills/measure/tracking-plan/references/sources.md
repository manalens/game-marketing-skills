# Sources

Written in our own words. Checked 2026-11-26.

- Manalens SDK docs (https://docs.manalens.dev/sdks/overview and the Godot, Unity, Unreal, Web and
  App events pages under it): every API call, the automatic events, consent behaviour, the
  `link_url()` handoff (`mana_hid`, 10 minutes), event limits and the event conventions
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
