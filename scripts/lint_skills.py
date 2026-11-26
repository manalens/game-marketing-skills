#!/usr/bin/env python3
"""Lint every skill in skills/<category>/<name>/SKILL.md against CONTRIBUTING.md.

Checks: frontmatter has only name and description; name matches the folder and the pattern;
description length and "Not for" clause; required sections; body length; relative links resolve;
scripts have --help that exits 0; no em dashes; each skill is in the marketplace and has
3 "should" and 1 "near-miss" prompt in evals/triggers.json.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED = ["## Workflow", "## Measure", "## Gotchas", "## Version notes"]
CATEGORIES = {"marketing", "measure", "launch"}


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm, body = m.group(1), text[m.end():]
    fields, key = {}, None
    for line in fm.splitlines():
        km = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if km:
            key = km.group(1)
            fields[key] = km.group(2).strip().lstrip(">|").strip()
        elif key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, body


def lint_skill(skill_dir, triggers, market, run_scripts):
    errs = []
    rel = skill_dir.relative_to(ROOT)
    md = skill_dir / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    fields, body = frontmatter(text)
    if fields is None:
        return [f"{rel}: no frontmatter"]
    extra = set(fields) - {"name", "description"}
    if extra:
        errs.append(f"{rel}: extra frontmatter fields {sorted(extra)}")
    name = fields.get("name", "")
    if name != skill_dir.name or not NAME.match(name) or len(name) > 64:
        errs.append(f"{rel}: name '{name}' must match folder and [a-z0-9-], max 64")
    desc = fields.get("description", "")
    if not desc or len(desc) > 1024:
        errs.append(f"{rel}: description empty or over 1024 characters ({len(desc)})")
    if "Not for" not in desc:
        errs.append(f"{rel}: description has no 'Not for ...' clause")
    if skill_dir.parent.name not in CATEGORIES:
        errs.append(f"{rel}: category must be one of {sorted(CATEGORIES)}")
    for sec in REQUIRED:
        if not re.search(rf"^{re.escape(sec)}\b", body, re.M):
            errs.append(f"{rel}: missing section '{sec}'")
    if "Last verified 20" not in body:
        errs.append(f"{rel}: Version notes need 'Last verified YYYY-MM-DD'")
    if len(text.splitlines()) > 400:
        errs.append(f"{rel}: SKILL.md over 400 lines")

    for f in skill_dir.rglob("*"):
        if f.is_file() and f.suffix in {".md", ".py", ".json", ".sh"}:
            content = f.read_text(encoding="utf-8")
            if "—" in content:
                errs.append(f"{f.relative_to(ROOT)}: contains an em dash")
            if f.suffix == ".md":
                prose = re.sub(r"^```.*?^```", "", content, flags=re.M | re.S)
                for link in re.findall(r"\]\(([^)#\s]+)", prose):
                    if link.startswith(("http://", "https://", "mailto:")):
                        continue
                    if not (f.parent / link).resolve().exists():
                        errs.append(f"{f.relative_to(ROOT)}: broken link {link}")

    if run_scripts:
        for script in sorted((skill_dir / "scripts").glob("*.py")):
            r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
            if r.returncode != 0:
                errs.append(f"{script.relative_to(ROOT)}: --help exited {r.returncode}")

    kinds = [t["kind"] for t in triggers if t.get("id", "").startswith(name + ".")]
    if kinds.count("should") < 3 or kinds.count("near-miss") < 1:
        errs.append(f"{rel}: evals/triggers.json needs 3 'should' and 1 'near-miss' (has {kinds})")
    if f"./{rel.as_posix()}" not in market:
        errs.append(f"{rel}: not listed in .claude-plugin/marketplace.json")
    return errs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-scripts", action="store_true", help="skip running each script's --help")
    args = p.parse_args()

    triggers = json.loads((ROOT / "evals/triggers.json").read_text(encoding="utf-8"))
    market = {s for pl in json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"]
              for s in pl.get("skills", [])}
    skills = sorted(p.parent for p in (ROOT / "skills").glob("*/*/SKILL.md"))
    if not skills:
        sys.exit("no skills found under skills/<category>/<name>/SKILL.md")

    errors = []
    for s in skills:
        errors += lint_skill(s, triggers, market, not args.no_scripts)
    for m in market:
        if not (ROOT / m / "SKILL.md").exists():
            errors.append(f"marketplace lists {m}, which has no SKILL.md")
    for t in triggers:
        if t.get("kind") not in {"should", "near-miss"}:
            errors.append(f"evals: {t.get('id')} kind must be 'should' or 'near-miss'")

    for e in errors:
        print(e)
    if errors:
        print(f"\n{len(errors)} problem(s) in {len(skills)} skills")
        sys.exit(1)
    print(f"ok: {len(skills)} skills")


if __name__ == "__main__":
    main()
