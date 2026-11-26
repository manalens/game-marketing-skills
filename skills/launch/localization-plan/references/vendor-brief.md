# Vendor brief template

Copy into `launch/localization-brief.md` and fill it in. The user sends it; the agent never does.

```markdown
# Localization brief: <game>

## The job
- Source language: English. Target languages: <list, with Steam ids>.
- Scope: full game / store page only, per language.
- Deadline: <date>. Build with the strings frozen on: <date>.
- Budget per language, if fixed: <amount>.

## Files
| File | Format | Strings | Words (unique) | Return as |
|---|---|---|---|---|
| godot/translations/game.csv | Godot CSV (one column per language) | 412 | 3,100 | same file, new column |
| locale/messages.pot | gettext template | 280 | 2,450 | one .po per language |

Word counts from count_words.py on <date>. Placeholders and markup are not counted.

## Rules for every string
- Never change placeholders or tags: {name}, {0}, %s, %d, {{var}}, <b>, [color], </>.
  Their order may change if the grammar needs it.
- Keep keys and msgctxt as they are. Do not add or delete rows.
- Length limits: <key or screen>: <max characters>. Buttons: about <n> characters.
- Leave a string empty rather than copying the English text.
- Mark questions in a comment column; do not guess.

## Context
- Genre and tone: <cozy, dry humor, formal>. Audience: <age, platform>.
- Screenshots of each screen: <link or folder>.
- Glossary: game name (translate or not), place names, item names, mechanics.
- Characters: name, gender, how they speak, formal or informal address to the player.
- Words not to translate: <list>.

## Fonts and display
- Fonts in use and which scripts they cover. CJK fallback: <font>.
- Known tight spaces: <screens>.

## Testing (LQA)
- Who plays the translated build, for how long, and how bugs are reported.

## Delivery
- Return files in the same format and encoding (UTF-8). We run a check for missing keys,
  empty strings and placeholder changes on delivery.
```
