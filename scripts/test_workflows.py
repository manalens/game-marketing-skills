#!/usr/bin/env python3
"""Checks the GitHub Actions workflows: every `uses:` is pinned to a full 40-character commit SHA
(local `./` actions excepted), and every workflow sets a top-level `permissions:` block.
Run: python3 scripts/test_workflows.py
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = sorted((ROOT / ".github/workflows").glob("*.y*ml"))
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*['\"]?([^'\"\s#]+)", re.M)
PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")


def unpinned(text):
    return [ref for ref in USES.findall(text) if not ref.startswith("./") and not PINNED.match(ref)]


class WorkflowPins(unittest.TestCase):
    def test_workflows_found(self):
        self.assertTrue(WORKFLOWS)

    def test_all_actions_pinned_by_sha(self):
        for path in WORKFLOWS:
            with self.subTest(workflow=path.name):
                self.assertEqual(unpinned(path.read_text()), [])

    def test_top_level_permissions(self):
        for path in WORKFLOWS:
            with self.subTest(workflow=path.name):
                self.assertRegex(path.read_text(), re.compile(r"^permissions:", re.M))

    def test_checker(self):
        self.assertEqual(unpinned("      - uses: actions/checkout@v4\n"), ["actions/checkout@v4"])
        self.assertEqual(unpinned("  - uses: ./local/action\n"), [])
        sha = "3d3c42e5aac5ba805825da76410c181273ba90b1"
        self.assertEqual(unpinned(f"    uses: actions/checkout@{sha} # v7.0.1\n"), [])
        self.assertEqual(unpinned(f"    uses: org/repo/.github/workflows/x.yml@{sha[:7]}\n"),
                         [f"org/repo/.github/workflows/x.yml@{sha[:7]}"])


if __name__ == "__main__":
    unittest.main()
