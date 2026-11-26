#!/usr/bin/env python3
"""Check a week of social posts written by the social-post skill.

Reads blocks like:
  ### x            (or bluesky, threads)
  - Post ID: 2026-11-28-x-wind-steering
  - Media: clips/wind-steering.gif
  - Alt: ...
  - Text: ...
  - Reply: ...    (optional)

Fails (exit 1) when text or the reply is over the platform limit (x 280, bluesky 300,
threads 500), media has
no alt text, the post ID is missing or malformed, a post
has more than --max-hashtags hashtags, or a word from marketing/rules.md appears.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

LIMITS = {"x": 280, "bluesky": 300, "threads": 500}
CODES = {"x": "x", "bluesky": "bs", "threads": "th"}
URL = re.compile(r"https?://\S+|<tagged link>|<short link>")


def length(text, platform):
    if platform == "x":
        # X counts each link as 23 characters.
        return len(URL.sub("x" * 23, text))
    # Bluesky counts graphemes; NFC length is a close, safe estimate.
    return len(unicodedata.normalize("NFC", text))


def field(block, name):
    m = re.search(rf"^- {name}:\s*(.*)$", block, re.M)
    return m.group(1).strip() if m else None


def banned(path):
    if not path.exists():
        return []
    return [m.group(1).lower() for line in path.read_text(encoding="utf-8").splitlines()
            if (m := re.match(r"^\s*-\s*`([^`]+)`", line))]


def word_pattern(word):
    """Match a do-not-say entry as a whole word or phrase, not inside a longer word.

    `ai` must not match "sail", and `gus` must not match "gust". An entry that starts or ends
    with a symbol (such as `$`) has no word edge on that side.
    """
    start = r"(?<!\w)" if re.match(r"\w", word) else ""
    end = r"(?!\w)" if re.search(r"\w$", word) else ""
    return re.compile(start + re.escape(word) + end)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", type=Path)
    p.add_argument("--rules", type=Path, default=Path("marketing/rules.md"))
    p.add_argument("--max-hashtags", type=int, default=2)
    args = p.parse_args()
    if not args.file.exists():
        sys.exit(f"{args.file}: not found")

    text = args.file.read_text(encoding="utf-8")
    blocks = re.split(r"^### ", text, flags=re.M)[1:]
    errors = []
    if not blocks:
        errors.append("no posts (expected '### x', '### bluesky' or '### threads' blocks)")
    words = banned(args.rules)

    for b in blocks:
        platform = b.splitlines()[0].strip().lower()
        where = f"{platform} post"
        if platform not in LIMITS:
            errors.append(f"unknown platform heading '### {platform}' (use x, bluesky or threads)")
            continue
        pid = field(b, "Post ID")
        if not pid or not re.match(rf"^\d{{4}}-\d{{2}}-\d{{2}}-{CODES[platform]}-[a-z0-9-]+$", pid):
            errors.append(f"{where}: post ID '{pid}' should be YYYY-MM-DD-{CODES[platform]}-slug")
        else:
            where = pid
        body = field(b, "Text") or ""
        if not body:
            errors.append(f"{where}: no '- Text:' line")
        n = length(body, platform)
        if n > LIMITS[platform]:
            errors.append(f"{where}: {n} characters, limit {LIMITS[platform]}")
        reply = field(b, "Reply") or ""
        if reply and length(reply, platform) > LIMITS[platform]:
            errors.append(f"{where}: reply has {length(reply, platform)} characters, limit {LIMITS[platform]}")
        if field(b, "Media") and not field(b, "Alt"):
            errors.append(f"{where}: media has no '- Alt:' text")
        if platform == "x" and URL.search(body):
            print(f"{args.file}: note: {where} has its link in the main X post; fine if this is the "
                  "link-placement test, otherwise move it to '- Reply:'")
        tags = re.findall(r"(?<!\w)#\w+", body)
        if len(tags) > args.max_hashtags:
            errors.append(f"{where}: {len(tags)} hashtags, max {args.max_hashtags}")
        lower = b.lower()
        for w in words:
            if word_pattern(w).search(lower):
                errors.append(f"{where}: uses '{w}' from {args.rules}")

    for e in errors:
        print(f"{args.file}: {e}")
    if errors:
        sys.exit(1)
    print(f"{args.file}: ok ({len(blocks)} posts)")


if __name__ == "__main__":
    main()
