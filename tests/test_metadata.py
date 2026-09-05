from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "factory-mission"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class MetadataTests(unittest.TestCase):
    def test_plugin_manifests_agree(self) -> None:
        manifests = [
            load_json(PLUGIN / ".codex-plugin" / "plugin.json"),
            load_json(PLUGIN / ".factory-plugin" / "plugin.json"),
            load_json(PLUGIN / ".claude-plugin" / "plugin.json"),
        ]
        self.assertEqual({item["name"] for item in manifests}, {"factory-mission"})
        self.assertEqual({item["version"] for item in manifests}, {"1.0.0"})
        self.assertEqual({item["description"] for item in manifests}, {
            "Plan, audit, launch, monitor, resume, and steer Factory Missions."
        })

    def test_marketplaces_reference_the_plugin(self) -> None:
        paths = [
            ROOT / ".agents" / "plugins" / "marketplace.json",
            ROOT / ".factory-plugin" / "marketplace.json",
            ROOT / ".claude-plugin" / "marketplace.json",
        ]
        for path in paths:
            data = load_json(path)
            self.assertEqual(data["name"], "factory-mission-skill")
            self.assertEqual(len(data["plugins"]), 1)
            self.assertEqual(data["plugins"][0]["name"], "factory-mission")

    def test_public_package_has_no_personal_machine_values(self) -> None:
        forbidden = (
            "C:" + "\\Users\\",
            "OpenRouter" + "-Free-Router",
            "fk" + "-",
        )
        for path in ROOT.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".py"}:
                text = path.read_text(encoding="utf-8")
                for value in forbidden:
                    self.assertNotIn(value, text, f"{value!r} found in {path}")


if __name__ == "__main__":
    unittest.main()
