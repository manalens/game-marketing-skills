#!/usr/bin/env python3
"""Check a devlog brief file written by the devlog-from-git skill.

Fails (exit 1) when a "- Commit:" line names a commit the repo does not have, a brief has no
"- In public build:" line, Update numbers repeat or skip, or a word from marketing/rules.md
appears.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def commit_exists(repo, sha):
    r = subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True)
    return r.returncode == 0


def banned_words(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*`([^`]+)`", line)
        if m:
            out.append(m.group(1).lower())
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", type=Path, help="marketing/devlog/<date>.md")
    p.add_argument("--repo", default=".", help="game repo (default: .)")
    p.add_argument("--rules", type=Path, default=Path("marketing/rules.md"))
    args = p.parse_args()

    if not args.file.exists():
        sys.exit(f"{args.file}: not found")
    text = args.file.read_text(encoding="utf-8")
    briefs = re.split(r"^## ", text, flags=re.M)[1:]
    errors = []
    if not briefs:
        errors.append("no briefs (expected '## N. ...' headings)")

    update_numbers = []
    for b in briefs:
        title = b.splitlines()[0].strip()
        m = re.search(r"^- Commit:\s*([0-9a-f]{7,40})", b, re.M)
        if not m:
            errors.append(f"'{title}': no '- Commit: <sha>' line")
        elif not commit_exists(args.repo, m.group(1)):
            errors.append(f"'{title}': commit {m.group(1)} not in {args.repo}")
        if not re.search(r"^- In public build:\s*\S", b, re.M):
            errors.append(f"'{title}': no '- In public build:' line")
        u = re.search(r"Update #(\d+)", title)
        if u:
            update_numbers.append(int(u.group(1)))

    if update_numbers:
        expected = list(range(update_numbers[0], update_numbers[0] + len(update_numbers)))
        if update_numbers != expected:
            errors.append(f"Update numbers {update_numbers} repeat or skip; expected {expected}")

    lower = text.lower()
    for w in banned_words(args.rules):
        if w in lower:
            errors.append(f"uses a word from {args.rules}: '{w}'")

    for e in errors:
        print(f"{args.file}: {e}")
    if errors:
        sys.exit(1)
    print(f"{args.file}: ok ({len(briefs)} briefs)")


if __name__ == "__main__":
    main()
