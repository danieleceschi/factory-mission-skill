from __future__ import annotations

import importlib.util
import json
import tempfile
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
    / "sync_private.py"
)
SPEC = importlib.util.spec_from_file_location("sync_private", SCRIPT)
assert SPEC and SPEC.loader
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class PrivateSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.public = self.root / "public"
        self.overlay = self.root / "overlay"
        self.private = self.root / "private"
        (self.public / "references").mkdir(parents=True)
        (self.public / "evals").mkdir()
        (self.public / "evals/replay").mkdir()
        self.overlay.mkdir()
        (self.public / "SKILL.md").write_text(
            "---\nname: factory-mission\nmetadata:\n  version: 1.2.0\n---\n\n## Models\n\nPublic policy.\n",
            encoding="utf-8",
        )
        (self.public / "evals/evals.json").write_text(
            json.dumps({"version": "1.2.0", "cases": []}) + "\n", encoding="utf-8"
        )
        (self.public / "evals/replay/cases.json").write_text(
            json.dumps({"schema_version": 1, "cases": []}) + "\n", encoding="utf-8"
        )
        (self.overlay / "fragment.md").write_text("Read private policy.\n\n", encoding="utf-8")
        (self.overlay / "policy.md").write_text("Private value.\n", encoding="utf-8")
        (self.overlay / "extra.json").write_text(
            json.dumps([{"id": "private-case"}]) + "\n", encoding="utf-8"
        )
        (self.overlay / "extra-replay.json").write_text(
            json.dumps([{"id": "private-case", "events": []}]) + "\n", encoding="utf-8"
        )
        (self.overlay / "overlay.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "version_suffix": "-private.1",
                    "metadata": {"private-variant": True},
                    "text_operations": [
                        {"path": "SKILL.md", "after": "## Models\n\n", "fragment": "fragment.md"}
                    ],
                    "files": [
                        {"source": "policy.md", "target": "references/private-policy.md"}
                    ],
                    "extra_evals": "extra.json",
                    "extra_replays": "extra-replay.json",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_sync(self, *extra: str) -> int:
        return SYNC.main(
            [
                "--source",
                str(self.public),
                "--target",
                str(self.private),
                "--overlay",
                str(self.overlay),
                *extra,
            ]
        )

    def test_sync_applies_overlay_and_becomes_idempotent(self) -> None:
        self.assertEqual(self.run_sync("--apply"), 0)
        skill = (self.private / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("version: 1.2.0-private.1", skill)
        self.assertIn("private-variant: true", skill)
        self.assertIn("Read private policy.", skill)
        self.assertEqual((self.private / "references/private-policy.md").read_text(), "Private value.\n")
        evals = json.loads((self.private / "evals/evals.json").read_text())
        self.assertEqual(evals["version"], "1.2.0-private.1")
        self.assertEqual(evals["cases"], [{"id": "private-case"}])
        replays = json.loads((self.private / "evals/replay/cases.json").read_text())
        self.assertEqual(replays["cases"], [{"id": "private-case", "events": []}])
        self.assertEqual(
            {case["id"] for case in evals["cases"]},
            {case["id"] for case in replays["cases"]},
        )
        self.assertEqual(self.run_sync(), 0)

    def test_sync_refuses_to_overwrite_private_drift(self) -> None:
        self.assertEqual(self.run_sync("--apply"), 0)
        (self.private / "SKILL.md").write_text("manual private edit\n", encoding="utf-8")
        self.assertEqual(self.run_sync("--apply"), 2)
        self.assertEqual((self.private / "SKILL.md").read_text(), "manual private edit\n")

    def test_first_sync_requires_explicit_adoption_of_unmanaged_target(self) -> None:
        self.private.mkdir()
        (self.private / "SKILL.md").write_text("old private copy\n", encoding="utf-8")
        self.assertEqual(self.run_sync("--apply"), 2)
        self.assertEqual(self.run_sync("--apply", "--adopt-existing"), 0)


if __name__ == "__main__":
    unittest.main()
