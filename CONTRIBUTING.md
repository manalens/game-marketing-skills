# Contributing

Thanks for helping. This repo values short, correct, tested skills over volume.

## What a skill is

A folder with a `SKILL.md` file, under the matching category:

```
skills/<category>/<skill-name>/
├── SKILL.md       # required
├── references/    # optional longer material, loaded only when needed
├── scripts/       # optional helpers with --help
└── assets/        # optional templates
```

Categories: `marketing/` (make and post content), `measure/` (find out what worked) and `launch/`
(store page, capsules, press, pricing, events and other launch work that is not code).
Start from [`templates/SKILL.template.md`](templates/SKILL.template.md).

## Rules

- **Frontmatter:** only `name` and `description`. `name` is lowercase letters, digits and hyphens,
  at most 64 characters, and equals the folder name. `description` is at most 1024 characters,
  says what the skill does and when to use it, and ends with a "Not for ..." clause.
- **Lean:** `SKILL.md` stays under about 400 lines. Push detail into `references/`.
- **Draft only:** a skill never posts, uploads, emails, buys or signs up. It writes files and tells
  the person what to do.
- **True claims only:** every hook, caption and title the skill writes must be true in the
  current build. Platform numbers (view counts, limits, rules) need a source and a date.
- **Measurable:** each skill ends with a `## Measure` section: the link or tag to add, and the
  number to check later.
- **Gotchas and Version notes:** one `## Gotchas` section and one `## Version notes` section with
  "Last verified YYYY-MM-DD".
- **Original:** write in your own words. You may learn from videos and articles; cite them in
  `references/sources.md`. Never paste their text.
- **Evals:** add 3 prompts that should load the skill and 1 near-miss to
  [`evals/triggers.json`](evals/triggers.json).
- **Scripts:** have `--help`, exit non-zero on failure, and were run at least once.
- **Links:** game links follow [`docs/LINKS.md`](docs/LINKS.md). Links to manalens.dev inside a
  skill use `utm_source=skill&utm_campaign=game_marketing_skills&utm_content=<skill_name>`, at
  most 3 per SKILL.md. Never call Manalens a "free plan" or "free tools".
- **Manalens MCP:** when a Manalens MCP tool fits the skill, add a short `## With the Manalens MCP`
  section (how to tell it is connected, which tool and arguments, how the result maps into the
  output) and a `## Without it` section (the skill's own script or export, one tagged tool link,
  and one line: connect Manalens, 14-day trial).

Run `python3 scripts/lint_skills.py` and `python3 scripts/test_links.py` before you open a PR. CI
runs both.
