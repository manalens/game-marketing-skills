# Steam capsule and library art sizes

Sizes as of 26 November 2026. Source: Valve's Steamworks Graphical Assets pages, as recorded in the
Manalens size table (`steam-assets.ts`, checked against Valve on 18 and 19 November 2026). Valve
moved most capsules to larger sizes in August 2024 and says "Old dimensions are no longer
accepted." Check the Valve pages before a big upload: sizes change.

| Id (script) | Asset | Size in pixels | Required | File type Valve names | Where Steam shows it | Valve page |
|---|---|---|---|---|---|---|
| `header` | Header capsule | 920 x 430 | Yes | None named | Top of the store page, Recommended For You, Big Picture browse, Daily Deals | [standard](https://partner.steamgames.com/doc/store/assets/standard) |
| `small` | Small capsule | 462 x 174 | Yes | None named | Lists: search results, top sellers, new releases. Steam also makes 120 x 45 and 184 x 69 copies | [standard](https://partner.steamgames.com/doc/store/assets/standard) |
| `main` | Main capsule | 1232 x 706 | Yes | None named | Main carousel at the top of the store home page | [standard](https://partner.steamgames.com/doc/store/assets/standard) |
| `vertical` | Vertical capsule | 748 x 896 | Yes | None named | Top of the front page during seasonal sales, sale pages | [standard](https://partner.steamgames.com/doc/store/assets/standard) |
| `background` | Page background | 1438 x 810 | No | None named | Behind the store page. With no upload, Steam uses your last screenshot | [standard](https://partner.steamgames.com/doc/store/assets/standard) |
| `bundle` | Bundle header | 707 x 232 | Only for a bundle | None named | Top of the bundle page | [standard](https://partner.steamgames.com/doc/store/assets/standard) |
| `library-capsule` | Library capsule | 600 x 900 | Yes | None named | Library overview and collections. Must include the logo | [libraryassets](https://partner.steamgames.com/doc/store/assets/libraryassets) |
| `library-header` | Library header | 920 x 430 | Yes, but falls back | None named | Library, for example Recent Games. With no upload, Steam uses the store header | [libraryassets](https://partner.steamgames.com/doc/store/assets/libraryassets) |
| `library-hero` | Library hero | 3840 x 1240 | Yes | PNG | Top of the game's library page. No words at all. Keep key art in the 860 x 380 safe area at the centre | [libraryassets](https://partner.steamgames.com/doc/store/assets/libraryassets) |
| `library-logo` | Library logo | 1280 wide and/or 720 tall | Yes | PNG, transparent background | On top of the library hero. Only the logotype | [libraryassets](https://partner.steamgames.com/doc/store/assets/libraryassets) |
| `shortcut-icon` | Shortcut icon | 256 x 256 or 512 x 512 | Yes | PNG or ICO | Desktop shortcuts | [community](https://partner.steamgames.com/doc/store/assets/community) |
| `app-icon` | App icon | 184 x 184 | Yes | JPG | Library list view, chat favourites, notifications | [community](https://partner.steamgames.com/doc/store/assets/community) |
| `event-cover` | Event cover | 800 x 450 | Yes, per event | None named | Recent announcements on the store page, event lists, library page. Steam shows your game name and icon next to it | [eventassets](https://partner.steamgames.com/doc/store/assets/eventassets) |
| `event-header` | Event header | 1920 x 622 | Suggested | None named | Top of the event detail page | [eventassets](https://partner.steamgames.com/doc/store/assets/eventassets) |

Not capsules, but often asked about with them: screenshots are 1920 x 1080 or larger, 16:9, at
least 5, and since 3 November 2026 at least 5 must be gameplay (Valve). Those belong to
`steam-page-review`.

## File size

Valve lists no file size limit for these assets. The script's `check --max-mb` is a cap you choose.

## Sizes Steam makes from your upload

| Upload | Copies Steam serves | Source |
|---|---|---|
| Small capsule | 120 x 45 and 184 x 69 | Valve, standard assets page |
| Small capsule | 231 x 87 in store tab lists | Manalens measurement of the desktop store, 19 November 2026 (not a Valve number) |
| Library capsule | 300 x 450 | Valve, library assets page |
| Library hero | 1920 x 620 | Valve, library assets page |

## Logo placement used by `capsules.py make`

These are starting points, not Valve rules. They follow the Manalens capsule maker defaults.

| Asset | Logo fits inside | Logo centre (height) | Why |
|---|---|---|---|
| Small capsule | 90% of the frame | middle | Valve: the logo "should nearly fill the small capsule" |
| Header, main, library header | 70% | 62% down | Room for the subject above |
| Vertical, library capsule | 80% | 78% down | Character or scene above, logo at the bottom |
| Shortcut and app icon | 80% | middle | Usually a symbol, not the full logo: replace by hand |
| Event cover | 60% | middle | Steam already shows the name next to it |
| Event header | 50% | middle | Wide banner |
| Library hero, page background | no logo | | Valve: the hero has "no words at all"; the background sits behind the page |

The logo also stays 5% in from every edge (Manalens practice). The library logo is your logo file
itself, scaled to 1280 wide or 720 tall, whichever keeps it inside 1280 x 720.
