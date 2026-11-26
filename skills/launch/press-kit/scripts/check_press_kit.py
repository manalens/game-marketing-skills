#!/usr/bin/env python3
"""Check a press kit folder written by the press-kit skill.

Reads <press>/index.md (or index.html), <press>/factsheet.md and <press>/assets.csv.
Fails (exit 1) when:
  - a required section of index.md or a fact sheet field is missing or empty;
  - a description is outside its word limit, or there are not 4 to 6 features;
  - an award line has no link (awards must be verifiable), unless the section says "None yet";
  - placeholder text is left (TODO, TBD, FIXME, XXX, lorem ipsum, [Your name], <appid>, Your Game);
  - a link to the Steam page, itch.io or the game's website does not carry utm_source=press and a
    lower-case utm_campaign, or carries a utm_medium (a kit link is a plain referral link,
    docs/LINKS.md);
  - an asset in assets.csv is missing, is below its minimum size (read with ffprobe), or the set is
    incomplete: 6 to 12 screenshots without baked text, key art with and without logo, a logo with a
    transparent background, a GIF, an MP4 trailer, and a trailer embed link;
  - the Download section does not link to a .zip in the folder (use --zip to build it).

assets.csv columns: path,kind,with_logo,text_free,alt
  kind is one of screenshot, keyart, logo, icon, gif, trailer. Paths are relative to the folder.

Needs ffprobe (part of ffmpeg) for the asset checks. Use --no-assets to skip them.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SECTIONS = [  # index.md headings, matched by prefix, case-insensitive, in presskit() order
    "fact sheet", "description", "features", "history", "videos", "images", "logo and key art",
    "awards", "team", "streaming and monetisation", "keys", "embargo", "contact", "download",
]
DESCRIPTIONS = {  # ### headings under "Description": (min words, max words)
    "one sentence": (5, 35),
    "one paragraph": (40, 120),
    "long": (150, 500),
}
ONE_SENTENCE_MAX_CHARS = 240
FACTS = ["developer", "publisher", "release date", "platforms", "price", "website", "socials",
         "press contact"]
MINS = {  # kind: (min width, min height)
    "screenshot": (1920, 1080), "keyart": (1920, 1080), "logo": (1000, 0), "icon": (256, 256),
    "gif": (480, 0), "trailer": (1280, 720),
}
ALPHA = {"rgba", "rgba64be", "rgba64le", "ya8", "ya16be", "ya16le", "bgra", "argb", "abgr",
         "yuva420p", "yuva444p"}
PLACEHOLDER = [
    re.compile(r"\b(TODO|TBD|FIXME|XXX)\b"),
    re.compile(r"lorem ipsum", re.I),
    re.compile(r"(?<![!\]])\[[^\]\n]{1,80}\](?![(:\[])"),
    re.compile(r"<(your|game|appid|app id|name|date|link|url|email|studio)[^>]*>", re.I),
    re.compile(r"\byour (game|studio|name)\b", re.I),
    re.compile(r"\bexample\.(com|org)\b", re.I),
]
URL = re.compile(r"https?://[^\s)<>\"']+")
FILE_LINK = re.compile(r"\.(zip|mp4|mov|webm|png|jpe?g|gif|pdf)$", re.I)
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’.-]*")


class HtmlToMd(HTMLParser):
    """Turn index.html into heading lines and text, enough for the checks."""

    def __init__(self):
        super().__init__()
        self.out, self.prefix = [], ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3"):
            self.out.append("\n" + "#" * int(tag[1]) + " ")
        elif tag in ("p", "li", "div", "br", "tr"):
            self.out.append("\n- " if tag == "li" else "\n")
        if tag == "a" and a.get("href"):
            self.out.append(f" ({a['href']}) ")
        if tag in ("iframe", "video", "source", "img") and a.get("src"):
            self.out.append(f" ({a['src']}) ")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "p", "li"):
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data.replace("\n", " "))


def read_index(folder):
    md, html = folder / "index.md", folder / "index.html"
    if md.exists():
        return md, md.read_text(encoding="utf-8")
    if html.exists():
        p = HtmlToMd()
        p.feed(html.read_text(encoding="utf-8"))
        return html, "".join(p.out)
    return None, ""


def sections(text, level):
    """Map heading text (lower case) at this level to its body."""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if m and len(m.group(1)) <= level:
            cur = m.group(2).strip().lower() if len(m.group(1)) == level else None
            if cur is not None:
                out[cur] = []
            continue
        if cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def find(secs, key):
    for name, body in secs.items():
        if name.startswith(key):
            return name, body
    return None, None


def words(text):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return len(WORD.findall(text))


def facts(text):
    out = {}
    for m in re.finditer(r"^\s*[-*]\s*\*\*([^*:]+):?\*\*:?\s*(.*)$", text, re.M):
        out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def check_text(path, text, errors):
    for i, line in enumerate(text.splitlines(), 1):
        for rx in PLACEHOLDER:
            m = rx.search(line)
            if m:
                errors.append(f"{path.name}:{i}: placeholder text '{m.group(0)}'")
                break


def check_links(path, text, website_host, errors):
    for url in URL.findall(text):
        url = url.rstrip(".,;")
        u = urlparse(url)
        host = u.netloc.lower().removeprefix("www.")
        own = (host == "store.steampowered.com" and "/app/" in u.path) or host.endswith("itch.io") \
            or (website_host and (host == website_host or host.endswith("." + website_host)))
        if not own:
            continue
        if FILE_LINK.search(u.path):
            continue  # a direct file download (the ZIP, an MP4, a PNG): no page visit to count
        for problem in link_problems(parse_qs(u.query)):
            errors.append(f"{path.name}: {problem}: {url}")


def link_problems(q):
    """UTM problems of one press kit link (docs/LINKS.md): source press, a beat, no medium."""
    problems = []
    source, campaign = q.get("utm_source", [""])[0], q.get("utm_campaign", [""])[0]
    if source != "press":
        problems.append(f"link has utm_source '{source}', use press" if source else "link without utm_source")
    if not campaign:
        problems.append("link without utm_campaign")
    elif campaign != campaign.lower():
        problems.append("utm_campaign must be lower case")
    if "utm_medium" in q:
        problems.append("link has a utm_medium; a press kit link has none")
    return problems


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,pix_fmt,codec_name", "-of", "json", str(path)],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    streams = json.loads(r.stdout or "{}").get("streams") or []
    return streams[0] if streams else None


def yes(value):
    return (value or "").strip().lower() in ("yes", "y", "true", "1")


def check_assets(folder, errors, warnings):
    manifest = folder / "assets.csv"
    if not manifest.exists():
        errors.append("assets.csv: not found")
        return
    with manifest.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    need = {"path", "kind", "with_logo", "text_free", "alt"}
    if not rows or not need <= set(rows[0].keys()):
        errors.append(f"assets.csv: needs columns {','.join(sorted(need))} and at least one row")
        return
    count = {k: 0 for k in MINS}
    keyart_logo = keyart_clean = transparent_logo = mp4 = 0
    for n, row in enumerate(rows, 2):
        kind, rel = row["kind"].strip().lower(), row["path"].strip()
        where = f"assets.csv:{n} {rel}"
        if kind not in MINS:
            errors.append(f"{where}: kind '{kind}' is not one of {', '.join(MINS)}")
            continue
        count[kind] += 1
        path = folder / rel
        if not path.is_file():
            errors.append(f"{where}: file not found")
            continue
        if kind != "trailer" and not row["alt"].strip():
            errors.append(f"{where}: no alt text")
        info = probe(path)
        if not info:
            errors.append(f"{where}: ffprobe cannot read it")
            continue
        w, h = int(info.get("width") or 0), int(info.get("height") or 0)
        mw, mh = MINS[kind]
        if w < mw or h < mh:
            errors.append(f"{where}: {w}x{h} is below the {kind} minimum {mw}x{mh}")
        if kind == "screenshot" and not yes(row["text_free"]):
            errors.append(f"{where}: screenshots must have no baked-in text (text_free=yes)")
        if kind == "keyart":
            if yes(row["with_logo"]):
                keyart_logo += 1
            else:
                keyart_clean += 1
        if kind == "logo":
            pix = info.get("pix_fmt", "")
            if pix in ALPHA:
                transparent_logo += 1
            elif pix == "pal8":
                warnings.append(f"{where}: palette PNG, cannot tell if it is transparent; export RGBA")
            else:
                warnings.append(f"{where}: no alpha channel ({pix}), so not transparent")
        if kind == "gif" and info.get("codec_name") != "gif":
            warnings.append(f"{where}: kind gif but codec is {info.get('codec_name')}")
        if kind == "trailer":
            if path.suffix.lower() == ".mp4":
                mp4 += 1
            if info.get("codec_name") != "h264":
                warnings.append(f"{where}: codec {info.get('codec_name')}; H.264 plays everywhere")
            if w < 1920 or h < 1080:
                warnings.append(f"{where}: {w}x{h}; give writers 1920x1080 if you have it")
    if not 6 <= count["screenshot"] <= 12:
        errors.append(f"assets.csv: {count['screenshot']} screenshots, need 6 to 12")
    if not keyart_logo or not keyart_clean:
        errors.append("assets.csv: need key art both with logo (with_logo=yes) and without (with_logo=no)")
    if not transparent_logo:
        errors.append("assets.csv: need a logo PNG with a transparent background")
    if not count["gif"]:
        errors.append("assets.csv: need at least one GIF")
    if not mp4:
        errors.append("assets.csv: need the trailer as an MP4 download")


def build_zip(folder, name):
    """Every file in the folder, plus assets.csv files that live outside it (stored by kind)."""
    target = folder / name
    inside = folder.resolve()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        names = set()
        for f in sorted(folder.rglob("*")):
            if f.is_file() and f.suffix.lower() != ".zip":
                arc = str(f.relative_to(folder))
                z.write(f, arc)
                names.add(arc)
        manifest = folder / "assets.csv"
        if manifest.exists():
            with manifest.open(newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    f = (folder / (row.get("path") or "").strip()).resolve()
                    if not f.is_file() or inside in f.parents:
                        continue
                    arc = f"{(row.get('kind') or 'files').strip().lower()}/{f.name}"
                    if arc not in names:
                        z.write(f, arc)
                        names.add(arc)
    return target


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=Path, nargs="?", default=Path("press"), help="press kit folder (default: press)")
    p.add_argument("--no-assets", action="store_true", help="skip the file and ffprobe checks")
    p.add_argument("--zip", metavar="NAME", help="build NAME.zip in the folder from every file in it before checking")
    args = p.parse_args()

    folder = args.folder
    if not folder.is_dir():
        sys.exit(f"{folder}: not a folder")
    if not args.no_assets and not shutil.which("ffprobe"):
        sys.exit("ffprobe not found. Install ffmpeg (it includes ffprobe), or run with --no-assets.")

    errors, warnings = [], []
    index_path, index = read_index(folder)
    if not index_path:
        sys.exit(f"{folder}: no index.md or index.html")
    fact_path = folder / "factsheet.md"
    fact_text = fact_path.read_text(encoding="utf-8") if fact_path.exists() else ""
    if not fact_text:
        errors.append("factsheet.md: not found or empty")

    # Fact sheet fields
    fs = facts(fact_text)
    for key in FACTS:
        if not fs.get(key):
            errors.append(f"factsheet.md: field '{key}' missing or empty (- **{key.title()}:** value)")
    if fs.get("press contact") and "@" not in fs["press contact"]:
        errors.append("factsheet.md: press contact has no email address")
    if not re.search(r"last updated:?\**:?\s*\d{4}-\d{2}-\d{2}", fact_text, re.I):
        errors.append("factsheet.md: add a 'Last updated: YYYY-MM-DD' line")
    website_host = ""
    m = URL.search(fs.get("website", ""))
    if m:
        website_host = urlparse(m.group(0)).netloc.lower().removeprefix("www.")

    # Index sections
    secs = sections(index, 2)
    for key in SECTIONS:
        name, body = find(secs, key)
        if name is None:
            errors.append(f"{index_path.name}: missing section '## {key.capitalize()}'")
        elif not body:
            errors.append(f"{index_path.name}: section '## {name}' is empty")

    _, desc = find(secs, "description")
    if desc:
        sub = sections(desc, 3)
        for key, (lo, hi) in DESCRIPTIONS.items():
            name, body = find(sub, key)
            if not body:
                errors.append(f"{index_path.name}: Description needs '### {key.capitalize()}'")
                continue
            n = words(body)
            if not lo <= n <= hi:
                errors.append(f"{index_path.name}: '{name}' is {n} words, keep it {lo} to {hi}")
            if key == "one sentence":
                one = " ".join(body.split())
                if len(one) > ONE_SENTENCE_MAX_CHARS or re.search(r"[.!?][\"')\]]?\s+\S", one):
                    errors.append(f"{index_path.name}: the one-sentence description must be one sentence, at most {ONE_SENTENCE_MAX_CHARS} characters")

    _, feats = find(secs, "features")
    if feats is not None:
        items = [l for l in feats.splitlines() if re.match(r"^\s*[-*]\s+\S", l)]
        if not 4 <= len(items) <= 6:
            errors.append(f"{index_path.name}: {len(items)} features, need 4 to 6 bullet points")
        for l in items:
            if words(l) > 25:
                errors.append(f"{index_path.name}: feature over 25 words: {l.strip()[:60]}")

    _, awards = find(secs, "awards")
    if awards and not re.match(r"^none yet\.?$", awards.strip(), re.I):
        for l in awards.splitlines():
            if re.match(r"^\s*[-*]\s+\S", l) and not URL.search(l):
                errors.append(f"{index_path.name}: award without a link to check it: {l.strip()[:60]}")

    _, videos = find(secs, "videos")
    if videos is not None and not re.search(r"youtube\.com|youtu\.be|vimeo\.com|<iframe", videos, re.I):
        errors.append(f"{index_path.name}: Videos needs a trailer embed link (YouTube or Vimeo)")

    _, stream = find(secs, "streaming")
    if stream and not re.search(r"monetis|monetiz", stream, re.I):
        errors.append(f"{index_path.name}: the streaming line must say whether videos may be monetised")

    _, embargo = find(secs, "embargo")
    if embargo and not re.match(r"^(no embargo|none)", embargo.strip(), re.I):
        if not re.search(r"\d{1,2}:\d{2}", embargo) or not re.search(r"\b(UTC|GMT|PT|PST|PDT|ET|EST|EDT|CET|CEST|BST|JST)\b", embargo):
            errors.append(f"{index_path.name}: the embargo needs a time and a time zone, or say 'No embargo'")

    # Placeholders and UTM tags
    check_text(index_path, index, errors)
    if fact_text:
        check_text(fact_path, fact_text, errors)
        check_links(fact_path, fact_text, website_host, errors)
    check_links(index_path, index, website_host, errors)

    if args.zip:
        z = build_zip(folder, args.zip if args.zip.endswith(".zip") else args.zip + ".zip")
        print(f"built {z}")
    _, download = find(secs, "download")
    if download is not None:
        refs = {k.lower(): v for k, v in re.findall(r"^\s*\[([^\]]+)\]:\s*(\S+)", index, re.M)}
        zips = [a or b for a, b in re.findall(r"\(([^)\s]+\.zip)\)|href=\"([^\"]+\.zip)\"", download)]
        zips += [refs[k.lower()] for k in re.findall(r"\]\[([^\]]+)\]", download)
                 if refs.get(k.lower(), "").endswith(".zip")]
        if not zips:
            errors.append(f"{index_path.name}: Download must link to the kit as one .zip")
        for zname in zips:
            if not zname.startswith("http") and not (folder / zname).is_file():
                errors.append(f"{index_path.name}: {zname} not found (build it with --zip)")

    if not args.no_assets:
        check_assets(folder, errors, warnings)

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        print(f"\n{len(errors)} problem(s) in {folder}")
        sys.exit(1)
    print(f"ok: {folder} passes ({len(warnings)} warning(s))")


if __name__ == "__main__":
    main()
