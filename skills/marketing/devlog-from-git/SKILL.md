---
name: devlog-from-git
description: >
  Finds devlog Short and post ideas in a game's git history: player-visible changes for a daily
  "Update #N" series, and real bugs, cut features and design problems for "there was a problem"
  Conflict Shorts, each with the commit before and after so both states can be recorded. Use for
  "what can I post about this week", "turn my commits into devlog content", "find bugs to make
  Shorts about", "devlog ideas from my changelog". Not for writing the final script and post text
  (`shorts-script`) or cutting the video (`clip-cut`).
---

# Devlog from git

The best short-form stories for a solo developer are true ones: the bug that made the pumpkins eat
the farmer, the feature that had to go, the change players will see today. They are already in
the git log. This skill finds them, checks they are visible to a player, and writes a story brief
for each, with the commits needed to record the "before" and the "after".

Writes `marketing/devlog/<YYYY-MM-DD>.md`. Hand each chosen brief to `shorts-script`.

## Inputs

1. **The game repo** and the folder that holds the game (skip the website, tools and backend).
2. **The date range:** default the last 14 days, or since the last file in `marketing/devlog/`.
3. **What the public build is:** the demo or the release a viewer can play. A change that is not
   in it yet can be a "coming soon" Update, never a promise.
4. **`marketing/rules.md`:** the do-not-say list (spoilers, names, dates). Ask once if missing.

## Workflow

1. **List candidates.** From the game repo:

   ```bash
   python3 <skill>/scripts/mine_git.py --since "14 days ago" --path <game folder>/
   ```

   Add `--kind conflict` or `--kind update` to narrow, `--show-skipped` to see what was dropped
   and why, `--json` to read it in code. The script is a first filter by message and path. It
   misses things and lets noise through, so read the diffs next.

2. **Read each candidate's diff** (`git show <sha> --stat`, then the parts that matter). Keep it
   only if a player can see or feel the change in under 3 seconds of footage. Drop refactors,
   tooling and numbers nobody notices.

3. **Sort the keepers into story types:**

   | Type | Signal in the log | Story shape |
   |---|---|---|
   | Bug | "fix", "stuck", "falls through", "crash" | "In my game about <loop>, <the bug>." Show it, show the cause, show the fix. |
   | Cut | "cut", "remove", "delete" a feature or item | "I had to delete <thing> from my game." Why, and what replaced it. |
   | Design problem | "rework", "too hard", "balance", "revert" | "Players kept <doing X>, so I <changed Y>." Or ask: "Which should I keep?" |
   | Glow-up | art, shader, animation, "polish" commits | Before and after, side by side or as a cut. One line of text. |
   | Update | "add", "new", content and asset files | "<Game> Update #N: <the change in plain words>." |

   Bugs and cuts are the strongest. Funny beats careful. A problem the viewer can see beats a
   problem you have to explain. Glow-ups (before and after) do well on Reddit and Bluesky because
   they read as progress, not an ad. Tell each story for players, not other developers: what
   changed in the game, not in the code.

4. **Plan the footage for each pick.** The "after" is the current build. For the "before", record
   from the commit before the fix in a separate worktree, so the main checkout is untouched:

   ```bash
   git worktree add ../before-<short-sha> <short-sha>^
   ```

   Run that build on a free port or in a separate folder and record the bug. Remove the worktree
   when done (`git worktree remove ../before-<short-sha>`). If the old build will not run, use a
   screenshot from the PR or issue, or skip the pick. Never fake a bug.

5. **Write the brief file** (see Output). Number Update posts in order and never skip a number:
   read the last number from the previous file in `marketing/devlog/`.

6. **Check:** every brief names a commit that exists (`git cat-file -e <sha>`), every Update is
   in the public build or marked "not in the demo yet", and no brief uses a word from
   `marketing/rules.md`. Run:

   ```bash
   python3 <skill>/scripts/check_briefs.py marketing/devlog/<date>.md --repo <game repo>
   ```

7. **Hand off:** the user picks 2 to 7 briefs for the week; run `shorts-script` on each, and
   `social-post` or `reddit-post` for the glow-ups. A longer written devlog belongs on the Steam
   page as a news event, not as patch notes. See
   [where to post devlogs](https://manalens.dev/blog/where-to-post-devlogs).

   You cannot over-show your game: post from the build early and often. Old ideas can be
   recycled too; a joke that flopped on one platform has gone viral on another.

## Output

`marketing/devlog/<YYYY-MM-DD>.md`:

```markdown
# Devlog ideas, 2026-11-26 (commits 2026-11-12 to 2026-11-26)

## 1. Cut: the golden shovel (conflict)
- Commit: 3f9c2e1 (before: 3f9c2e1^)
- Story: I made a golden shovel and a golden rod. Then I deleted both.
- Why it matters to a player: upgrades now come from the shop; one fewer grind.
- Footage: before worktree, the golden shovel digging; after, the shop's upgrade card.
- Hook ideas: "I had to delete the golden shovel from my game." / "Why I cut my best item."
- In public build: yes

## 2. Update #14: dig cells show what is under the sand (update)
- Commit: a71b0d4
- Footage: a crack dug cell by cell, the picture appearing.
- In public build: not yet (say "coming in the next update")
```

## Measure

Tag each resulting post with its post ID (`docs/LINKS.md`). In `marketing-retro`, compare
Conflict and Update posts against Caption and Mechanic posts by average view duration. Note which
story types (bug, cut, glow-up) hold viewers, and mine those first next time.

## Gotchas

- **Squashed merges hide the story:** a PR squashed into one "Feature X" commit loses the bug
  that happened on the way. Read the PR description and review comments too, if the repo has them.
- **Commit messages lie by omission:** "fix" can be a typo in a comment. Always read the diff.
- **Old builds will not start:** dependencies drift. Install in the worktree with the lockfile from
  that commit. If it still fails, use stored screenshots or drop the pick.
- **Shallow clones:** CI or cloud checkouts may have only recent history. Run
  `git fetch --depth=500` (or `--unshallow`) first if the date range looks empty.
- **Spoilers in the diff:** late-game content shows up in commits. Check `marketing/rules.md`
  before suggesting it.
- **Private repo details:** do not show code, file names, secrets or internal tools on screen
  unless the user says so.

## Version notes

Uses only `git` (any version from 2.20). No platform facts to go stale.

Last verified 2026-11-26.
