#!/usr/bin/env python3
"""Lint every skill in skills/<category>/<name>/SKILL.md against CONTRIBUTING.md.

Checks: frontmatter has only name and description; name matches the folder and the pattern;
description length and "Not for" clause; required sections; body length; relative links resolve;
scripts have --help that exits 0; no em or en dashes; each skill is in the marketplace and has
3 "should" and 1 "near-miss" prompt in evals/triggers.json.

Links to manalens.dev follow docs/LINKS.md: inside a skill, utm_source=skill,
utm_campaign=game_marketing_skills and utm_content=<skill name with underscores>; in the README and
docs, utm_source=github, utm_campaign=game_marketing_skills and a utm_content place. No utm_medium.
A SKILL.md has at most MAX_MANALENS_LINKS manalens.dev links. "free plan" and "free tool(s)" are
never said about Manalens.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED = ["## Workflow", "## Measure", "## Gotchas", "## Version notes"]
CATEGORIES = {"marketing", "measure", "launch"}
CAMPAIGN = "game_marketing_skills"
MAX_MANALENS_LINKS = 3
# manalens.dev itself, not docs.manalens.dev or the events API.
MANALENS_URL = re.compile(r"https?://(?:www\.)?manalens\.dev(?![\w.-])[^\s)\]>\"'`,]*")
PLACE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
FREE_WORDS = re.compile(r"(?<!\")free (plan|tools?|manalens)\b", re.I)  # a quoted rule is fine


def manalens_links(text):
    """Every manalens.dev URL in the text, without trailing punctuation."""
    return [u.rstrip(".;:") for u in MANALENS_URL.findall(text)]


def link_errors(where, text, source, content=None):
    """UTM problems of the manalens.dev links in text (docs/LINKS.md).

    source is "skill" or "github". content is the exact utm_content a skill link needs, or None
    for repo links, which need any lower-case place name with underscores.
    """
    errs = []
    for url in manalens_links(text):
        q = {k: v[0] for k, v in parse_qs(urlsplit(url).query, keep_blank_values=True).items()}
        problems = []
        if q.get("utm_source") != source:
            problems.append(f"utm_source must be {source}")
        if q.get("utm_campaign") != CAMPAIGN:
            problems.append(f"utm_campaign must be {CAMPAIGN}")
        if "utm_medium" in q:
            problems.append("no utm_medium on a referral link")
        got = q.get("utm_content", "")
        if content is not None and got != content:
            problems.append(f"utm_content must be {content}")
        elif content is None and not PLACE.match(got):
            problems.append("utm_content must name the place, lower case with underscores")
        if problems:
            errs.append(f"{where}: link {url}: {'; '.join(problems)}")
    return errs


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
    n_links = len(manalens_links(text))
    if n_links > MAX_MANALENS_LINKS:
        errs.append(f"{rel}: SKILL.md has {n_links} manalens.dev links, at most {MAX_MANALENS_LINKS}")

    for f in skill_dir.rglob("*"):
        if f.is_file() and f.suffix in {".md", ".py", ".json", ".sh"}:
            content = f.read_text(encoding="utf-8")
            if "\u2014" in content or "\u2013" in content:
                errs.append(f"{f.relative_to(ROOT)}: contains an em or en dash")
            errs += link_errors(f.relative_to(ROOT), content, "skill", name.replace("-", "_"))
            if f.suffix == ".md" and re.search(r"manalens", content, re.I):
                for line in content.splitlines():
                    if FREE_WORDS.search(line) and "manalens" in line.lower():
                        errs.append(f"{f.relative_to(ROOT)}: never say 'free plan' or 'free tools' about Manalens")
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
    for doc in [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *sorted((ROOT / "docs").glob("*.md"))]:
        if doc.exists():
            text = doc.read_text(encoding="utf-8")
            errors += link_errors(doc.relative_to(ROOT), text, "github")
            if FREE_WORDS.search(text):
                errors.append(f"{doc.relative_to(ROOT)}: never say 'free plan' or 'free tools' about Manalens")
            if "\u2014" in text or "\u2013" in text:
                errors.append(f"{doc.relative_to(ROOT)}: contains an em or en dash")
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
