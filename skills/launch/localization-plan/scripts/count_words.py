#!/usr/bin/env python3
"""Count source-language words in a game's string files and check translation coverage.

Commands:
  count [ROOT]   Find string files, count source words per file (keys, placeholders and markup
                 left out), and estimate the cost per target language.
  check [ROOT]   Compare target-language files with the source: missing keys, empty strings,
                 strings left equal to the source, and placeholder or tag mismatches.

Formats it reads:
  .po / .pot   gettext, Godot and Unreal exports (msgctxt + msgid is the key; plurals read)
  .csv         Godot translation CSV (keys,en,fr,...), Unity Localization CSV export
               (Key,Id,...,English(en),French(fr)), Unreal string table CSV (Key,SourceString)
  .json        flat or nested key/value files, one language per file (en.json, locales/fr/ui.json),
               or a list of objects with a key and language fields
The language comes from the path (a folder or file name that is a language code, or a suffix
such as strings_fr.json), the CSV header, or the .po "Language:" header.

What counts as a word: a run of letters or digits after removing placeholders ({name}, {0},
{{var}}, %s, %1$d, %.2f, ${var}), markup (<b>, <color=#f00>, [b], [url=...], </>) and escapes
(\\n, \\t). Each CJK character counts as one word, as vendors charge for CJK sources.
Cost uses unique source strings (repeats are counted once); many vendors discount repeats.

Default rates per word (USD) are midpoints of Allcorrect Games' published EUR rates (page dated
5 March 2026) at the ECB rate of 23 November 2026, as used by the Manalens localization planner.
Use --rate or --rates with your own quote.

Exit codes: count: 0 ok, 1 no source strings found. check: 0 ok, 1 missing keys or placeholder
mismatches (or untranslated strings with --strict). 2 bad input.
Stdlib only.
"""
import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "Library", "Temp", "Logs", "obj", ".godot",
             ".import", "build", "Build", "Builds", "Binaries", "Intermediate", "Saved",
             "DerivedDataCache", "venv", ".venv", "__pycache__", "dist", "Packages"}
LOCALE_HINTS = {"locale", "locales", "localization", "localisation", "i18n", "l10n", "lang", "langs",
                "language", "languages", "translation", "translations", "strings", "stringtables",
                "text", "texts", "loc"}

# Steam language ids (Steam Hardware and Software Survey, October 2026, as in Manalens
# localization-planner.ts) and the file codes that map to them.
STEAM = {
    "english": ("English", 39.04, ["en"]),
    "schinese": ("Simplified Chinese", 21.98, ["zh", "zh_cn", "zh_hans", "zh_sg", "chs"]),
    "russian": ("Russian", 10.14, ["ru"]),
    "spanish": ("Spanish (Spain)", 4.83, ["es", "es_es"]),
    "brazilian": ("Portuguese (Brazil)", 4.46, ["pt_br"]),
    "german": ("German", 2.89, ["de"]),
    "japanese": ("Japanese", 2.47, ["ja", "jp"]),
    "french": ("French", 2.41, ["fr"]),
    "polish": ("Polish", 1.73, ["pl"]),
    "korean": ("Korean", 1.36, ["ko", "kr"]),
    "turkish": ("Turkish", 1.35, ["tr"]),
    "tchinese": ("Traditional Chinese", 1.30, ["zh_tw", "zh_hant", "zh_hk", "cht"]),
    "latam": ("Spanish (Latin America)", 0.89, ["es_419", "es_mx", "es_la", "es_us"]),
    "thai": ("Thai", 0.83, ["th"]),
    "ukrainian": ("Ukrainian", 0.73, ["uk", "ua"]),
    "italian": ("Italian", 0.64, ["it"]),
    "czech": ("Czech", 0.58, ["cs", "cz"]),
    "hungarian": ("Hungarian", 0.39, ["hu"]),
    "portuguese": ("Portuguese (Portugal)", 0.36, ["pt", "pt_pt"]),
    "swedish": ("Swedish", 0.27, ["sv"]),
    "dutch": ("Dutch", 0.27, ["nl"]),
    "danish": ("Danish", 0.22, ["da"]),
    "vietnamese": ("Vietnamese", 0.20, ["vi"]),
    "indonesian": ("Indonesian", 0.16, ["id"]),
    "finnish": ("Finnish", 0.15, ["fi"]),
    "romanian": ("Romanian", 0.13, ["ro"]),
    "norwegian": ("Norwegian", 0.12, ["no", "nb", "nn"]),
    "greek": ("Greek", 0.06, ["el"]),
    "bulgarian": ("Bulgarian", 0.05, ["bg"]),
    "arabic": ("Arabic", 0.00, ["ar"]),
    "malay": ("Malay", 0.00, ["ms"]),
}
CODE_TO_STEAM = {c: sid for sid, (_, _, codes) in STEAM.items() for c in codes}
LANG_NAMES = {"english": "en", "french": "fr", "german": "de", "spanish": "es", "italian": "it",
              "japanese": "ja", "korean": "ko", "russian": "ru", "polish": "pl", "turkish": "tr",
              "portuguese": "pt", "chinese": "zh", "chinese (simplified)": "zh_cn",
              "chinese (traditional)": "zh_tw"}
EUR_TO_USD = 1.0939
RATE_GROUPS = [
    (0.10, 0.14, ["french", "german", "spanish", "portuguese", "italian", "polish", "greek",
                  "hungarian", "romanian", "czech", "japanese"]),
    (0.09, 0.14, ["latam", "brazilian", "korean", "tchinese"]),
    (0.09, 0.12, ["arabic", "turkish", "indonesian", "vietnamese", "schinese"]),
    (0.10, 0.17, ["dutch", "swedish", "danish", "finnish", "norwegian"]),
    (0.06, 0.09, ["russian"]),
    (0.12, 0.13, ["malay"]),
]
DEFAULT_TARGETS = ["schinese", "russian", "spanish", "brazilian", "german", "japanese", "french", "korean"]

PLACEHOLDER = re.compile(
    r"\{\{\s*[\w.]+\s*\}\}"            # {{var}}
    r"|\$\{[^}]*\}"                    # ${var}
    r"|\{[\w.]*(?:[:,][^{}]*)?\}"      # {name} {0} {count:N0} {0,number}
    r"|%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?(?:hh|h|ll|l|L|z|j|t)?[sdifuxXeEgGcpo@]"  # printf
    r"|%[A-Za-z_][\w]*%"               # %PLAYER_NAME%
)
TAG = re.compile(r"</?[A-Za-z][\w.-]*(?:[ =][^<>]*)?/?>|</>|\[/?[A-Za-z_][\w]*(?:[= ][^\[\]]*)?\]")
ESCAPE = re.compile(r"\\[ntr\"'\\]")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]")
WORD = re.compile(r"[^\W_]+(?:['\u2019.-][^\W_]+)*", re.UNICODE)


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def norm_code(text):
    """'fr', 'pt-BR', 'zh_Hans', 'French(fr)', 'English' -> normalized code like 'pt_br', or None."""
    t = (text or "").strip()
    m = re.search(r"\(([A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,4})?)\)\s*$", t)
    if m:
        t = m.group(1)
    t = t.lower().replace("-", "_")
    if t in LANG_NAMES:
        return LANG_NAMES[t]
    if re.fullmatch(r"[a-z]{2,3}(?:_[a-z0-9]{2,4})?", t):
        base = t.split("_")[0]
        if t in CODE_TO_STEAM or base in CODE_TO_STEAM or base in {"en"}:
            return t
    return None


def same_lang(code, source):
    if code is None:
        return False
    return code == source or code.split("_")[0] == source.split("_")[0] and "_" not in source


def steam_id(code):
    return CODE_TO_STEAM.get(code) or CODE_TO_STEAM.get(code.split("_")[0]) if code else None


def strip_text(text):
    t = ESCAPE.sub(" ", text)
    t = PLACEHOLDER.sub(" ", t)
    t = TAG.sub(" ", t)
    return t


def count_words(text):
    t = strip_text(text)
    cjk = len(CJK.findall(t))
    t = CJK.sub(" ", t)
    return cjk + len(WORD.findall(t))


def placeholders(text):
    return Counter(m.group(0).replace(" ", "") for m in PLACEHOLDER.finditer(text))


def tags(text):
    out = Counter()
    for m in TAG.finditer(text):
        name = re.match(r"[<\[]/?([A-Za-z_][\w.-]*)?", m.group(0))
        closing = m.group(0)[1:2] == "/" or m.group(0) == "</>"
        out[("/" if closing else "") + ((name.group(1) or "") if name else "")] += 1
    return out


# ---------- path helpers ----------

def lang_from_path(path, root):
    """Return (language code or None, table id with the language part replaced)."""
    rel = path.relative_to(root)
    parts = list(rel.parts)
    for i, part in enumerate(parts[:-1]):
        c = norm_code(part)
        if c:
            parts[i] = "{lang}"
            return c, "/".join(parts)
    stem, suffix = Path(parts[-1]).stem, Path(parts[-1]).suffix
    c = norm_code(stem)
    if c:
        parts[-1] = "{lang}" + suffix
        return c, "/".join(parts)
    m = re.match(r"^(.*?)[._-]([A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,4})?)$", stem)
    if m and norm_code(m.group(2)):
        parts[-1] = m.group(1) + "_{lang}" + suffix
        return norm_code(m.group(2)), "/".join(parts)
    return None, "/".join(parts)


def looks_localized(path, root):
    parts = {p.lower().replace(" ", "") for p in path.relative_to(root).parts[:-1]}
    stem = path.stem.lower()
    return bool(parts & LOCALE_HINTS) or any(h in stem for h in LOCALE_HINTS) or lang_from_path(path, root)[0] is not None


def find_files(root):
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        if p.is_file() and p.suffix.lower() in {".po", ".pot", ".csv", ".json"}:
            yield p


# ---------- parsers: each returns a list of tables {lang, table, entries: {key: text}, fmt, meta} ----------

def unquote_po(s):
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.replace('\\"', '"').replace("\\\\", "\\")


def read_po_lines(path):
    raw = path.read_bytes()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return raw.decode(enc, errors="replace").splitlines()


def parse_po(path, root):
    """gettext entries: key (msgctxt + msgid) -> (source text, translation)."""
    items, cur, flags, field = [], {}, "", None

    def flush():
        nonlocal cur, flags, field
        if "msgid" in cur:
            items.append((cur, flags))
        cur, flags, field = {}, "", None

    has_str = lambda: any(k.startswith("msgstr") for k in cur)
    for line in read_po_lines(path):
        s = line.strip()
        if not s:
            if "msgid" in cur:
                flush()
            continue
        if s.startswith("#"):
            if has_str():
                flush()
            if s.startswith("#,"):
                flags += s
            continue
        m = re.match(r"^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+(\".*\")$", s)
        if m:
            if m.group(1) in ("msgctxt", "msgid") and has_str():
                flush()
            field = m.group(1)
            cur[field] = unquote_po(m.group(2))
        elif s.startswith('"') and field:
            cur[field] += unquote_po(s)
    flush()
    entries, fuzzy, header_lang = {}, set(), None
    for cur, fl in items:
        if cur["msgid"] == "" and "msgctxt" not in cur:
            m = re.search(r"Language:\s*([A-Za-z_-]+)", cur.get("msgstr", ""))
            if m:
                header_lang = norm_code(m.group(1))
            continue
        key = cur["msgctxt"] + "\x04" + cur["msgid"] if "msgctxt" in cur else cur["msgid"]
        src = cur["msgid"] + (" " + cur["msgid_plural"] if "msgid_plural" in cur else "")
        plural = [cur[k] for k in sorted(cur) if k.startswith("msgstr[")]
        tgt = cur.get("msgstr", "") if not plural else (" ".join(plural) if all(x.strip() for x in plural) else "")
        entries[key] = (src, tgt)
        if "fuzzy" in fl:
            fuzzy.add(key)
    plang, table = lang_from_path(path, root)
    pot = path.suffix.lower() == ".pot"
    return [{"fmt": "gettext .pot" if pot else "gettext .po", "lang": "template" if pot else (header_lang or plang),
             "table": table, "po": True, "entries": entries, "fuzzy": fuzzy, "path": path}]


def sniff_csv(text):
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.reader(io.StringIO(text), dialect))


def parse_csv(path, root, source):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows = sniff_csv(text)
    if len(rows) < 2:
        return []
    header = [h.strip() for h in rows[0]]
    low = [h.lower() for h in header]
    # Unreal string table: Key,SourceString[,Comment]
    if "key" in low and "sourcestring" in low:
        ki, si = low.index("key"), low.index("sourcestring")
        entries = {r[ki]: r[si] for r in rows[1:] if len(r) > max(ki, si) and r[ki]}
        plang, table = lang_from_path(path, root)
        return [{"fmt": "Unreal string table .csv", "lang": source, "table": table, "entries": entries, "path": path}]
    key_i = next((i for i, h in enumerate(low) if h in ("keys", "key", "id", "string_id", "stringid", "name")), None)
    if key_i is None:
        return []
    if low[key_i] == "id" and "key" in low:
        key_i = low.index("key")
    langs = [(i, norm_code(h)) for i, h in enumerate(header) if i != key_i and h.lower() not in ("id",)]
    langs = [(i, c) for i, c in langs if c]
    if not langs:
        return []
    fmt = "Godot translation .csv" if low[key_i] == "keys" else (
        "Unity Localization .csv" if any("(" in header[i] for i, _ in langs) else "translation .csv")
    rel = "/".join(path.relative_to(root).parts)
    out = []
    for i, c in langs:
        entries = {}
        for r in rows[1:]:
            if len(r) > key_i and r[key_i].strip():
                entries[r[key_i].strip()] = r[i] if len(r) > i else ""
        out.append({"fmt": fmt, "lang": c, "table": rel + "#csv", "entries": entries, "path": path, "multi": True})
    return out


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flatten(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flatten(v, f"{prefix}[{i}]")
    elif isinstance(obj, str):
        yield prefix, obj


def parse_json(path, root, source):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeDecodeError):
        return []
    plang, table = lang_from_path(path, root)
    # A list of {key, en, fr} or {key/id, value/text} objects.
    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
        keyf = next((f for f in ("key", "id", "Key", "Id", "name") if f in data[0]), None)
        if keyf:
            langf = [(f, norm_code(f)) for f in data[0] if f != keyf and norm_code(f)]
            if langf:
                rel = "/".join(path.relative_to(root).parts)
                return [{"fmt": "JSON table", "lang": c, "table": rel + "#json", "multi": True, "path": path,
                         "entries": {str(x.get(keyf)): x.get(f, "") or "" for x in data if x.get(keyf) is not None}}
                        for f, c in langf]
            valf = next((f for f in ("value", "text", "source", "Value", "Text") if f in data[0]), None)
            if valf and plang:
                return [{"fmt": "JSON list", "lang": plang, "table": table, "path": path,
                         "entries": {str(x.get(keyf)): str(x.get(valf, "")) for x in data if x.get(keyf) is not None}}]
        return []
    if not isinstance(data, dict):
        return []
    # {"en": {...}, "fr": {...}} in one file
    codes = {k: norm_code(k) for k in data}
    if data and all(codes.values()) and all(isinstance(v, dict) for v in data.values()):
        rel = "/".join(path.relative_to(root).parts)
        return [{"fmt": "JSON (languages as top keys)", "lang": codes[k], "table": rel + "#json", "multi": True,
                 "path": path, "entries": dict(flatten(v))} for k, v in data.items()]
    if plang is None and not looks_localized(path, root):
        return []
    entries = {k: v for k, v in flatten(data) if not k.startswith(("$schema", "@"))}
    if not entries:
        return []
    return [{"fmt": "JSON", "lang": plang, "table": table, "entries": entries, "path": path}]


def load_tables(root, source, include_all):
    tables, skipped = [], []
    for p in find_files(root):
        suf = p.suffix.lower()
        if suf in (".po", ".pot"):
            tables += parse_po(p, root)
        elif suf == ".csv":
            got = parse_csv(p, root, source)
            if got:
                tables += got
            else:
                skipped.append(p)
        elif suf == ".json":
            if not include_all and not looks_localized(p, root):
                continue
            got = parse_json(p, root, source)
            if got:
                tables += got
            elif looks_localized(p, root):
                skipped.append(p)
    return tables, skipped


def source_entries(tables, source):
    """Source strings per table id: {table: {key: text}} and where they came from."""
    by_table = defaultdict(dict)
    origin = {}
    for t in tables:
        tid = t["table"]
        if t.get("po"):
            if t["lang"] == "template" or same_lang(t["lang"], source):
                by_table[tid].update({k: v[0] for k, v in t["entries"].items()})
                origin.setdefault(tid, t)
        elif same_lang(t["lang"], source):
            by_table[tid].update(t["entries"])
            origin.setdefault(tid, t)
    # .po tables with no source in the same table: use a .pot in the same or a parent folder
    # (same file stem first, else the only one), else the msgid of the first file.
    pots = [t for t in tables if t.get("po") and t["lang"] == "template"]
    for t in tables:
        if not t.get("po") or t["table"] in by_table:
            continue
        cands = [x for x in pots if x["path"].parent in [t["path"].parent, *t["path"].parents]]
        pick = [x for x in cands if x["path"].stem == t["path"].stem] or (cands if len(cands) == 1 else [])
        if pick:
            by_table[t["table"]] = {k: v[0] for k, v in pick[0]["entries"].items()}
            origin[t["table"]] = pick[0]
            t["template_table"] = pick[0]["table"]
    for t in tables:
        if t.get("po") and t["table"] not in by_table:
            by_table[t["table"]] = {k: v[0] for k, v in t["entries"].items()}
            origin[t["table"]] = t
    return by_table, origin


def default_rate(sid):
    for lo, hi, ids in RATE_GROUPS:
        if sid in ids:
            return round((lo + hi) / 2 * EUR_TO_USD, 3)
    return None


def parse_rates(text):
    out = {}
    for part in filter(None, (x.strip() for x in (text or "").split(","))):
        if "=" not in part:
            die(f"--rates item '{part}' must look like schinese=0.11")
        k, v = part.split("=", 1)
        sid = k.strip() if k.strip() in STEAM else steam_id(norm_code(k))
        if not sid:
            die(f"--rates: unknown language '{k}'")
        out[sid] = float(v)
    return out


def cmd_count(a):
    root = Path(a.root).resolve()
    if not root.is_dir():
        die(f"{root} is not a folder")
    source = norm_code(a.source) or die(f"unknown source language '{a.source}'")
    tables, skipped = load_tables(root, source, a.all_json)
    src, origin = source_entries(tables, source)
    rows, all_texts, seen_paths = [], [], set()
    for tid, entries in sorted(src.items()):
        if origin[tid]["path"] in seen_paths and not origin[tid].get("multi"):
            continue
        seen_paths.add(origin[tid]["path"])
        texts = [v for v in entries.values() if v and v.strip()]
        words = sum(count_words(v) for v in texts)
        all_texts += texts
        t = origin[tid]
        rows.append((str(t["path"].relative_to(root)), t["fmt"], len(texts), words))
    if not rows:
        print("No source strings found. Formats read: .po/.pot, Godot/Unity/Unreal .csv, JSON. "
              "Pass the folder that holds them, or --all-json for JSON outside locale folders.")
        return 1
    total_words = sum(r[3] for r in rows)
    unique = {}
    for t in all_texts:
        unique.setdefault(t.strip(), count_words(t))
    unique_words = sum(unique.values())
    store_words = a.store_words
    if a.store_text:
        store_words = count_words(Path(a.store_text).read_text(encoding="utf-8"))
    rates = parse_rates(a.rates)
    targets = [x.strip() for x in a.languages.split(",")] if a.languages else DEFAULT_TARGETS
    bad = [x for x in targets if x not in STEAM]
    if bad:
        die("unknown Steam language id(s): " + ", ".join(bad) + ". Use ids like " + ", ".join(list(STEAM)[1:6]))
    report = {"root": str(root), "source": source, "files": [], "total_strings": sum(r[2] for r in rows),
              "total_words": total_words, "unique_strings": len(unique), "unique_words": unique_words,
              "store_words": store_words, "languages": []}
    print(f"Source language: {source}. Files with source strings:")
    print(f"  {'file':<58} {'format':<26} {'strings':>8} {'words':>8}")
    for r in rows:
        print(f"  {r[0]:<58} {r[1]:<26} {r[2]:>8} {r[3]:>8}")
        report["files"].append({"file": r[0], "format": r[1], "strings": r[2], "words": r[3]})
    print(f"  {'TOTAL':<58} {'':<26} {report['total_strings']:>8} {total_words:>8}")
    print(f"Unique strings: {len(unique)}, unique words: {unique_words} (cost below uses unique words)")
    if skipped:
        print("Skipped (no key column or language columns found): " + ", ".join(str(p.relative_to(root)) for p in skipped))
    print(f"\nEstimated cost per language (USD){' plus store page of %d words' % store_words if store_words else ''}:")
    print(f"  {'language':<26} {'Steam share':>11} {'rate':>6} {'game':>9} {'store':>8}  rate source")
    for sid in targets:
        name, share, _ = STEAM[sid]
        rate = a.rate if a.rate is not None else rates.get(sid, default_rate(sid))
        src_note = "--rate" if a.rate is not None else ("--rates" if sid in rates else ("Allcorrect midpoint" if rate is not None else "none: pass --rates"))
        game = None if rate is None else unique_words * rate
        store = None if rate is None or not store_words else store_words * rate
        print(f"  {name:<26} {share:>10.2f}% {('%.3f' % rate) if rate is not None else '-':>6} "
              f"{('%.0f' % game) if game is not None else '-':>9} {('%.0f' % store) if store is not None else '-':>8}  {src_note}")
        report["languages"].append({"id": sid, "name": name, "survey_share": share, "rate": rate,
                                    "game_cost": game, "store_cost": store, "rate_source": src_note})
    print("\nShares: Steam Hardware and Software Survey, October 2026 (share of respondents).")
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {a.json}")
    return 0


def cmd_check(a):
    root = Path(a.root).resolve()
    if not root.is_dir():
        die(f"{root} is not a folder")
    source = norm_code(a.source) or die(f"unknown source language '{a.source}'")
    tables, _ = load_tables(root, source, a.all_json)
    src, origin = source_entries(tables, source)
    only = {norm_code(x) for x in a.targets.split(",")} if a.targets else None
    errors = warnings = 0
    checked = 0
    for t in sorted(tables, key=lambda x: (x["table"], x["lang"] or "")):
        lang = t["lang"]
        if lang in (None, "template") or same_lang(lang, source):
            continue
        if only and lang not in only and lang.split("_")[0] not in only:
            continue
        base = src.get(t["table"], {})
        if not base:
            print(f"? {t['path'].relative_to(root)} ({lang}): no source file found for this table")
            continue
        checked += 1
        missing, empty, same, ph, tg, extra = [], [], [], [], [], []
        for key, stext in base.items():
            if not stext or not stext.strip():
                continue
            if t.get("po"):
                if key not in t["entries"]:
                    missing.append(key); continue
                ttext = t["entries"][key][1]
            else:
                if key not in t["entries"]:
                    missing.append(key); continue
                ttext = t["entries"][key]
            if not ttext or not ttext.strip():
                empty.append(key); continue
            if ttext.strip() == stext.strip() and count_words(stext) > 0:
                same.append(key)
            if placeholders(stext) != placeholders(ttext):
                ph.append((key, sorted(placeholders(stext).elements()), sorted(placeholders(ttext).elements())))
            elif tags(stext) != tags(ttext):
                tg.append((key, sorted(tags(stext).elements()), sorted(tags(ttext).elements())))
        for key in t["entries"]:
            if key not in base:
                extra.append(key)
        total = sum(1 for v in base.values() if v and v.strip())
        done = total - len(missing) - len(empty)
        pct = 100 * done / total if total else 100
        label = f"{t['path'].relative_to(root)} [{lang}]"
        print(f"\n{label}: {done}/{total} translated ({pct:.0f}%)")
        show = lambda k: k.replace("\x04", " | ")
        for k in missing[:a.limit]:
            print(f"  FAIL missing key: {show(k)}")
        for k in empty[:a.limit]:
            print(f"  FAIL empty: {show(k)}")
        for k, s, d in ph[:a.limit]:
            print(f"  FAIL placeholders differ: {show(k)}: source {s}, translation {d}")
        for k, s, d in tg[:a.limit]:
            print(f"  WARN markup differs: {show(k)}: source {s}, translation {d}")
        for k in same[:a.limit]:
            print(f"  WARN same as source: {show(k)}")
        for k in extra[:a.limit]:
            print(f"  WARN key not in source (stale?): {show(k)}")
        fz = [k for k in t.get("fuzzy", ()) if k in base]
        for k in fz[:a.limit]:
            print(f"  WARN fuzzy (needs review): {show(k)}")
        more = max(0, len(missing) - a.limit) + max(0, len(empty) - a.limit) + max(0, len(ph) - a.limit)
        if more:
            print(f"  ... and {more} more failures (raise --limit)")
        errors += len(missing) + len(empty) + len(ph)
        warnings += len(same) + len(tg) + len(extra) + len(fz)
    if not checked:
        print("No target-language files found next to the source files. Nothing to check.")
        return 0
    print(f"\n{errors} failure(s), {warnings} warning(s) in {checked} target file(s)")
    return 1 if errors or (a.strict and warnings) else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn, hlp in (("count", cmd_count, "count source words and estimate cost"),
                          ("check", cmd_check, "check target files against the source")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("root", nargs="?", default=".", help="folder to search (default: current folder)")
        s.add_argument("--source", default="en", help="source language code (default en)")
        s.add_argument("--all-json", action="store_true", help="also read JSON files outside locale folders")
        s.set_defaults(func=fn)
        if name == "count":
            s.add_argument("--rate", type=float, help="one USD rate per word for every language")
            s.add_argument("--rates", default="", help="per language rates, e.g. 'schinese=0.11,ja=0.14'")
            s.add_argument("--languages", default="", help="Steam language ids to price (default: "
                           + ",".join(DEFAULT_TARGETS) + ")")
            s.add_argument("--store-words", type=int, default=0, help="store page word count, for the store-only cost")
            s.add_argument("--store-text", help="a text or Markdown file with the store page text to count")
            s.add_argument("--json", help="also write the report as JSON to this path")
        else:
            s.add_argument("--targets", default="", help="only check these language codes, e.g. 'fr,de'")
            s.add_argument("--limit", type=int, default=20, help="max lines per problem type per file (default 20)")
            s.add_argument("--strict", action="store_true", help="fail on warnings too")
    a = p.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
