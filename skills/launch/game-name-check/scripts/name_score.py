#!/usr/bin/env python3
"""Score candidate game names offline. No network requests.

Each name gets six sub-scores from 0 to 100 and a weighted total:

  length       core name (before a colon or " - ") of 4 to 20 characters is best;
               over 30 characters fails the App Store and Google Play name limit
  words        1 to 3 words is best; 5 or more is hard to remember
  spelling     penalties for digits, apostrophes or symbols inside words, doubled
               letters, words from a homophone list, and spellings that do not match
               the sound (ph, ae, y as a vowel, silent k or w at the start)
  search       how unique the words are: common English words and generic game words
               (legend, quest, simulator ...) lower the score; an invented word raises it
  handles      whether the plain handle (lowercase letters and digits) fits the length
               and character rules of X, Instagram, TikTok, YouTube, Bluesky, a subreddit,
               a Discord custom invite and a .com label
  similarity   100 minus the closest match to a list of existing game titles, by edit
               distance and shared words (exact and close matches are flagged)

Total = 0.7 x the weighted average + 0.3 x the lowest sub-score, capped at 20 for an exact
match and 60 for a close match with an existing title.

The scores are heuristics for comparing a shortlist. They do not tell you whether a name
is free to use: run the checklist in the skill for that, and ask a lawyer for clearance.

Examples:
  python3 name_score.py "Lantern Tide" "Hollow Knight Farm" "Kn1ght's Quest"
  python3 name_score.py --file candidates.txt --existing steam-titles.txt --format md
  python3 name_score.py --file candidates.txt --existing titles.txt --fail-below 60

Exit codes: 0 ok; 1 bad input (no names, missing file); 2 a name scored under --fail-below
or matched an existing title exactly (with --fail-on-exact).
"""
import argparse
import json
import re
import sys
import unicodedata

WEIGHTS = {"length": 0.10, "words": 0.10, "spelling": 0.20, "search": 0.20, "handles": 0.15, "similarity": 0.25}

MOBILE_MAX = 30  # Apple App Store and Google Play name limit (store help pages, read by Manalens 2026-11-18)

# Handle rules for the plain handle form (lowercase a-z and 0-9). Sources and dates: references/handles.md.
PLATFORMS = [
    ("X", 5, 15),            # 5 is the safe minimum; X words it as "more than 4"
    ("Instagram", 1, 30),    # not published by Instagram; 30 is what the app enforces
    ("TikTok", 2, 24),
    ("YouTube", 3, 30),
    ("Bluesky", 3, 18),      # name before .bsky.social
    ("subreddit", 3, 21),
    ("Discord invite", 1, 25),  # custom invite link, needs Server Boost Level 3
    ("domain label", 1, 63),    # one DNS label, RFC 1035
]

# About 300 of the most frequent English words, plus common short nouns that show up in titles.
COMMON = set("""
a about above across act after again against age ago air all almost alone along already also always am
among an and animal another answer any are area around art as ask at away back bad ball be bear beautiful
became because become bed been before began begin behind being believe below best better between big bird
black blood blue boat body book both box boy bring brother brought build built but buy by call came can
car care carry case cat cause center change child children city class clear close cold color come common
complete could country course cut dark day dead deep did different do does dog done door down draw dream
during each early earth east eat end enough even ever every eye face fact fall family far farm fast father
fear feel feet few field fight figure fill final find fine fire first fish five fly follow food foot for
force form found four free friend from front full game garden gave get girl give go god gold good got great
green ground group grow had half hand happen happy hard has have he head hear heard heart help her here
high him his hold home horse hot hour house how however human hundred i ice idea if important in inside
into is island it its just keep kind king knew know land large last late later lead learn least leave left
less let life light like line list little live long look lost lot love low machine made main make man many
map may me mean men might mind miss money moon more morning most mother mountain move much music must my
name near need never new next night no north not nothing now number of off often oh old on once one only
open or order other our out over own page paper part party pass past people perhaps person picture piece
place plan plant play point power present problem pull put question quick quite rain ran rather reach read
ready real red remember rest right river road rock room round run said same saw say school sea second see
seem self sentence set several shall shape she ship short should show side simple since sing sister sit
six size sky sleep slow small snow so some something song soon sound south space speak special stand star
start state stay step still stone stop story street strong study such summer sun sure surface system take
talk tell ten than that the their them then there these they thing think this those though thought three
through time tiny to today together told too took top toward town tree true try turn two under until up
upon us use very voice wait walk wall want war warm was watch water way we well went were west what wheel
when where which while white who whole why wild will wind window winter with without woman wood word work
world would write year yes yet you young your
""".split())

# Words so common in game titles that they add genre but no uniqueness.
GAME_GENERIC = set("""
adventure adventures age arena battle battles blade chronicles clash craft crusade defense defender
dungeon dungeons empire empires epic escape fantasy fate frontier galaxy hero heroes kingdom kingdoms
knight knights legend legends legacy lord lords magic mystery quest quests rage realm realms rise royal
saga shadow shadows simulator simulation souls story survival survivor survivors tactics tale tales
tower tycoon void wars warrior warriors world worlds zero online deluxe edition remastered
""".split())

# Words that sound like another word with a different spelling. A listener may type either.
HOMOPHONES = set("""
night knight nite knite write right rite wright write site sight cite pair pear pare peer pier hole whole
knot not knew new gnu sole soul sail sale tail tale rain reign rein their there whose whos weight wait
way weigh weather whether which witch break brake flower flour hour our knows nose know no
meet meat sea see son sun steal steel throne thrown wood would bare bear by buy bye die dye dew due
fair fare grate great hare hair heal heel hear here mail male morning mourning plain plane prey pray
road rode rowed seen scene so sew sow stair stare toe tow waist waste wear where week weak won one
""".split())


def ascii_fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def match_form(name):
    """Lowercase, accents and punctuation removed, words kept (as the Manalens name checker does)."""
    t = ascii_fold(name).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def handle_of(name):
    return re.sub(r"[^a-z0-9]", "", ascii_fold(name).lower())


def core_of(name):
    return re.split(r"\s*:\s*|\s+[-|]\s+", name.strip(), maxsplit=1)[0].strip()


def clamp(x):
    return max(0, min(100, int(round(x))))


def score_length(name, notes):
    core = core_of(name)
    n = len(core)
    s = 100
    if n < 2:
        s = 0
        notes.append("under 2 characters (Apple minimum)")
    elif n < 4:
        s = 70
    elif n > 20:
        s = 100 - (n - 20) * 5
    if len(name) > MOBILE_MAX:
        if n <= MOBILE_MAX:
            notes.append(f"full name over {MOBILE_MAX} characters; core fits, keep the subtitle optional on mobile")
        else:
            s = min(s, 30)
            notes.append(f"core name over {MOBILE_MAX} characters (App Store and Google Play limit)")
    return clamp(s)


def score_words(name, notes):
    n = len(match_form(core_of(name)).split())
    table = {0: 0, 1: 100, 2: 100, 3: 90, 4: 65}
    s = table.get(n, 40)
    if n >= 5:
        notes.append(f"{n} words in the core name")
    return s


def score_spelling(name, notes):
    s = 100
    core = core_of(name)
    if re.search(r"[0-9]", core):
        if re.search(r"[A-Za-z][0-9]|[0-9][A-Za-z]", core):
            s -= 40
            notes.append("letters and digits mixed in a word")
        else:
            s -= 15
            notes.append("a number: say it or spell it?")
    if re.search(r"[A-Za-z]['’][A-Za-z]{2,}", core):
        s -= 20
        notes.append("apostrophe inside a word")
    if re.search(r"[^A-Za-z0-9\s:'’&!?.,-]", ascii_fold(core) if ascii_fold(core) else core):
        s -= 20
        notes.append("unusual symbols")
    if ascii_fold(core) != core:
        s -= 15
        notes.append("accented or non-ASCII letters (hard to type, dropped from handles)")
    if re.search(r"(.)\1\1", core.lower()):
        s -= 20
        notes.append("triple letter")
    words = match_form(core).split()
    doubled = [w for w in words if re.search(r"([a-z])\1", w) and w not in COMMON]
    if doubled:
        s -= 5 * min(2, len(doubled))
        notes.append("doubled letter in " + ", ".join(doubled[:2]))
    homo = [w for w in words if w in HOMOPHONES]
    if homo:
        s -= 12 * min(2, len(homo))
        notes.append("homophone: " + ", ".join(homo[:2]))
    odd_hits = 0
    odd = []
    for w in words:
        if w in COMMON or w in GAME_GENERIC:
            continue
        hits = sum(1 for pat in ODD_SPELLING if re.search(pat, w))
        if hits:
            odd_hits += hits
            odd.append(w)
    if odd:
        s -= 12 * min(4, odd_hits)
        notes.append("spelling may not match the sound: " + ", ".join(odd[:2]))
    if ALL_CAPS.match(core) and len(re.sub(r"[^A-Za-z]", "", core)) > 3:
        s -= 10
        notes.append("ALL CAPS (Google Play allows it only as part of the brand)")
    return clamp(s)


# Letter patterns a listener is unlikely to guess from the sound.
ODD_SPELLING = [r"ph", r"ae", r"^kn", r"^wr", r"^gn", r"[^aeiou]y[^aeiou]", r"q(?!u)", r"xx|zz|kk|yy",
                r"[0-9]", r"(.)\1\1"]
ALL_CAPS = re.compile(r"^[^a-z]*[A-Z][^a-z]*$")


def score_search(name, notes):
    words = match_form(core_of(name)).split()
    if not words:
        return 0
    common = [w for w in words if w in COMMON]
    generic = [w for w in words if w in GAME_GENERIC]
    distinct = [w for w in words if w not in COMMON and w not in GAME_GENERIC and len(w) >= 3]
    s = 100 - 60 * len(common) / len(words) - 70 * len(generic) / len(words)
    if distinct:
        s += 15
    if len(words) == 1 and (common or generic):
        s = min(s, 20)
        notes.append("a single common or generic word: search returns everything else first")
    elif not distinct:
        notes.append("only common or generic words: hard to find by search")
    if generic:
        notes.append("generic game words: " + ", ".join(generic[:3]))
    return clamp(s)


def score_handles(name, notes):
    h = handle_of(core_of(name))
    if not h:
        notes.append("no letters or digits for a handle")
        return 0, []
    fails = [p for p, lo, hi in PLATFORMS if not lo <= len(h) <= hi]
    s = 100 * (len(PLATFORMS) - len(fails)) / len(PLATFORMS)
    if fails:
        notes.append(f"handle '{h}' ({len(h)} chars) does not fit: " + ", ".join(fails))
    if h[0].isdigit():
        s -= 10
        notes.append("handle starts with a digit")
    return clamp(s), fails


def levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similarity(a, b):
    """Return (score 0..1, kind) between two names. kind is exact, close or ''."""
    ma, mb = match_form(a), match_form(b)
    if not ma or not mb:
        return 0.0, ""
    if ma == mb:
        return 1.0, "exact"
    wa, wb = ma.split(), mb.split()
    sa, sb = set(wa), set(wb)
    shared = len(sa & sb)
    # Same rule as the Manalens checker: one contains the other, or 60% of the words are shared.
    close = mb in ma and len(wb) >= 2 or ma in mb and len(wa) >= 2 or shared / max(len(sa), len(sb)) >= 0.6
    ca, cb = ma.replace(" ", ""), mb.replace(" ", "")
    edit = 1 - levenshtein(ca, cb) / max(len(ca), len(cb))
    jacc = shared / len(sa | sb)
    sim = max(edit, jacc)
    if edit >= 0.8:
        close = True
    return sim, "close" if close else ""


def score_similarity(name, existing, notes):
    if not existing:
        return 100, None
    order = {"exact": 2, "close": 1, "": 0}
    best = max(((*similarity(name, t), t) for t in existing), key=lambda x: (order[x[1]], x[0]))
    sim, kind, title = best
    s = 100 * (1 - sim)
    if kind == "exact":
        s = 0
        notes.append(f"EXACT match: {title}")
    elif kind == "close":
        s = min(s, 40)
        notes.append(f"close to: {title}")
    return clamp(s), {"title": title, "kind": kind or "none", "similarity": round(sim, 2)}


def score(name, existing):
    notes = []
    sub = {
        "length": score_length(name, notes),
        "words": score_words(name, notes),
        "spelling": score_spelling(name, notes),
        "search": score_search(name, notes),
    }
    sub["handles"], fails = score_handles(name, notes)
    sub["similarity"], nearest = score_similarity(name, existing, notes)
    # Weighted average, pulled down by the weakest sub-score, so one bad problem is not hidden.
    total = 0.7 * sum(sub[k] * w for k, w in WEIGHTS.items()) + 0.3 * min(sub.values())
    if nearest and nearest["kind"] == "exact":
        total = min(total, 20)
    elif nearest and nearest["kind"] == "close":
        total = min(total, 60)
    total = clamp(total)
    return {"name": name, "handle": handle_of(core_of(name)), "total": total, **sub,
            "nearest": nearest, "handle_fails": fails, "notes": notes}


def read_lines(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    except OSError as e:
        sys.exit(f"error: cannot read {path}: {e}")


def to_markdown(rows, with_existing):
    cols = ["Name", "Total", "Length", "Words", "Spelling", "Search", "Handles", "Similarity", "Handle", "Notes"]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        sim = str(r["similarity"]) if with_existing else "n/a"
        notes = "; ".join(r["notes"]).replace("|", "/") or "none"
        out.append(f"| {r['name']} | **{r['total']}** | {r['length']} | {r['words']} | {r['spelling']} | "
                   f"{r['search']} | {r['handles']} | {sim} | {r['handle']} | {notes} |")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("names", nargs="*", help="candidate names (quote names with spaces)")
    p.add_argument("--file", help="file with one candidate name per line (# starts a comment)")
    p.add_argument("--existing", help="file with existing game titles, one per line, to compare against")
    p.add_argument("--format", choices=["md", "json", "text"], default="md", help="output format (default md)")
    p.add_argument("--fail-below", type=int, metavar="N", help="exit 2 if any name totals under N")
    p.add_argument("--fail-on-exact", action="store_true", help="exit 2 if any name matches an existing title exactly")
    args = p.parse_args()

    names = list(args.names) + (read_lines(args.file) if args.file else [])
    names = [n for n in dict.fromkeys(n.strip() for n in names) if n]
    if not names:
        p.print_usage(sys.stderr)
        sys.exit("error: give at least one name, or --file")
    existing = read_lines(args.existing) if args.existing else []

    rows = sorted((score(n, existing) for n in names), key=lambda r: -r["total"])
    if args.format == "json":
        print(json.dumps(rows, indent=2))
    elif args.format == "text":
        for r in rows:
            print(f"{r['total']:3d}  {r['name']}  ({'; '.join(r['notes']) or 'no notes'})")
    else:
        print(to_markdown(rows, bool(existing)))
        if not existing:
            print("\nSimilarity not scored: pass --existing with titles from your Steam and itch.io searches.")

    failed = False
    if args.fail_below is not None:
        low = [r["name"] for r in rows if r["total"] < args.fail_below]
        if low:
            print(f"\nFAIL: under {args.fail_below}: " + ", ".join(low), file=sys.stderr)
            failed = True
    if args.fail_on_exact:
        exact = [r["name"] for r in rows if r["nearest"] and r["nearest"]["kind"] == "exact"]
        if exact:
            print("\nFAIL: exact match with an existing title: " + ", ".join(exact), file=sys.stderr)
            failed = True
    sys.exit(2 if failed else 0)


if __name__ == "__main__":
    main()
