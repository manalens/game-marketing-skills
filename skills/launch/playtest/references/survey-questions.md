# Survey questions

Contents: Rules; Core survey; Extra questions by goal; Leading questions and fixes; Moving it into a form tool.

## Rules

- 8 to 12 questions; 8 or fewer after a session under 15 minutes (Manalens practice). About 20
  seconds for a closed question and 60 for an open one.
- Broad questions first, money last. One open question at the end.
- Ask about what happened, not about the future. Ask for one thing per question.
- Name both ends of a scale in the question ("How easy or hard..."). Keep the same scale every
  round so builds compare.
- No question asks the tester to design the fix. "One thing to change" is fine: read it as a pointer
  to the problem, not as the solution.
- Put the intro and consent at the top: "We test the game, not you. There are no wrong answers.
  When you send your answers, you agree that we use them to improve the game. Please do not write
  personal data in the text boxes."

## Core survey

The headers below are worded so `survey_report.py` finds the key questions by header text.

| # | Question | Type | Why |
|---|---|---|---|
| 0 | Your tester ID (hidden or pre-filled) | text | Joins answers to play data |
| 1 | How often do you play games like this one? (Most weeks / A few times a year / I tried one or two / Never before this test) | single | Segment: weigh answers by how close the tester is to your players |
| 2 | Overall, how was the game? (1 very bad to 5 very good) | scale | One number to compare builds |
| 3 | How easy or hard was it to understand what to do in the first minutes? (1 very hard to 5 very easy) | scale | First-time experience |
| 4 | How easy or hard was the game for you? (1 much too easy, 3 about right, 5 much too hard) | scale | Difficulty; the middle is the target |
| 5 | Which moment was the hardest, and what made it hard? | text | Hardest moment; a place to look for in fail and quit data |
| 6 | Describe a moment when you did not know what to do next, if there was one. | text | Confusing moment |
| 7 | Which moment do you remember best? Tell us what happened. | text | What to protect and show in the trailer |
| 8 | What broke, froze or looked wrong? Tell us where it happened. | text | Bugs |
| 9 | Why did you stop playing? (End of the build / Out of time / Got stuck / Got bored / A bug stopped me / Other) | single | Separates lost interest from lack of time |
| 10 | Is this game on your Steam wishlist now? (Yes, from before / Yes, added after playing / No / I do not use wishlists) | single | Wishlist as a fact, not a promise |
| 11 | How likely are you to recommend this game to a friend who plays games like this? (0 to 10) | scale | Would-you-recommend; read next to question 10 |
| 12 | If you could change one thing, what would it be? | text | One thing to change |
| 13 | What else do you want to tell us? | text | Topics you did not ask about |

That is 13 plus the ID. Cut to fit the session: for a 10 minute demo keep 1, 2, 3, 5, 6, 10, 12, 13.

About would-you-wishlist: the common wording "Would you wishlist this game?" asks for a promise,
which overstates intent. Ask whether it is on the wishlist now (live builds), or one day later
"Since the test, which of these have you done?" (wishlisted, followed, told a friend, played again).

About would-you-recommend: a 0 to 10 scale is familiar and quick, but it is still a prediction.
The script reports the median and the shares of 9 to 10 and 0 to 6 answers. Compare it between
builds, never as a forecast of sales.

## Extra questions by goal

- **First-time experience:** "In your own words, what is the goal of the game?" (text); "How was
  the amount of explanation at the start? Too little / About right / Too much" (single).
- **Difficulty:** "When you failed, what did you mostly feel? I knew what I did wrong / Bad luck /
  It felt unfair / I did not fail" (single); "How did the pace feel? Too slow / About right / Too
  fast / It changed a lot" (single).
- **Fun:** "When the session ended, how much did you want to keep playing?" (1 not at all to 5 very
  much); "How would you describe this game to a friend in one sentence?" (text).
- **Controls:** "What did you play with?" (single); "Which action did not do what you expected?"
  (text).
- **Bugs:** "How many times did the game crash or freeze?" (Never / Once / 2 or 3 / More than 3);
  "What did you play on?" (text).
- **Price, only late:** "What did you pay for the last game like this that you bought?" (text).

## Leading questions and fixes

| Leading | Neutral |
|---|---|
| How fun was the boss fight? | How did the boss fight feel? / Which moment do you remember best? |
| Did you like the new crafting system? | How easy or hard was crafting to use? |
| Was the tutorial too long? | How was the amount of explanation at the start? Too little / About right / Too much |
| Would you buy this game? | Which game like this did you buy most recently? What made you buy it? |
| Don't you think the jump is floaty? | Which action did not do what you expected? |
| How much better is this build? | (Same questions as last round; compare the numbers.) |
| What feature should we add? | If you could change one thing, what would it be? |

## Moving it into a form tool

- **Google Forms:** Linear scale for scales, Multiple choice for single choice, Checkboxes for
  multi choice, Paragraph for text. For the tester ID, use "Pre-fill form" and send each tester
  their own link. Export with Responses, "Download responses (.csv)".
- **Tally:** Linear scale, Multiple choice, Checkboxes and Long answer blocks. Add a hidden field
  `tester_id` and add `?tester_id=<id>` to each tester's link. Export the submissions as CSV.
- Both export checkbox answers joined with commas. `survey_report.py` splits on ", " and ";", so
  avoid commas inside option text.
