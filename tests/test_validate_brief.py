from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "plugins"
    / "factory-mission"
    / "skills"
    / "factory-mission"
    / "scripts"
    / "validate_brief.py"
)
SPEC = importlib.util.spec_from_file_location("validate_brief", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ValidateBriefTests(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        result = MODULE.validate_file(ROOT / "tests" / "fixtures" / "valid-brief.md")
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.assertions, 5)
        self.assertEqual(result.features, 3)
        self.assertEqual(result.milestones, 2)
        self.assertEqual(result.worker_run_floor, 7)

    def test_invalid_fixture_reports_structural_failures(self) -> None:
        result = MODULE.validate_file(ROOT / "tests" / "fixtures" / "invalid-brief.md")
        self.assertFalse(result.valid)
        joined = "\n".join(result.errors)
        self.assertIn("Mission title must contain 3-8 words", joined)
        self.assertIn("VAL-AUTH-01 is missing fields: Evidence:", joined)
        self.assertIn("M1 is missing an Exit: clause", joined)
        self.assertIn("Assertions not covered by a feature", joined)

    def test_one_fenced_brief_is_supported(self) -> None:
        fixture = (ROOT / "tests" / "fixtures" / "valid-brief.md").read_text(encoding="utf-8")
        result = MODULE.validate_text(f"Recommendation\n\n```markdown\n{fixture}\n```")
        self.assertTrue(result.valid, result.errors)


if __name__ == "__main__":
    unittest.main()
