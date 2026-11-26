#!/usr/bin/env python3
"""Check local Steam store assets before you upload them.

Screenshots (--screenshots DIR): at least 5 image files, each 1920x1080 or larger, 16:9, PNG or
JPG. Sizes are read with ffprobe (part of ffmpeg), which must be installed.

Short description (--short FILE): plain text, 300 characters or fewer (Manalens guide; Valve says
"a few hundred"), no time-based text ("Now available", dates, quarters, Early Access promises),
no links. Warns when no genre word or player verb is found.

About This Game (--about FILE): no links; warns under 150 words (Manalens rule of thumb).
Description media (--about-media DIR): each GIF or image under 5 MB, all under 15 MB (Valve).

Exit code 0 when nothing fails, 1 when a check fails, 2 on a usage or setup error.
Warnings do not fail the run unless you pass --strict.

Examples:
  check_store_assets.py --screenshots marketing/steam/screenshots --short launch/short-description.txt
  check_store_assets.py --short launch/short-description.txt --strict
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCREENSHOT_MIN_W, SCREENSHOT_MIN_H, SCREENSHOT_MIN_COUNT = 1920, 1080, 5
SHORT_GUIDE = 300
ABOUT_WORDS_MIN = 150
MEDIA_MAX_EACH, MEDIA_MAX_TOTAL = 5 * 1024 * 1024, 15 * 1024 * 1024
SAFE_TYPES = {".png", ".jpg", ".jpeg"}
IMAGE_TYPES = SAFE_TYPES | {".gif", ".webp", ".bmp", ".tif", ".tiff", ".avif", ".heic"}
MEDIA_TYPES = IMAGE_TYPES | {".webm", ".mp4"}

# Word lists follow the Manalens short description checker (steam-assets.ts, Nov 2026).
GENRE_WORDS = ["action", "adventure", "roguelike", "roguelite", "rpg", "role-playing", "strategy",
               "simulation", "sim", "puzzle", "platformer", "metroidvania", "shooter", "survival",
               "horror", "racing", "sports", "fighting", "rhythm", "card", "deckbuilder",
               "deckbuilding", "tower defense", "city builder", "colony", "sandbox", "visual novel",
               "farming", "cozy", "idle", "incremental", "stealth", "tactics", "tactical",
               "turn-based", "real-time", "co-op", "multiplayer", "open world", "narrative",
               "management", "crafting", "bullet hell", "soulslike", "arcade", "mystery",
               "detective", "party"]
VERBS = ["explore", "build", "fight", "craft", "survive", "battle", "collect", "solve", "race",
         "defend", "design", "manage", "grow", "farm", "fish", "cook", "escape", "hunt", "discover",
         "command", "trade", "recruit", "upgrade", "customize", "sail", "fly", "climb", "sneak",
         "shoot", "slay", "befriend", "uncover", "investigate", "conquer", "create", "play", "lead",
         "choose", "master", "unlock", "raise", "restore"]
TIME_PHRASES = ["now available", "available now", "out now", "coming soon", "pre-order", "preorder",
                "prepurchase", "pre-purchase", "wishlist now", "available on", "launching",
                "release date", "releases on", "launch day", "buy now", "on sale", "% off",
                "free weekend", "demo out", "play the demo", "early bird"]
MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december|"
          "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
DATE_RES = [
    (re.compile(rf"\b({MONTHS})\.?\s+\d{{1,2}}(st|nd|rd|th)?\b", re.I), "a month and day"),
    (re.compile(rf"\b\d{{1,2}}(st|nd|rd|th)?\s+({MONTHS})\b", re.I), "a day and month"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "a numeric date"),
    (re.compile(r"\bQ[1-4]\s*'?\d{2,4}\b", re.I), "a quarter"),
    (re.compile(r"\b(this|next)\s+(spring|summer|fall|autumn|winter|year|month|week)\b", re.I), "a season or period"),
]
EARLY_ACCESS_PROMISE = re.compile(
    r"(coming|launching|entering|join|joins|available|out|enter|leaves?|leaving)\s+(in\s+|to\s+|into\s+|on\s+)?early access"
    r"|early access\s+(soon|now|in\s|on\s|from\s|starting|launch)"
    r"|full release\s+(in|on|by|this|next|soon)", re.I)
YEAR = re.compile(r"\b20[2-3]\d\b")
LINK = re.compile(r"https?://|www\.|\b[a-z0-9-]+\.(com|net|org|io|gg|co|dev|app|me|tv)\b", re.I)
NON_GAMEPLAY_NAME = re.compile(r"(logo|title|menu|concept|key[-_ ]?art|award|capsule|banner|poster|cover|text)", re.I)


class Report:
    def __init__(self):
        self.rows = []

    def add(self, area, status, text):
        self.rows.append({"area": area, "status": status, "text": text})

    def count(self, status):
        return sum(1 for r in self.rows if r["status"] == status)


def has_word(lower, word):
    pattern = r"(^|[^a-z])" + re.escape(word) + r"(e?s|d|ed|ing)?([^a-z]|$)"
    return re.search(pattern, lower) is not None


def probe_size(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
           "-of", "csv=p=0:s=x", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
    m = re.match(r"^(\d+)x(\d+)", line)
    return (int(m.group(1)), int(m.group(2))) if m else None


def check_screenshots(folder, rep, min_count):
    area = "screenshots"
    if not folder.is_dir():
        rep.add(area, "fail", f"{folder} is not a folder.")
        return
    if not shutil.which("ffprobe"):
        print("error: ffprobe not found. Install ffmpeg (for example `apt install ffmpeg` or "
              "`brew install ffmpeg`) and run again.", file=sys.stderr)
        sys.exit(2)
    files = sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))
    images = [p for p in files if p.suffix.lower() in IMAGE_TYPES]
    skipped = [p.name for p in files if p.suffix.lower() not in IMAGE_TYPES]
    if skipped:
        rep.add(area, "info", f"Skipped {len(skipped)} non-image file(s): {', '.join(skipped[:5])}.")
    good = 0
    for p in images:
        ext = p.suffix.lower()
        size = probe_size(p)
        problems = []
        if ext not in SAFE_TYPES:
            problems.append(f"file type {ext} (Valve names no type; PNG or JPG is the safe choice)")
        if size is None:
            rep.add(area, "fail", f"{p.name}: ffprobe could not read the image size.")
            continue
        w, h = size
        if w < SCREENSHOT_MIN_W or h < SCREENSHOT_MIN_H:
            problems.append(f"{w}x{h} is under {SCREENSHOT_MIN_W}x{SCREENSHOT_MIN_H}")
        ratio = w / h if h else 0
        if abs(ratio - 16 / 9) >= 0.01:
            problems.append(f"aspect {ratio:.3f}:1 is not 16:9 (1.778:1)")
        if problems:
            rep.add(area, "fail", f"{p.name}: " + "; ".join(problems) + ".")
        else:
            good += 1
            rep.add(area, "pass", f"{p.name}: {w}x{h}, 16:9, {ext[1:].upper()}.")
        if NON_GAMEPLAY_NAME.search(p.stem):
            rep.add(area, "warn", f"{p.name}: the name suggests a non-gameplay image. Categorize it "
                                  "correctly in Steamworks and keep it out of the first 4.")
    status = "pass" if good >= min_count else "fail"
    rep.add(area, status, f"{good} usable screenshot(s) of {len(images)} image(s). Valve asks for at "
                          f"least {min_count}, and at least 5 categorized as gameplay (since 3 Nov 2026).")
    rep.add(area, "info", "Not checked by this script: baked-in marketing text, gameplay vs menu "
                          "content, the 'suitable for all ages' mark. Look at each image yourself.")


def check_short(path, rep):
    area = "short description"
    if not path.is_file():
        rep.add(area, "fail", f"{path} not found.")
        return
    text = path.read_text(encoding="utf-8").strip()
    lower = text.lower()
    n = len(text)
    if n == 0:
        rep.add(area, "fail", "The file is empty.")
        return
    rep.add(area, "pass" if n <= SHORT_GUIDE else "fail",
            f"{n} characters. Guide: {SHORT_GUIDE} or fewer (the Steamworks editor counter has the final say).")
    found = [p for p in TIME_PHRASES if p in lower]
    for regex, label in DATE_RES:
        m = regex.search(text)
        if m:
            found.append(f"{label} ('{m.group(0)}')")
    m = EARLY_ACCESS_PROMISE.search(text)
    if m:
        found.append(f"an Early Access or release promise ('{m.group(0)}')")
    rep.add(area, "fail" if found else "pass",
            "Time-based text: " + "; ".join(found) + ". Valve allows none here." if found
            else "No time-based text found.")
    if not m and "early access" in lower:
        rep.add(area, "warn", "Mentions Early Access. Steam shows the Early Access state itself; "
                              "use the space to say what the player does.")
    y = YEAR.search(text)
    if y:
        rep.add(area, "warn", f"Contains the year {y.group(0)}. Remove it if it is a release date.")
    link = LINK.search(text)
    rep.add(area, "fail" if link else "pass",
            f"Link or web address found ('{link.group(0)}'). Valve allows no links." if link else "No links.")
    genres = [g for g in GENRE_WORDS if has_word(lower, g)]
    verbs = [v for v in VERBS if has_word(lower, v)]
    rep.add(area, "pass" if genres else "warn",
            f"Genre words: {', '.join(genres)}." if genres else "No genre word found. Say what kind of game it is.")
    rep.add(area, "pass" if verbs else "warn",
            f"Player verbs: {', '.join(verbs)}." if verbs else "No common player verb found. Say what the player does.")
    if "\n" in text or re.search(r"^\s*[-*•]", text, re.M):
        rep.add(area, "warn", "Line breaks or bullets found. The field is plain text and does not render them.")
    if re.search(r"<[a-z/][^>]*>|\[/?[a-z]+\]", text, re.I):
        rep.add(area, "fail", "HTML or BBCode markup found. The short description is plain text.")
    if "!" in text:
        rep.add(area, "warn", "Exclamation mark found. Shoppers skim hype; state the genre and the actions.")


def check_about(path, rep):
    area = "about"
    if not path.is_file():
        rep.add(area, "fail", f"{path} not found.")
        return
    text = path.read_text(encoding="utf-8")
    words = len(re.findall(r"[A-Za-z0-9']+", re.sub(r"<[^>]+>|\[[^\]]+\]", " ", text)))
    rep.add(area, "pass" if words >= ABOUT_WORDS_MIN else "warn",
            f"{words} words. Manalens rule of thumb: {ABOUT_WORDS_MIN} or more (Valve: 'detailed and coherent').")
    link = LINK.search(re.sub(r"\[img\][^\[]*\[/img\]|<img[^>]*>", " ", text, flags=re.I))
    rep.add(area, "fail" if link else "pass",
            f"Link to another site found ('{link.group(0)}'). Valve allows no links in descriptions."
            if link else "No links to other sites.")
    for phrase in ["wishlist now", "buy now", "click here", "add to wishlist"]:
        if phrase in text.lower():
            rep.add(area, "warn", f"'{phrase}': make sure no image or text copies a Steam button.")


def check_media(folder, rep):
    area = "about media"
    if not folder.is_dir():
        rep.add(area, "fail", f"{folder} is not a folder.")
        return
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_TYPES)
    total = 0
    for p in files:
        size = p.stat().st_size
        total += size
        mb = size / 1024 / 1024
        rep.add(area, "pass" if size < MEDIA_MAX_EACH else "fail", f"{p.name}: {mb:.2f} MB (limit under 5 MB each).")
    rep.add(area, "pass" if total < MEDIA_MAX_TOTAL else "fail",
            f"{len(files)} file(s), {total / 1024 / 1024:.2f} MB in total (limit under 15 MB).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--screenshots", type=Path, help="folder of screenshot files")
    ap.add_argument("--short", type=Path, help="text file with the short description")
    ap.add_argument("--about", type=Path, help="text, BBCode or HTML file with About This Game")
    ap.add_argument("--about-media", type=Path, help="folder of GIFs and images for About This Game")
    ap.add_argument("--min-count", type=int, default=SCREENSHOT_MIN_COUNT, help="minimum screenshots (default 5)")
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args()
    if not any([args.screenshots, args.short, args.about, args.about_media]):
        ap.error("give at least one of --screenshots, --short, --about, --about-media")

    rep = Report()
    if args.screenshots:
        check_screenshots(args.screenshots, rep, args.min_count)
    if args.short:
        check_short(args.short, rep)
    if args.about:
        check_about(args.about, rep)
    if args.about_media:
        check_media(args.about_media, rep)

    fails, warns = rep.count("fail"), rep.count("warn")
    if args.json:
        print(json.dumps({"fails": fails, "warnings": warns, "checks": rep.rows}, indent=2))
    else:
        for r in rep.rows:
            print(f"[{r['status'].upper():4}] {r['area']}: {r['text']}")
        print(f"\n{fails} failed, {warns} warning(s).")
    sys.exit(1 if fails or (args.strict and warns) else 0)


if __name__ == "__main__":
    main()
