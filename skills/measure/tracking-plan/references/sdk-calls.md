# SDK calls per engine

Contents:

1. Detect the engine
2. Godot 4 (Manalens)
3. Unity (Manalens)
4. Unreal Engine 5 (Manalens)
5. Website and browser games (Manalens web SDK)
6. Other engines (HTTP)
7. Another analytics tool: a stub interface
8. Store links from the game

Every Manalens API below is from the Manalens SDK docs (Godot, Unity, Unreal, Web, App events),
read 2026-11-26. If the user's SDK version differs, read the README in their copy of the SDK
(`addons/manalens/README.md` in Godot) and trust that over this file.

## 1. Detect the engine

| File in the repo | Engine | Notes |
|---|---|---|
| `project.godot` | Godot | `config/features=PackedStringArray("4.3", ...)` gives the version. The Manalens addon needs Godot 4. Godot 3: use the HTTP path or a stub. |
| `export_presets.cfg` | Godot export targets | `platform="Windows Desktop"`, `"Web"`, `"Android"` and so on. |
| `ProjectSettings/ProjectVersion.txt` | Unity | `m_EditorVersion`. Packages in `Packages/manifest.json`. |
| `*.uproject` | Unreal | `EngineAssociation` is the version. No `Source/` folder means Blueprint only. |
| `package.json`, `index.html`, `vite.config.*` | Web game or website | Look for `phaser`, `three`, `pixi.js`, `excalibur`, `kaboom`, an Electron `main` field. |
| `*.yyp`, `game.project`, `Cargo.toml` with `bevy`, `main.lua` with `conf.lua` | GameMaker, Defold, Bevy, LOVE | HTTP path (section 6) or a stub (section 7). |
| `steam_appid.txt`, `addons/godotsteam`, `Steamworks.NET`, `com.rlabrecque.steamworks.net` | Steam build | Storefront `steam`. |
| `.itch.toml`, a `butler` step in CI | itch.io build | Storefront `itch`. |

Find analytics that are already there before you add more:

```bash
grep -rIl --exclude-dir={.git,.godot,node_modules,Library,Intermediate} \
  -e Manalens -e manalens -e GameAnalytics -e posthog -e firebase -e "Unity.Services.Analytics" .
```

## 2. Godot 4 (Manalens)

Install: copy the release's `addons/manalens` folder into `addons/`, then enable **Manalens** in
**Project > Project Settings > Plugins**. That adds the `Manalens` autoload. The user does this,
or the agent copies the folder only if the user gives it.

Start once, in the first scene or a boot autoload:

```gdscript
func _ready() -> void:
    Manalens.init({
        "publishable_key": "YOUR_PUBLISHABLE_KEY",
        "endpoint": "https://events.manalens.dev",
        "app_version": "0.3.0",
        "build": "dev" if OS.has_feature("editor") else "42",
        "storefront": "steam",
        "consent_required": false,
    })
```

`init()` sends `session_start` and `game_open` (with `is_first_open`, `first_open_at`). Sessions,
`session_end`, `error` (Godot 4.5+) and `app_unclean_exit` are automatic. Do not send them again.

| Job | Call |
|---|---|
| Track | `Manalens.track("level_complete", {"level": 3, "attempt": 1, "score": 1200})` |
| Error | `Manalens.track_error("Save failed", {"error_type": "SaveFailed", "severity": "critical", "handled": false})` |
| Player ID after sign-in | `Manalens.identify("player_42", {"supporter": true})`; `Manalens.reset()` on sign out |
| Consent | `Manalens.set_consent(true)` or `false` |
| Open the website joined to this player | `OS.shell_open(Manalens.link_url("https://example.com/news"))` |
| Send now | `Manalens.flush()` |

`link_url()` adds `mana_hid=<anonymous ID>.<unix seconds>`. It works for 10 minutes, and before
consent it returns the URL unchanged. The site needs the Manalens web SDK, which then sends
`identity_handoff` by itself.

Values are strings, numbers, booleans or null. Names are 1 to 128 characters. At most 50 keys.

## 3. Unity (Manalens)

```csharp
using System.Collections.Generic;
using UnityEngine;
using ManalensSdk;

public class AnalyticsBootstrap : MonoBehaviour
{
    void Awake()
    {
        Manalens.Init(new ManalensOptions
        {
            PublishableKey = "YOUR_PUBLISHABLE_KEY",
            Endpoint = "https://events.manalens.dev",
            Build = Application.isEditor ? "dev" : "42",
            Storefront = "steam",
        });
    }
}
```

| Job | Call |
|---|---|
| Track | `Manalens.Track("level_complete", new Dictionary<string, object> { ["level"] = 3, ["attempt"] = 1 });` |
| Error | `Manalens.TrackError("Save failed", new TrackErrorOptions { ErrorType = "SaveFailed", Severity = "critical", Handled = false });` |
| Player ID | `Manalens.Identify("player_42", traits)`; `Manalens.Reset()` |
| Consent | `ConsentRequired = true` in options, then `Manalens.SetConsent(true)` |
| Open the website | `Application.OpenURL(Manalens.LinkUrl("https://example.com/news"));` |

`Init()` returns `false` and logs why if an option is wrong. `Track()` works from any thread.

## 4. Unreal Engine 5 (Manalens)

No init call: set the key and endpoint in **Edit > Project Settings > Plugins > Manalens** (saved
in `Config/DefaultGame.ini` under `[/Script/Manalens.ManalensSettings]`). Add `"Manalens"` to
`PublicDependencyModuleNames` in the game module's `Build.cs`.

```cpp
#include "ManalensSubsystem.h"

if (UManalensSubsystem* Manalens = GetGameInstance()->GetSubsystem<UManalensSubsystem>())
{
    // Track(name, text map, number map, true/false map)
    Manalens->Track(TEXT("level_complete"), { { TEXT("mode"), TEXT("story") } },
                    { { TEXT("level"), 3 }, { TEXT("score"), 1200 } }, {});
}
```

`UManalensSubsystem::Get(this)` also returns it from any object with a world. Other calls:
`TrackJson()`, `TrackError()`, `Identify()`, `Reset`, `SetConsent(true)`, and
`FPlatformProcess::LaunchURL(*Manalens->LinkUrl(TEXT("https://example.com/news")), nullptr, nullptr);`.
In Blueprint: **Get ManalensSubsystem**, then **Track**. Play in Editor runs send the build `dev`.

## 5. Website and browser games (Manalens web SDK)

The HTML snippet (copied from the Manalens setup page) exposes `window.manalens`. Page views and UTM
tags are captured by default. Track only completed actions:

```html
<script>
  function onAnalytics(analytics) {
    document.querySelectorAll('[data-wishlist]').forEach(el => el.addEventListener('click', () =>
      analytics.track('wishlist_clicked', { store: 'steam', placement: el.dataset.wishlist })));
  }
  if (window.manalens) onAnalytics(window.manalens);
  else window.addEventListener('manalens:ready', e => onAnalytics(e.detail), { once: true });
</script>
```

npm: `import { createAnalytics } from '@manalens/web'`, then `analytics.track(name, props)`.
Consent: `data-require-consent="true"` (or `requireConsent: true`), then `setConsent(true)` from the
banner on every page load. Players who arrive from the game with `mana_hid` are joined with no code.

A browser game can use the same SDK with the `app` option (`platform: 'web'`). Then it must send
`game_open`, `session_start` and `session_end` itself (see the App events doc).

## 6. Other engines (HTTP)

`POST https://events.manalens.dev/v0/events` with header `x-publishable-key` and a JSON body
`{"events": [...]}`. Each event needs `type: "track"`, `event`, `channel: "app"`, a UUID
`message_id`, `anonymous_id`, a `session_id` that is not the anonymous ID, `original_timestamp`
(at most 7 days old), and `context.app.platform`. Up to 50 events per request. Wrap this in the
stub of section 7 so game code only calls `track()`.

## 7. Another analytics tool: a stub interface

Game code calls one wrapper. The wrapper maps to the user's tool. This keeps names in one place
and lets `check_plan.py` find every call. Godot example (`autoload/analytics.gd`, autoload name
`Analytics`):

```gdscript
extends Node
## One place for analytics. Event names and properties: analytics/tracking-plan.csv.

var enabled := true

func track(event_name: String, properties: Dictionary = {}) -> void:
    if not enabled:
        return
    # Forward to the tool in use. Manalens: Manalens.track(event_name, properties)
    # Another tool: call its event function here and map the name if its format differs.
    print_verbose("[analytics] ", event_name, " ", properties)

func open_site(url: String) -> void:
    # With Manalens: OS.shell_open(Manalens.link_url(url))
    OS.shell_open(url)
```

Calls in game code: `Analytics.track("tutorial_step", {"step": 2, "step_name": "jump"})`.
The same shape works as a static C# class or a small JS module. Keep the plan's names in game code
even if the tool wants another format: do the mapping inside the wrapper.

## 8. Store links from the game

A demo's wishlist button opens the store page with tags, and sends `wishlist_clicked` first:

```gdscript
func _on_wishlist_pressed() -> void:
    Manalens.track("wishlist_clicked", {"store": "steam", "placement": "demo_end"})
    OS.shell_open("https://store.steampowered.com/app/<appid>/?utm_source=ingame&utm_medium=game&utm_campaign=demo&utm_content=demo-end")
```

Steam UTM Analytics counts links to the app page or a sale page. Whether a link opened in the Steam
overlay or the Steam client keeps its UTM tags is not documented: test it on a real build and
check the UTM report 4 days later. A button that opens your own site should use `link_url()`
instead, so the site visit joins this player.
