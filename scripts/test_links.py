#!/usr/bin/env python3
"""Tests for the link rules of docs/LINKS.md: the linter's manalens.dev check, the press kit check
and the outreach tracker check. Run: python3 scripts/test_links.py
"""
import csv
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lint = load("lint_skills", "scripts/lint_skills.py")
press_kit = load("check_press_kit", "skills/launch/press-kit/scripts/check_press_kit.py")
OUTREACH = ROOT / "skills/launch/press-outreach/scripts/check_outreach.py"


class ManalensLinks(unittest.TestCase):
    def test_skill_link_ok(self):
        text = "[grader](https://manalens.dev/tools/steam-page-grader?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=steam_page_review)."
        self.assertEqual(lint.link_errors("x", text, "skill", "steam_page_review"), [])

    def test_old_skill_tags_fail(self):
        text = "https://manalens.dev/tools/x?utm_source=game-marketing-skills&utm_medium=skill&utm_campaign=steam-page-review"
        errs = lint.link_errors("x", text, "skill", "steam_page_review")
        self.assertEqual(len(errs), 1)
        for part in ("utm_source must be skill", "utm_campaign must be game_marketing_skills",
                     "no utm_medium", "utm_content must be steam_page_review"):
            self.assertIn(part, errs[0])

    def test_untagged_and_wrong_skill_fail(self):
        self.assertTrue(lint.link_errors("x", "see https://manalens.dev/blog/a.", "skill", "a_b"))
        text = "https://manalens.dev/?utm_source=skill&utm_campaign=game_marketing_skills&utm_content=other"
        self.assertTrue(lint.link_errors("x", text, "skill", "a_b"))

    def test_github_links(self):
        ok = '<a href="https://manalens.dev/?utm_source=github&utm_campaign=game_marketing_skills&utm_content=sponsor_banner">'
        self.assertEqual(lint.link_errors("README", ok, "github"), [])
        old = '<a href="https://manalens.dev/?utm_source=github&utm_medium=readme&utm_campaign=game-marketing-skills&utm_content=sponsor_banner">'
        self.assertTrue(lint.link_errors("README", old, "github"))
        dashes = "https://manalens.dev/?utm_source=github&utm_campaign=game_marketing_skills&utm_content=sponsor-text"
        self.assertTrue(lint.link_errors("README", dashes, "github"))

    def test_other_hosts_ignored(self):
        text = "https://docs.manalens.dev/mcp/overview and https://events.manalens.dev/v0/events"
        self.assertEqual(lint.link_errors("x", text, "skill", "a"), [])

    def test_free_words(self):
        self.assertTrue(lint.FREE_WORDS.search("Many skills hand off to a free tool"))
        self.assertTrue(lint.FREE_WORDS.search("the free Manalens analyzer"))
        self.assertIsNone(lint.FREE_WORDS.search("connect Manalens (14-day trial)"))


class PressKitLinks(unittest.TestCase):
    def problems(self, query):
        return press_kit.link_problems(parse_qs(query))

    def test_press_source_no_medium(self):
        self.assertEqual(self.problems("utm_source=press&utm_campaign=launch&utm_content=factsheet"), [])

    def test_old_presskit_tags_fail(self):
        got = self.problems("utm_source=presskit&utm_medium=press&utm_campaign=launch")
        self.assertEqual(len(got), 2)
        self.assertIn("use press", got[0])
        self.assertIn("utm_medium", got[1])

    def test_missing_campaign(self):
        self.assertIn("link without utm_campaign", self.problems("utm_source=press"))


class OutreachLinks(unittest.TestCase):
    HEADER = ["name", "outlet", "contact", "audience", "similar_games", "status", "sent_date",
              "follow_up_date", "key_sent", "coverage_url", "utm_content", "type", "contact_source",
              "key_batch", "link"]

    def run_check(self, utm, link):
        row = {"name": "Sam", "outlet": "Cozy Weekly", "contact": "sam@cozyweekly.net",
               "audience": "12k readers", "similar_games": "Unpacking", "status": "todo",
               "sent_date": "", "follow_up_date": "", "key_sent": "", "coverage_url": "",
               "utm_content": utm, "type": "press", "contact_source": "cozyweekly.net/about",
               "key_batch": "", "link": link}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "contacts.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self.HEADER)
                w.writeheader()
                w.writerow(row)
            return subprocess.run([sys.executable, str(OUTREACH), str(path), "--today", "2026-11-26"],
                                  capture_output=True, text=True)

    def test_underscore_name_ok(self):
        link = "https://store.steampowered.com/app/480/?utm_source=press&utm_medium=email&utm_campaign=launch&utm_content=cozy_weekly_sam"
        r = self.run_check("cozy_weekly_sam", link)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_hyphen_name_fails(self):
        link = "https://store.steampowered.com/app/480/?utm_source=press&utm_medium=email&utm_campaign=launch&utm_content=cozyweekly-sam"
        r = self.run_check("cozyweekly-sam", link)
        self.assertEqual(r.returncode, 1)
        self.assertIn("underscores", r.stdout)

    def test_post_id_ok(self):
        link = "https://store.steampowered.com/app/480/?utm_source=x&utm_medium=social&utm_campaign=demo&utm_content=2026-11-26-x-demo-live"
        r = self.run_check("2026-11-26-x-demo-live", link)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_bad_medium_and_case_fail(self):
        link = "https://store.steampowered.com/app/480/?utm_source=Press&utm_medium=referral&utm_campaign=launch&utm_content=cozy_weekly_sam"
        r = self.run_check("cozy_weekly_sam", link)
        self.assertEqual(r.returncode, 1)
        self.assertIn("must be lower case", r.stdout)
        self.assertIn("utm_medium 'referral'", r.stdout)


if __name__ == "__main__":
    unittest.main()
