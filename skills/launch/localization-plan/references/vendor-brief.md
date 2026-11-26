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

## AI or machine translation drafts

If the team drafts with an AI tool instead of, or before, a vendor, give the tool what a
translator would get. The table and the prompt are Manalens practice, built on Godot's gettext
features (translation context with `msgctxt`, plurals with `msgid_plural`, translator comments).

| Context | Example | Rule for the tool |
|---|---|---|
| Glossary | Character, place, item and mechanic names | Use the listed translation, or keep the term |
| Translation context | `msgctxt "Actions"` for Close | Translate the meaning in that context, not the word alone |
| Plural forms | There is %d apple / There are %d apples | Fill every plural form the language needs |
| Placeholders and tags | `%s`, `%d`, `{name}`, `[b]` | Keep each one unchanged and valid |
| Length limit | Buttons, HUD text | Stay within it, and flag lines that cannot |
| Tone and speaker | Who says the line, to whom | Keep each character's voice |

```
Translate these strings for [game], a [genre] game, from English
to [language]. The player is [age range, tone].

Rules:
- Use the glossary exactly. Keep any term marked KEEP in English.
- Each line has an ID, a context and a max length. Stay within it.
- Keep placeholders such as %s, %d, {name} and tags such as [b] unchanged.
- Fill every plural form [language] needs.
- Keep each speaker's voice, from the speaker column.
- If a line is unclear or cannot fit, translate it anyway and add
  FLAG with the reason.

Return a table: ID | translation | FLAG.

Glossary:
[term | translation or KEEP]

Strings (ID | context | speaker | max length | English):
[paste batch]
```

Then, in this order (Manalens practice, with Valve's QA advice):

1. Run `count_words.py check` on the returned files: placeholders, empty strings, missing keys.
2. Check by hand that glossary terms are used and lengths fit.
3. Have a native speaker play the build in that language and log issues with screenshots. Valve
   suggests localization QA, for example by a second company, or by players who speak the
   language through a forum set up for their feedback.
4. Disclose the AI translation in Steam's Content Survey if players read it (see the Gotchas in
   SKILL.md).
5. To choose between two tools, translate the same 50 strings in both and ask a native speaker
   to mark errors without knowing which tool wrote which line.
