import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_dsa
import build_dsa_guide
import dsa_guide
import lint_dsa


class TestExampleRunner(unittest.TestCase):
    def test_example_does_not_write_to_callers_directory(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                code, error = verify_dsa.run('from pathlib import Path\nPath("probe.txt").write_text("ok")')
                self.assertEqual((code, error), (0, ""))
                self.assertFalse(Path("probe.txt").exists())
            finally:
                os.chdir(previous)

    def test_example_failure_is_reported(self):
        code, error = verify_dsa.run('raise ValueError("visible error")')
        self.assertNotEqual(code, 0)
        self.assertIn("visible error", error)

    def test_problem_card_links_enter_link_inventory(self):
        module = {
            "further": [],
            "items": [],
            "practice": [],
            "cards": {"1": {"md": "[reference](https://example.test/section)\n"
                                   "```python\nurl = 'https://not-a-link.test/'\n```"}},
        }
        self.assertEqual(build_dsa_guide.urls_of([module], None, []), {"https://example.test/section"})

    def test_video_duration_policy_checks_value_and_timestamp_parameter(self):
        url = "https://www.youtube.com/watch?v=example"
        self.assertEqual(lint_dsa.link_notes(url, "Read this: 20 min"), [])
        self.assertTrue(any("video without" in note for note in lint_dsa.link_notes(url, "Watch: 35 min")))
        self.assertTrue(any("video without" in note for note in lint_dsa.link_notes(url + "&start=90", "Watch: 35 min")))
        self.assertEqual(lint_dsa.link_notes(url + "&t=90", "Watch the marked segment"), [])

    def test_offline_problem_catalog_preserves_records_and_urls(self):
        catalog = {
            "1": ["Example", "E", "example", "", "", 0],
            "cses:1": ["Example task", "CSES", "https://cses.fi/problemset/task/1"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "dsa_catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
            with patch.object(build_dsa_guide, "HERE", root), patch.object(build_dsa_guide, "DATA", root / "missing"):
                problems = build_dsa_guide.Problems()
                self.assertEqual(problems.record("1"), catalog["1"])
                self.assertEqual(problems.record("cses:1"), catalog["cses:1"])
                self.assertIn("https://leetcode.com/problems/example/", problems.urls("1"))
                self.assertFalse(problems.known("2"))

    def test_invalid_offline_catalog_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "dsa_catalog.json").write_text('{"1": ["incomplete"]}', encoding="utf-8")
            with patch.object(build_dsa_guide, "HERE", root), patch.object(build_dsa_guide, "DATA", root / "missing"):
                with self.assertRaisesRegex(ValueError, "invalid record"):
                    build_dsa_guide.Problems()

    def test_strict_build_rejects_bad_card_before_writing(self):
        module = {
            "key": "test", "stage": "test", "bank": [],
            "items": [{"id": "l:test", "tag": ["test", "Test"], "p": []}],
            "practice": [{"id": "1", "tier": "core", "pattern": "test"}],
            "cards": {"1": {"md": "## The problem\nIncomplete.", "time": None}},
            "cards_name": "test.cards.md",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(build_dsa_guide, "HERE", root / "_build"), \
                 patch.object(build_dsa_guide, "load", return_value=([module], [])), \
                 patch.object(build_dsa_guide, "old_bank", return_value={}), \
                 patch.object(build_dsa_guide, "Problems") as problems, \
                 patch.object(dsa_guide, "TRACK", {"contentDir": "lessons"}), \
                 patch.object(dsa_guide, "STAGES", [{"key": "test"}]), \
                 redirect_stdout(StringIO()):
                problems.return_value.known.return_value = True
                problems.return_value.record.return_value = ["test", "M"]
                with self.assertRaises(SystemExit):
                    build_dsa_guide.build(strict=True)
            self.assertFalse((root / "lessons").exists())


if __name__ == "__main__":
    unittest.main()
