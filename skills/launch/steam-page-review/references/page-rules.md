# Steam page rules and templates

Valve's rules for each part of the page, our practice where Valve says nothing, and the
templates the skill fills. Every rule names its source; dates and links are in
[sources.md](sources.md).

Contents:

1. Short description
2. About This Game
3. Screenshots
4. Trailer
5. Supported languages
6. System requirements
7. Timing
8. Why Valve rejects a page
9. Fix list template

## Short description

Rules (Valve, Store Page Written Description):

- A brief synopsis at the very top of the page, next to the header capsule. Also used where
  space is short. Valve: "limited to a few hundred characters".
- Plain text. Line breaks and bullets do not render.
- No time-based text: not "Now Available", "Available on March 4th" or "Prepurchase now".
- No links in any description field.
- "It's often a good idea to mention the game genre."

Guide (Manalens, community report): 300 characters, where the Steamworks editor stops.

Formula (our practice, after Valve, HTMAG 25 May 2020 and GameDiscoverCo 10 August 2020):

1. Genre: "A [genre] set in [place]." or "The [known thing] [genre]."
2. Hook: the one rule, limit or twist other games in the genre do not have.
3. Actions: 2 or 3 verbs in core loop order (build, trade, defend).
4. Cut: adjectives, lore, feature counts, dates, prices, links, exclamation marks.

Worked example: Balatro opens with a three-word label, "The poker roguelike", then one sentence
with "deckbuilder" and three actions (play, discover, trigger). 187 characters.

Weak vs strong (made-up game):

| Weak | Strong |
|---|---|
| Now available! Over 200 recipes, 40 customers, 12 shops. Wishlist now! | A cozy bakery management sim. Bake bread before sunrise, design your shop and manage the morning rush. Each loaf takes real minutes, so you choose which customers to keep. |

## About This Game

Rules (Valve, Store Page Written Description; Review Process):

- Detailed and coherent. Write less, make it easy to skim with bold key features or headers,
  avoid genre jargon, add GIFs or screenshots of key features.
- Each image under 5 MB; all images under 15 MB in total.
- No links to other websites, no graphics that mimic the Steam UI (a fake wishlist button), no
  advertising of other games.
- Only features and content available at launch.
- Text inside an image needs a new image per language. Valve suggests images without text.

Our rule of thumb: 150 words or more (Manalens grader). Balatro uses about 280 words, 6 looping
clips and three blocks.

Template:

```text
[GIF 1: the core loop in 4 to 6 seconds, no text]

[b]<What the player does, as a header>[/b]
<2 to 3 sentences: the core loop, in the verbs from the short description.>

[GIF 2: the second system]

[b]<The second system>[/b]
<2 to 3 sentences.>

[b]<What is different>[/b]
<The hook, shown, not claimed. No "unique", "revolutionary" or "next-gen".>

[b]At launch[/b]
<A short list of real, counted content: 3 biomes, 40 cards, 2 endings. Only what the build has.>
```

Use the Steamworks editor's own formatting (it accepts BBCode-style tags). Keep the list short;
bullets render here, unlike the short description.

## Screenshots

Rules (Valve, Store Graphical Assets; announcement of 3 November 2026):

- At least 5 screenshots. No maximum stated.
- 1920x1080 minimum, 16:9.
- No file type or file size stated. PNG or JPG is the safe choice.
- At least 5 categorized as gameplay. Since 3 November 2026, menus, concept art and in-game
  cinematics are allowed if categorized correctly. Still no marketing copy or awards.
- Older doc text: show gameplay only; menu screens only if they are a unique part of the game.
- Not marked "suitable for all ages" by default. Mark at least 4 if the content allows, or Steam
  may not show them in some places, such as front page hovers.
- Localized versions: drop a version in another language on the screenshot's thumbnail, or end
  the file name with the language (foo_japanese.jpg).
- Valve: showing the in-game UI helps players understand how they interact with the game.

Order (our practice, from the Balatro hover read of 19 November 2026 and HTMAG 25 May 2020):
the store hover tooltip cycles the first 4 screenshots, not the trailer. Make them 4 different
things:

| Position | Job |
|---|---|
| 1 | Core action, HUD on |
| 2 | Second system |
| 3 | Reward or progress |
| 4 | Variety (many units, cards, biomes) |
| 5+ | Depth: shop, map, late game, menus if they matter |

## Trailer

Rules (Valve, Trailers):

- .mov, .wmv or .mp4; H.264 and AAC preferred; up to 1920x1080; 16:9 preferred; 30 or 60 fps;
  5,000+ Kbps; 44 or 48 kHz audio.
- Valve highly recommends a first trailer that is primarily gameplay with the HUD visible.
- The Discovery Queue may give you less than 10 seconds.
- Steam shows the first two trailers before the screenshots.
- Microtrailers: Steam makes 6-second loops from six 1-second clips of the first visible
  trailer. You cannot edit them.
- Upload early: first in, first out; a re-upload goes to the back; no release while converting.

Practice (Derek Lieu via Game Developer 19 April 2021; GameDiscoverCo 19 September 2022):

- No logos or slow pans before play. Viewers do not wait 15 to 30 seconds for gameplay.
- 90 to 180 seconds for a store trailer; shots of about 3 to 5 seconds.
- Many viewers scrub the progress bar, so every point of the timeline shows play.
- Do not stack old trailers on the page.

Review question for the user: "List the first 10 seconds shot by shot." Fail if shot 1 is not
play.

## Supported languages

Rules (Valve, Localization and Languages):

- Over 60% of Steam users use Steam in a language other than English.
- Language support for visibility comes from the game's languages, not the store page. A
  translated page helps the visitor read; a translated game helps Steam show it.
- List interface, full audio and subtitles per language only where the build has them. A
  language on the page that the build lacks is a "feature not in the build".

## System requirements

Rules (Valve, Review Process):

- Minimum requirements for every platform the game supports. Recommended are optional.
- Reviewers compare them with the build.
- Platforms on the page must match the platforms set in Steamworks.

Practice (Manalens guide, 24 November 2026): lines are OS, Processor, Memory, Graphics, Storage.
Start the OS line at Windows 10 (the Steam client supports Windows 10 and later since
1 January 2024). Write them from tests on real hardware.

Template:

```text
Minimum (Windows)
OS: Windows 10 64-bit
Processor: <tested CPU>
Memory: <n> GB RAM
Graphics: <tested GPU or "integrated graphics, OpenGL x.y">
Storage: <build size rounded up> available space
```

## Timing

| Step | Rule | Source |
|---|---|---|
| First game | Wait 21 days between paying the app fee and release | Valve, Onboarding |
| Page review | Mark ready at least 7 business days before it must be live; usually 3 to 5 business days | Valve, Review Process |
| Build review | Up to 12 business days (3 November 2026 backlog) | Valve announcement |
| Coming Soon | Public for at least 2 weeks before release | Valve, Coming Soon |
| Release date | Exact date 60+ days ahead for the Personal Calendar page, 3 weeks for the front page | Valve, Personal Calendar |
| Date lock | Changeable until 2 weeks before; a delay of more than 24 h inside the last 2 weeks drops the game off the calendar | Valve, Release Dates; Personal Calendar |
| Queue (claim) | About 47 days for a new Steamworks account and 15 days for a build review right now | HTMAG, 19 November 2026 |

Put the page up "as soon as presentable" (HTMAG, 19 November 2026): wishlists only collect while
the page is public, and Steam gives no special boost to a newly announced page.

## Why Valve rejects a page

From the Manalens review check, each mapped to Valve's rule (Review Process, Graphical Asset
Rules, Store Graphical Assets, Written Description, Library Assets):

| Problem | Valve rule |
|---|---|
| Page lists features or content not in the game at launch | Only features and content available at launch |
| Capsule has no readable name or logo | Capsules need a readable product title or logo |
| Base capsule shows a score, award, discount or call to action | Base capsules: game art, name and official subtitle only |
| Screenshot carries awards, marketing copy or a product description | Use the page's own spaces for copy and awards |
| Fewer than 5 screenshots | At least 5 screenshots |
| Description thin or hard to follow, or has outside links | Detailed and coherent; no links to other websites |
| Short description has time-based text | No time-based text |
| Images copy Steam buttons, or advertise other games | No graphics that mimic the Steam UI; no ads for other games |
| Library hero has text | The library hero cannot include text |
| Build does not start on a listed OS | Must start on all supported operating systems |
| A listed feature (controller support) is not in the build | All listed features implemented in the current build |
| In-game purchases skip the Steam Wallet | Use the Steam Wallet for in-game transactions |

Capsule and library rows belong to `steam-capsules`; list them here only when Valve's note names
them.

## Fix list template

```markdown
## Fix list
### Blocks review
- [ ] <what> in <where>. Fix: <one line>. Rule: <Valve page>.
### Costs wishlists
- [ ] <what>. Fix: <one line>.
### Polish
- [ ] <what>. Fix: <one line>.
```
