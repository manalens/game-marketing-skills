#!/usr/bin/env python3
"""Check a Short script written by the shorts-script skill.

Fails (exit 1) when the hook is longer than 12 words, a post ID is missing or malformed,
the post text has no tagged link or related video, there is no end card line with the game name, the script runs over 60 seconds, or a word
from marketing/rules.md ("Do not say" list) appears.
"""
import argparse
import re
import sys
from pathlib import Path

POST_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-(yt|tt|ig|rd|x|bs|th|yl|nl|dc)-[a-z0-9-]+$")


def section(text, title):
    m = re.search(rf"^## {re.escape(title)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def banned_words(rules_path):
    if not rules_path.exists():
        return []
    words = []
    for line in rules_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*(?:say:|word:)?\s*`([^`]+)`", line)
        if m:
            words.append(m.group(1).lower())
    return words


def check(path, rules_path, max_hook_words, max_seconds):
    text = path.read_text(encoding="utf-8")
    errors = []

    hook = section(text, "Hook")
    words = len(hook.split())
    if not hook:
        errors.append("no '## Hook' section")
    elif words > max_hook_words:
        errors.append(f"hook has {words} words, max {max_hook_words}")

    m = re.search(r"^- Post IDs:\s*(.+)$", text, re.M)
    if not m:
        errors.append("no '- Post IDs:' line")
    else:
        for pid in [p.strip() for p in m.group(1).split(",") if p.strip()]:
            if not POST_ID.match(pid) or len(pid) > 60:
                errors.append(f"bad post ID: {pid} (see docs/LINKS.md)")

    post = section(text, "Post text")
    if not re.search(r"utm_content=|utm_campaign=|<short link>|https?://|^- Related video:", post, re.M):
        errors.append("no link, tagged profile link or related video in '## Post text'")
    if not re.search(r"^- End card", post, re.M):
        errors.append("no '- End card' line (show the game name at the end)")

    m = re.search(r"^- Length:\s*(\d+)\s*s", text, re.M)
    if not m:
        errors.append("no '- Length: N s' line")
    elif int(m.group(1)) > max_seconds:
        errors.append(f"length {m.group(1)} s, max {max_seconds} s")

    lower = text.lower()
    for word in banned_words(rules_path):
        if word in lower:
            errors.append(f"uses a word from {rules_path}: '{word}'")
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", type=Path, help="marketing/shorts/<post-id>.md files")
    p.add_argument("--rules", type=Path, default=Path("marketing/rules.md"),
                   help="do-not-say list; lines like '- `word`' (default: marketing/rules.md)")
    p.add_argument("--max-hook-words", type=int, default=12)
    p.add_argument("--max-seconds", type=int, default=60)
    args = p.parse_args()

    failed = False
    for f in args.files:
        if not f.exists():
            print(f"{f}: not found", file=sys.stderr)
            failed = True
            continue
        errors = check(f, args.rules, args.max_hook_words, args.max_seconds)
        if errors:
            failed = True
            for e in errors:
                print(f"{f}: {e}")
        else:
            print(f"{f}: ok")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
