#!/usr/bin/env python3
"""Check an ordered Steam tag list before you enter it in the Tag Wizard.

Input: a text file with one tag per line, in the order you want (first = most weight). Commas
also separate tags. Blank lines and lines starting with # are ignored; leading "1." or "-" is
stripped. Example: launch/steam-tags.txt

Checks:
  count       5 to 20 tags. Valve requires 5 before launch, recommends up to 20, and only the
              top 20 are shown and used. Fewer than 20 is a warning.
  duplicates  the same tag twice, also after spelling variants ("Point & Click" vs "point and click").
  top 5       at least one specific sub-genre tag; no generic tags (Indie, Action, Adventure,
              Casual, Singleplayer) and no opinion tags (Masterpiece, Great Soundtrack...).
  status      Early Access and Free to Play only when true for the game.
  known tags  each tag is looked up in the bundled Manalens benchmark list (66 genre and theme
              tags, snapshot 2026-11-18) and labeled Crowded, Mid or Smaller. A tag that is not in
              the list is info only: check its spelling in the Tag Wizard.
  --similar   optional file of similar games' tags, one game per line as "Name: tag, tag, ...".
              Reports tags used by at least half the set that you miss, and tags only you have.

Exit code 0 when nothing fails, 1 when a check fails, 2 on a usage error. --strict fails on warnings.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALVE_MIN, VALVE_MAX, VALVE_FILTER, VALVE_DESCRIBE = 5, 20, 15, 5
CROWDED_SHARE, SMALLER_SHARE, COMMON_SHARE = 5.0, 2.0, 50.0

# Ours, from HTMAG (12 Nov 2020) "empty calorie" tags and Valve's Suggest Prioritization, which
# moves low-information tags such as indie and singleplayer down.
HARD_GENERIC = {"indie", "singleplayer"}
EMPTY = {"action", "adventure", "casual", "2d", "3d", "colorful"}
# Broad parent genres: fine in the list, but below the specific sub-genre tags.
PARENT = {"simulation", "strategy", "rpg", "puzzle", "arcade", "shooter", "platformer", "sports", "racing"}
GENERIC = HARD_GENERIC | EMPTY | PARENT
# Ours: tags that judge quality instead of describing the game. Leave them to players.
OPINION = {"masterpiece", "great soundtrack", "addictive", "beautiful", "classic", "cult classic",
           "epic", "replay value", "good", "best", "fun", "awesome", "amazing", "unique",
           "innovative", "polished"}
STATUS = {"early access", "free to play"}
ALIASES = {"f2p": "free to play", "free 2 play": "free to play", "shmup": "shoot em up",
           "soulslike": "souls like", "roguelike deck builder": "roguelike deckbuilder",
           "deck building": "deckbuilding", "deckbuilder": "deckbuilding", "deck builder": "deckbuilding",
           "point n click": "point and click", "hack n slash": "hack and slash", "idle": "idler",
           "clicker": "incremental", "colony simulator": "colony sim", "farming simulator": "farming sim",
           "life simulation": "life sim", "dating simulator": "dating sim", "first person shooter": "fps",
           "real time strategy": "rts", "japanese rpg": "jrpg", "action roguelite": "action roguelike",
           "single player": "singleplayer"}


def norm(text):
    """Lower case, '&' to 'and', no accents or punctuation, then aliases (Manalens normalizeTag)."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"['’]", "", t.replace("&", " and "))
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return ALIASES.get(t, t)


def read_tags(path):
    tags = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for part in line.split(","):
            part = re.sub(r"^(\d+[.)]|[-*])\s*", "", part.strip()).strip()
            if part:
                tags.append(part)
    return tags


def load_benchmark():
    data = json.loads((HERE / "benchmark_tags.json").read_text(encoding="utf-8"))
    return data, {norm(t["name"]): t for t in data["tags"]}


def size_label(games, all_games):
    share = 100 * games / all_games
    label = "Crowded" if share >= CROWDED_SHARE else "Smaller" if share < SMALLER_SHARE else "Mid"
    return share, label


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tags", type=Path, help="text file with your tags, one per line, in order")
    ap.add_argument("--similar", type=Path, help='file with similar games, one per line: "Name: tag, tag, ..."')
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args()
    if not args.tags.is_file():
        ap.error(f"{args.tags} not found")

    rows = []
    add = lambda status, text: rows.append({"status": status, "text": text})
    tags = read_tags(args.tags)
    keys = [norm(t) for t in tags]
    bench, known = load_benchmark()

    n = len(tags)
    if n < VALVE_MIN:
        add("fail", f"{n} tags. Valve requires at least {VALVE_MIN} before launch and recommends up to {VALVE_MAX}.")
    elif n > VALVE_MAX:
        add("fail", f"{n} tags. Only the top {VALVE_MAX} are shown and used by Steam. Cut to {VALVE_MAX}.")
    elif n < VALVE_MAX:
        add("warn", f"{n} tags. Valve recommends up to {VALVE_MAX}; empty slots are lost reach.")
    else:
        add("pass", f"{n} tags.")

    seen = {}
    for i, k in enumerate(keys):
        if k in seen:
            add("fail", f"Duplicate: '{tags[i]}' (position {i + 1}) repeats '{tags[seen[k]]}' (position {seen[k] + 1}).")
        else:
            seen[k] = i
    if len(seen) == n and n:
        add("pass", "No duplicates.")

    top = keys[:VALVE_DESCRIBE]
    specific = [tags[i] for i, k in enumerate(top) if k not in GENERIC and k not in OPINION and k not in STATUS]
    if top and not specific:
        add("fail", "The top 5 has no specific sub-genre tag. Valve uses the top 5 to describe the game.")
    elif top:
        add("pass", f"Specific tags in the top 5: {', '.join(specific)}.")
    first_specific = next((i for i, k in enumerate(keys) if k not in GENERIC | OPINION | STATUS), n)
    for i, k in enumerate(keys):
        pos = i + 1
        if k in OPINION:
            add("warn" if pos > 10 else "fail",
                f"'{tags[i]}' (position {pos}) is an opinion tag. Let players apply it; it says nothing about what you play.")
        elif k in HARD_GENERIC and pos <= VALVE_DESCRIBE:
            add("fail", f"'{tags[i]}' (position {pos}) in the top 5. Valve's prioritization moves it down; it describes almost every game.")
        elif k in EMPTY and pos <= VALVE_DESCRIBE:
            add("warn", f"'{tags[i]}' (position {pos}) is a broad tag in the top 5. Move it below the sub-genre tags.")
        elif k in PARENT and i < first_specific:
            add("warn", f"'{tags[i]}' (position {pos}) is a parent genre above your first specific tag. Put the sub-genre first.")
        if k in STATUS:
            add("warn", f"'{tags[i]}' (position {pos}) is a status tag. Keep it only if it is true, and below the genre tags.")

    for i, k in enumerate(keys):
        t = known.get(k)
        if t:
            share, label = size_label(t["games"], bench["allGames"])
            add("info", f"{i + 1}. {t['name']}: {t['games']:,} games ({share:.1f}%, {label}), "
                        f"{t['shareAtLeast50']}% reached 50+ reviews (all games {bench['allShareAtLeast50']}%).")
        else:
            add("info", f"{i + 1}. {tags[i]}: not in the bundled list of {len(known)} genre tags. "
                        "Check the exact spelling in the Tag Wizard.")
    if n > VALVE_FILTER:
        add("info", f"Positions {VALVE_FILTER + 1} to {n} are outside the first {VALVE_FILTER}, which some store filters prioritize.")

    if args.similar:
        if not args.similar.is_file():
            ap.error(f"{args.similar} not found")
        games = []
        for line in args.similar.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#") or ":" not in line:
                continue
            name, rest = line.split(":", 1)
            gtags = [norm(t) for t in rest.split(",") if t.strip()]
            games.append((name.strip(), gtags))
        if len(games) < 3:
            add("warn", f"Only {len(games)} similar game(s). Use 3 to 5 at least; 10 or more for stable shares.")
        counts, names = {}, {}
        for _, gtags in games:
            for t in dict.fromkeys(gtags):
                counts[t] = counts.get(t, 0) + 1
        for line in args.similar.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                for t in line.split(":", 1)[1].split(","):
                    names.setdefault(norm(t), t.strip())
        mine = set(keys)
        if games:
            for t, c in sorted(counts.items(), key=lambda x: -x[1]):
                share = 100 * c / len(games)
                if share >= COMMON_SHARE and t not in mine:
                    add("warn", f"Missing: '{names[t]}' is on {c} of {len(games)} similar games ({share:.0f}%). Add it if it fits.")
            only = [tags[i] for i, k in enumerate(keys) if k not in counts]
            if only:
                add("info", f"Only you have: {', '.join(only)}. Fine if true and specific; check none is misleading.")

    fails = sum(r["status"] == "fail" for r in rows)
    warns = sum(r["status"] == "warn" for r in rows)
    if args.json:
        print(json.dumps({"tags": tags, "fails": fails, "warnings": warns, "checks": rows}, indent=2))
    else:
        for r in rows:
            print(f"[{r['status'].upper():4}] {r['text']}")
        print(f"\n{fails} failed, {warns} warning(s). Benchmark snapshot {bench['asOf']}, {bench['window']}.")
    sys.exit(1 if fails or (args.strict and warns) else 0)


if __name__ == "__main__":
    main()
