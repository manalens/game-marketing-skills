#!/usr/bin/env python3
"""List git commits that could become devlog Shorts.

Sorts commits into two kinds of candidates:
  update    a change a player can see (new feature, art, sound, UI, content)
  conflict  a bug, a design problem or a revert, with a before and an after

Skips tooling, tests, CI, docs, refactors and dependency bumps. This is a first filter by
message and file path; the agent still reads each diff before it writes a story.

Prints a Markdown table, or JSON with --json.
"""
import argparse
import json
import re
import subprocess
import sys

CONFLICT_WORDS = re.compile(
    r"\b(fix(e[sd])?|bug|broke(n)?|crash(es|ed)?|stuck|glitch|exploit|softlock|clip(ping|s)? through|"
    r"revert|undo|rollback|wrong|weird|infinite|falls? through|too (hard|easy|fast|slow)|"
    r"balance|nerf|buff|rework|redesign|cut|remove[sd]?|delete[sd]?)\b",
    re.I,
)
UPDATE_WORDS = re.compile(
    r"\b(add(s|ed)?|new|now|show(s)?|animat\w*|sound|music|sfx|vfx|particle\w*|shader|light(ing)?|"
    r"weather|model|sprite|art|texture|ui|menu|hud|emote|level|map|island|boss|enemy|npc|"
    r"quest|item|recipe|skin|outfit|polish|juice|feel)\b",
    re.I,
)
SKIP_WORDS = re.compile(
    r"\b(test(s|ing)?|ci|lint|typo|docs?|readme|refactor|chore|deps?|bump|upgrade|format(ting)?|"
    r"cleanup|clean up|build script|tooling|wip|merge (branch|pull request)|helpers?|tsc|vitest|types?|"
    r"module|newsletter|blog|seo|analytics|sdk)\b|^(tools|dev tools|helpers|[\w./-]+\.(ts|js|py|cs|gd|cpp|h)):",
    re.I,
)
SKIP_PATHS = re.compile(
    r"(^|/)(tests?|spec|__tests__|\.github|docs?|scripts|tools?|ci)/|"
    r"(\.md|\.lock|package-lock\.json|pnpm-lock\.yaml|\.ya?ml|\.toml|\.cfg|\.ini)$",
    re.I,
)
VISIBLE_PATHS = re.compile(
    r"\.(png|jpe?g|webp|gif|svg|ogg|wav|mp3|glb|gltf|fbx|obj|tscn|tres|scn|prefab|unity|uasset|umap|"
    r"shader|gdshader|glsl|hlsl|ttf|otf|json)$|(^|/)(art|audio|sound|music|levels?|scenes?|maps?|ui|"
    r"assets|content|data)/",
    re.I,
)


def git(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def commits(repo, since, until, branch, limit, paths):
    fmt = "%x1e%H%x1f%h%x1f%ad%x1f%s%x1f%b%x1d"
    args = ["log", branch, f"--format={fmt}", "--date=short", "--name-only", "--no-merges"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if limit:
        args.append(f"-n{limit}")
    if paths:
        args += ["--", *paths]
    raw = git(repo, *args)
    for chunk in raw.split("\x1e")[1:]:
        meta, _, files = chunk.partition("\x1d")
        sha, short, date, subject, body = (meta.split("\x1f") + [""] * 5)[:5]
        file_list = [l.strip() for l in files.splitlines() if l.strip()]
        yield {"sha": sha, "short": short, "date": date, "subject": subject.strip(),
               "body": body.strip(), "files": file_list}


def classify(c):
    text = f"{c['subject']}\n{c['body']}"
    files = c["files"]
    code_or_assets = [f for f in files if not SKIP_PATHS.search(f)]
    if files and not code_or_assets:
        return None, "only tooling, docs or config files"
    if SKIP_WORDS.search(c["subject"]) and not CONFLICT_WORDS.search(c["subject"]):
        return None, "tooling or chore message"
    visible = any(VISIBLE_PATHS.search(f) for f in files)
    if CONFLICT_WORDS.search(text):
        return "conflict", "fix, revert or design change"
    if UPDATE_WORDS.search(text) or visible:
        return "update", "visible change" if visible else "feature words in message"
    return None, "no player-facing signal"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default=".", help="path to the game repo (default: .)")
    p.add_argument("--since", default="14 days ago", help='git date, e.g. "2026-11-01" or "7 days ago"')
    p.add_argument("--until", default=None)
    p.add_argument("--branch", default="HEAD")
    p.add_argument("--limit", type=int, default=500, help="max commits to read (default 500)")
    p.add_argument("--path", action="append", default=[],
                   help="only commits touching this path (repeat; e.g. --path game/)")
    p.add_argument("--kind", choices=["all", "update", "conflict"], default="all")
    p.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    p.add_argument("--show-skipped", action="store_true", help="also list skipped commits and why")
    args = p.parse_args()

    git(args.repo, "rev-parse", "--git-dir")
    rows, skipped = [], []
    for c in commits(args.repo, args.since, args.until, args.branch, args.limit, args.path):
        kind, why = classify(c)
        if kind is None:
            skipped.append({**c, "why": why})
            continue
        if args.kind != "all" and kind != args.kind:
            continue
        rows.append({**c, "kind": kind, "why": why, "before": f"{c['short']}^"})

    if args.json:
        print(json.dumps({"candidates": rows, "skipped": skipped if args.show_skipped else len(skipped)}, indent=2))
        return
    print(f"# Devlog candidates ({len(rows)} of {len(rows) + len(skipped)} commits)\n")
    print("| Kind | Date | Commit | Before | Subject | Files | Why |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        files = ", ".join(r["files"][:3]) + (f" +{len(r['files']) - 3}" if len(r["files"]) > 3 else "")
        subj = r["subject"].replace("|", "/")
        subj = subj if len(subj) <= 100 else subj[:97] + "..."
        print(f"| {r['kind']} | {r['date']} | {r['short']} | {r['before']} | {subj} | {files} | {r['why']} |")
    if args.show_skipped:
        print("\n## Skipped\n")
        for s in skipped:
            print(f"- {s['short']} {s['subject']} ({s['why']})")
    if not rows:
        print("\nNo candidates. Try an earlier --since, or --show-skipped to see why.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.stderr.close()
