---
name: playtest
description: >
  Plans, runs and analyses playtests of a game or demo. Sets the goal (first-time experience,
  difficulty, fun, bugs), finds testers (friends, Discord, r/playtesters, Steam Playtest, itch.io),
  prepares the build and consent, plans what to observe (silent observation, think-aloud), writes a
  short survey without leading questions, and after the test summarises the survey CSV (Google
  Forms or Tally) with counts, medians, segments and grouped free text, paired with play data by
  tester ID. Writes playtest/plan.md, playtest/survey.md and playtest/report.md. Use for "plan a
  playtest for my demo", "write a playtest survey", "summarise my playtest feedback". Not for
  in-game analytics funnels or event drop-off (use player-funnel).
---

# Playtest

Plan a playtest, write its survey, and turn the answers into a short list of fixes. The agent
reads the game's docs and build notes, writes `playtest/plan.md` and `playtest/survey.md` before
the test, and after it runs `scripts/survey_report.py` on the survey export and writes
`playtest/report.md`. It never sends invites, posts calls for testers or uploads builds.

## Inputs

Look in the repo first, then ask only for what is missing.

- **The game and build:** genre, platform, how long a session takes, what is new in this build.
  Look in `README.md`, design docs, changelogs and `git log`.
- **The question this test must answer.** One main goal, at most two. If the user has none, ask:
  "What decision will you make after this test?"
- **Who is available:** friends, a Discord, a newsletter, a Steam page (for Steam Playtest).
- **Analytics:** does the build send events with a player or tester ID? Look for a tracking plan
  (`tracking-plan` skill output) or an analytics SDK call such as `identify(`.
- **After the test:** the survey CSV export, observation notes, and the event export or funnel.

## Workflow

1. **Pick the goal and the test type.** Use the table in
   [references/running-sessions.md](references/running-sessions.md#goals-and-test-types): first-time
   experience needs a blind test with new players; difficulty and fun need your target players;
   bugs can use anyone, including other developers. Output: goal, type and the decision it feeds,
   at the top of `playtest/plan.md`.
2. **Size and recruit.** About 5 testers per round find most usability problems (Nielsen), so
   run small rounds and fix between them. For rates (how many quit, how many wishlist), aim for
   30 or more new players per build (a Manalens working minimum, not a research figure). Draft
   the call for testers from the template in the reference: friends and other developers for a
   build that runs, then Discord or newsletter, genre communities such as r/playtesters (read the
   rules first), Steam Playtest signups, or a restricted itch.io page. Ask the user to post the
   call and report back how many signed up. Never post it.
3. **Prepare the build and consent.** Checklist in the reference: a build that installs clean,
   a tester ID shown in the menu or sent in the invite, logs on, known bugs listed, the consent
   text (what you record, what you use it for, that they can stop at any time, no personal data
   in text boxes). Ask before recording video or voice. Output: the checklist in `plan.md`.
4. **Plan the observation.** For in-person or call sessions: silent observation or think-aloud,
   a note sheet (time, where, what happened, what the tester said), and the only prompts allowed
   ("What are you thinking?", "What are you trying to do?"). Never explain the game during a
   blind test. Output: the session script in `plan.md`.
5. **Write the survey** to `playtest/survey.md` from
   [references/survey-questions.md](references/survey-questions.md): 8 to 12 questions, 8 or
   fewer after a session under 15 minutes. Always include a profile question for segmenting
   ("How often do you play games like this one?"), the hardest moment, the confusing moment,
   one thing to change, the wishlist question as a fact ("Is it on your wishlist now?"), and
   would-you-recommend. Keep scales the same between builds so rounds compare. Rewrite any
   leading question with the table in the reference. Hand off: the
   [Manalens playtest survey builder](https://manalens.dev/tools/playtest-survey-builder?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=playtest)
   builds the same kind of survey from playtest type, genre, length and goals and exports CSV,
   with steps for Google Forms and Tally.
6. **Pair with event data.** Put the tester ID in the survey (a Google Forms pre-filled link or a
   Tally hidden field) and send the same ID from the build. List in `plan.md` the 3 to 5 events
   that answer the goal (tutorial step done, level start and end, quit point, deaths). If the
   events do not exist yet, run the `tracking-plan` skill first.
7. **Run the test.** Ask the user to run the sessions, export the survey as CSV, and save notes
   to `playtest/notes/`. Report back when done.
8. **Summarise the survey:**
   `python3 scripts/survey_report.py playtest/responses.csv --segment "how often" --out playtest/report-data.md`.
   It counts choices, gives medians for scales, splits by the segment, groups free text by
   keyword and flags small samples. Map key questions the header text did not match with
   `--role change="what would you fix"`.
9. **Write `playtest/report.md`.** Read the data file and the notes, then write: what we tested,
   who (count per segment), the top 3 to 5 problems with evidence (quotes, counts, and the event
   data for the same testers), what to change, and what to test next round. Pair each problem
   with play data: for example, testers who wrote about the key door, and where the funnel shows
   them stopping (`player-funnel` skill). Separate what testers did from what they said.
10. **Check:** `survey_report.py` exits 0 (add `--min-responses 5` to fail a round too small to
    report), and `playtest/report.md` has the sections Goal, Testers, Findings, Changes, Next test.

## Output

- `playtest/plan.md`: goal and decision, test type, tester count and sources, call for testers,
  build and consent checklist, session script, events to pair, dates.
- `playtest/survey.md`: intro, consent line, numbered questions with answer type and options.
- `playtest/report.md`, after the test:

```markdown
# Playtest report: demo build 0.4, 2026-11-24
## Goal
Can new players finish the first area without help? Decision: ship the tutorial or rework it.
## Testers
14 (10 play the genre most weeks, 4 never before). Small segments flagged.
## Findings
1. Key door: 6 of 12 answers to "did not know what to do" mention the key or the map. Event data:
   5 of those 6 testers spent over 4 minutes between `area1_enter` and `key_pickup`.
2. Level 3 boss: hardest moment for 7 of 13. Overall median 4 of 5, recommend median 8 of 10.
## Changes
- Map marker for the key. Checkpoint before the boss.
## Next test
5 new players, blind, same survey, same scales.
```

## Measure

Compare rounds, not single numbers: the same questions and scales each build, the onboarding and
difficulty medians, the share of testers who name the same problem, and from event data the share
who pass the step you fixed. For a public demo or Steam Playtest, also note how many testers
wishlisted (survey fact question, and Steamworks wishlists in the test days). `marketing-retro`
reads `playtest/report.md` to tie fixes to later demo numbers.

## Gotchas

- **Asking for predictions:** "Would you buy this?" overstates intent. Ask facts ("Is it on your
  wishlist now?", "Which similar game did you buy last?") and read recommend scores next to
  actions.
- **Helping during a blind test:** one hint ruins what the test measures. Write down where you
  wanted to help; that is the finding.
- **Friends as the only testers:** they know you and are kind. Use them to check the build runs,
  not to judge fun or difficulty.
- **Leading questions:** "How fun was the boss?" assumes fun. Name both ends of a scale ("How easy
  or hard..."), and ask about one thing at a time.
- **Tiny segments:** a split with 3 testers in one group is anecdote. The script flags any segment
  under 5; do not turn those into percentages in the report.
- **Survey without IDs:** without a tester ID, answers cannot be joined to play data. Add it
  before the round, not after.
- **Personal data in quotes:** testers write names and emails into text boxes. Remove them before
  sharing the report.
- **Steam Playtest does not collect feedback:** Valve says that part is up to you. Link the survey
  from the main menu or the invite.
- **Playtest during Next Fest:** Valve advises against a live Steam Playtest during the fest,
  because it splits players between two builds.

## Version notes

- Steam Playtest: free, signups from the store page in batches, keys possible before the page is
  live, no charging for access, feedback collection is up to the developer, no effect on Next Fest
  eligibility (Steamworks Steam Playtest docs, as read by Manalens 19 and 24 Nov 2026).
- Survey length (8 to 12 questions, 8 or fewer under 15 minutes) and the 30 players per build
  minimum are Manalens practice, not standards. Sources: [references/sources.md](references/sources.md).

Last verified 2026-11-26.
