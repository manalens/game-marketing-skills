# Running a playtest

Contents: Goals and test types; Recruiting; Call for testers template; Build and consent checklist;
Observation; Pairing survey answers with event data.

## Goals and test types

| Goal | Test type | Testers | What to watch |
|---|---|---|---|
| First-time experience | Blind: the game only, as a buyer gets it; you do not help | Never played it, play the genre | First minutes, where they stop or ask, the tutorial |
| Difficulty and pacing | Blind or guided to a section (a save at the boss) | Players of the genre | Deaths, retries, quits, time per level |
| Fun and core loop | Blind, longer session or several days | Players of the genre | Do they keep going when the session ends; what they talk about |
| Bugs and performance | Guided tasks, many devices | Anyone, other developers too | Crashes, device specs, logs |

Never spend a fresh tester on a guided task: a person can be new to the game only once.

## Recruiting

- **Friends and family:** fine to check that a build installs and runs. Their quits and scores do
  not predict your players.
- **Developer swaps:** trade a session for a session. Good for bugs and first impressions, not for
  fun or difficulty.
- **Your Discord and newsletter:** people who already like the game. Good for rounds after the
  first blind test; mark them as fans in the segment column.
- **Genre communities and r/playtesters:** strangers who play the genre. Read each community's
  rules first, post one clip and a signup form, not a public download.
- **Steam Playtest:** a separate test app on your store page. Players request access next to the
  wishlist button; you add them in batches, and Steam picks them at random from the signups.
  Free; you may not charge for access. You can also
  send Playtest keys before the store page is live. Feedback collection is up to you, so link the
  survey from the main menu.
- **itch.io restricted page:** open only to people you approve, hidden from itch.io search and
  search engines. Good before a Steam page exists.
- **Local events:** meetups and IGDA chapters. You see people play in person.

More, with paid services and prices: [How to find playtesters](https://manalens.dev/blog/how-to-find-playtesters?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=playtest).

Signup form questions: which games like this they played recently, platform and input device,
how to contact them, and consent to be contacted about this test only.

## Call for testers template

```
We are looking for <N> playtesters for <game>, a <genre> where you <fantasy>.
Like <comparable 1> or <comparable 2>? This test is for you.
Platform: <PC / Steam Deck>. Session: about <minutes> minutes, between <date> and <date>.
What we ask: play, then fill in a short survey (about <minutes> minutes).
What you get: <a name in the credits / a key at launch>. No payment.
Sign up: <form link>. We pick testers who play games like this and send the build privately.
```

Draft it; the user posts it. Promise only rewards the user confirms they can give.

## Build and consent checklist

- [ ] Fresh install tested on a clean machine or account.
- [ ] Version number on the title screen; tester ID visible in the menu or in the invite.
- [ ] Logs or analytics on; crash reports reach you.
- [ ] Known bugs listed, so testers do not spend the survey on them.
- [ ] Session length and the end point are clear ("play until the first boss or 30 minutes").
- [ ] Consent text in the invite and at the top of the survey: what you record (survey answers,
  play events, screen or voice only if they agree), what you use it for, that they can stop at
  any time, and that they should not write personal data in text boxes.
- [ ] Separate, explicit yes before any screen, camera or voice recording.
- [ ] Build link sent privately; not posted in public.
- [ ] Survey link with the tester ID filled in.

## Observation

- **Silent observation:** watch, do not speak. Note the time, where in the game, what happened,
  and the face or words. Best for a blind first-time test.
- **Think-aloud:** ask the tester to say what they think while they play. Neutral prompts only:
  "What are you thinking?", "What are you trying to do?", "Please keep talking." Never answer a
  question about the game during the test; say "What would you try?" and note it.
- **Note sheet columns:** time, location in the game, what the tester did, what they said, your
  note. One row per event. Save as `playtest/notes/<tester-id>.md`.
- **After the session:** the survey first, then a short talk. Ask what you saw: "At the door you
  stopped for a while. What were you thinking then?"

## Pairing survey answers with event data

1. Use one tester ID in the build (for example an `identify()` call) and in the survey link.
2. Pick 3 to 5 events that answer the goal: tutorial steps, level start and end, deaths, quit
   point, session length. The `tracking-plan` skill names them; the `player-funnel` skill draws
   the funnel.
3. For each finding, join the two: testers who named the key door as confusing, and their time
   between `area1_enter` and `key_pickup`; testers who rated difficulty 5, and their deaths at the
   boss. Report both counts.
4. Trust behaviour over words when they disagree, and write down both.
