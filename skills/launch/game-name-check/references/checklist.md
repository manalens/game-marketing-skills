# Name availability checklist

Contents: Stores and search; Trademarks; Domains; Handles; Clone and confusion risk; Recording results.

Run it for the top 2 or 3 names. For each row, write the result, who checked it (agent or user)
and the date. The agent runs what it can reach; for the rest, write "ask the user to open <link>
and report back". Never register, claim, file or buy anything.

## Stores and search

| Check | How | Fail when |
|---|---|---|
| Steam exact | `https://store.steampowered.com/search/?term=<name>` | a game with the same words (ignore case, accents, punctuation) |
| Steam similar | search the main word alone, and the name without spaces | a close name in the same genre |
| itch.io | `https://itch.io/search?q=<name>` | an active project with the same name |
| Google | the exact name in quotes, plus "<name> game" | a game, app, film or brand owns page one |
| App Store and Google Play | search the store, or a web search for "<name> app" | a game or app with the same name |
| Console stores, if relevant | ask the user to search the eShop, PlayStation Store and Xbox Store | same name in games |

The Manalens matching rule, used by `name_score.py` too: exact means the same words after removing
case, accents and punctuation. Close means one name contains the other (when the shorter has two or
more words), or they share at least 60% of their words.

## Trademarks

This skill gives no legal advice. It records what free searches show.

| Office | Link | Look in |
|---|---|---|
| USPTO (United States) | https://tmsearch.uspto.gov/search/search-information | live marks, classes 9 (software) and 41 (entertainment) |
| EUIPO TMview (EU, national offices, partners) | https://www.tmdn.org/tmview/ | same classes |
| WIPO Global Brand Database | https://branddb.wipo.int/en/ | international registrations |

Search the exact name, the main word alone, and spellings that sound the same. Write down any live
mark in class 9 or 41 with the same or a similar name, with its number and owner. The USPTO says
marks can conflict when they are similar in sound, look or meaning and the goods are related; they
do not need to be identical. Close every trademark note with: "A free search is not legal advice.
Ask a trademark lawyer to clear the name in the countries where you sell."

## Domains

Check `<handle>.com` first, then `.gg`, `.games`, `.io`, `.dev`, or `play<handle>.com` and
`<handle>game.com`. Ask the user to look the domain up at a registrar and report back: a domain
without DNS records may still be registered. You do not need the .com. A rule of thumb from
Manalens: own one short domain that matches the name.

## Handles

YouTube, TikTok, X, Bluesky, Instagram, a subreddit, Reddit user, Discord custom invite. Rules and
URLs: [handles.md](handles.md). Prefer the same handle everywhere. If the plain name is taken on
the two or three networks the players use most, pick one variant (`play<name>`, `<name>game`) and
use it on every network.

Also search the hashtag (`#<name>`) on TikTok, Instagram and X. A hashtag already full of another
topic will bury your posts.

## Clone and confusion risk

Confusion with an existing game:

- An exact or close name in the same genre: fail.
- The name uses a famous game's distinctive word, or a word plus a genre ("<Famous>like"): flag.
- Two of your candidates sound alike: keep only one.

How easy the game is to copy (four signs from How To Market A Game, 11 Nov 2026, as used by the
Manalens clone risk check). Count the yes answers: 0 or 1 is low, 2 is medium, 3 or 4 is high
(Manalens rule of thumb).

1. Does one clever mechanic or joke sell the game, so one short clip shows it all?
2. Is the art neutral or realistic rather than a recognisable style?
3. Does the design follow a well established genre closely?
4. Does the content come from systems rather than hand made levels or story?

A distinct name helps players find the original. Note it, and if the risk is medium or high, point
the user to a ready demo, a live store page and a filed trademark (the Steam trademark complaint
form asks for registration numbers).

## Recording results

Add one availability table per name to `launch/name-check.md` (see the Output example in
SKILL.md). Keep the date on each row: handles and domains change hands.
