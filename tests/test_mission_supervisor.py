from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
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
    / "mission_supervisor.py"
)
SPEC = importlib.util.spec_from_file_location("mission_supervisor", SCRIPT)
assert SPEC and SPEC.loader
SUPERVISOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUPERVISOR)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class MissionSupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Tests")
        (self.repo / "app.txt").write_text("ready\n", encoding="utf-8")
        git(self.repo, "add", "app.txt")
        git(self.repo, "commit", "-m", "initial")
        self.checkpoint = self.root / "checkpoint.json"
        result = SUPERVISOR.main(
            [
                "init",
                str(self.checkpoint),
                "--repo",
                str(self.repo),
                "--objective",
                "Finish the fixture Mission",
                "--acceptance-id",
                "VAL-1",
                "--session-id",
                "session-1",
            ]
        )
        self.assertEqual(result, 0)
        SUPERVISOR.acquire_lease(self.checkpoint, "test-controller", 300)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_replay_cases_produce_required_states(self) -> None:
        cases = json.loads(
            (
                ROOT
                / "plugins/factory-mission/skills/factory-mission/evals/replay/cases.json"
            ).read_text(encoding="utf-8")
        )["cases"]
        behavior_cases = json.loads(
            (
                ROOT
                / "plugins/factory-mission/skills/factory-mission/evals/evals.json"
            ).read_text(encoding="utf-8")
        )["cases"]
        self.assertEqual({case["id"] for case in cases}, {case["id"] for case in behavior_cases})
        self.assertEqual(len(cases), 23)
        for case in cases:
            with self.subTest(case=case["id"]):
                state = {
                    "status": "ready",
                    "seen_event_ids": [],
                    "events": [],
                    "active_workers": [],
                    "requests": {},
                    "recovery_attempts": {},
                }
                actions = []
                for event in case["events"]:
                    actions.append(SUPERVISOR.append_event(state, event))
                self.assertEqual(state["status"], case["expected_status"])
                self.assertEqual(actions, case["expected_actions"])

    def test_droid_command_preserves_session_worktree_and_models(self) -> None:
        state = SUPERVISOR.read_json(self.checkpoint)
        state["model_policy"] = {
            "orchestrator": "orchestrator-model",
            "worker": "worker-model",
            "validator": "validator-model",
        }
        prompt = self.root / "brief.md"
        args = argparse.Namespace(droid="droid")
        command = SUPERVISOR.build_droid_command(state, args, prompt)
        self.assertEqual(command[:5], ["droid", "exec", "--mission", "--auto", "high"])
        self.assertIn(state["worktree"], command)
        self.assertEqual(command[command.index("--session-id") + 1], "session-1")
        self.assertEqual(command[command.index("--model") + 1], "orchestrator-model")
        self.assertEqual(command[command.index("--worker-model") + 1], "worker-model")
        self.assertEqual(command[command.index("--validator-model") + 1], "validator-model")

    def test_lease_prevents_a_second_controller(self) -> None:
        with self.assertRaisesRegex(SUPERVISOR.SupervisorError, "held by"):
            SUPERVISOR.acquire_lease(self.checkpoint, "other-controller", 300)

    def test_delivered_request_is_not_answered_twice(self) -> None:
        state = SUPERVISOR.read_json(self.checkpoint)
        SUPERVISOR.append_event(
            state,
            {"type": "question", "id": "event-1", "request_id": "question-1", "text": "Proceed?"},
        )
        SUPERVISOR.atomic_write_json(self.checkpoint, state)
        SUPERVISOR.record_answer(
            self.checkpoint, "test-controller", "question-1", "Proceed within scope", "delivered"
        )

        def replay(current: dict) -> None:
            action = SUPERVISOR.append_event(
                current,
                {"type": "question", "id": "event-2", "request_id": "question-1", "text": "Proceed?"},
            )
            self.assertEqual(action, "ignore_delivered_request")

        final = SUPERVISOR.mutate_checkpoint(self.checkpoint, "test-controller", replay)
        self.assertEqual(final["requests"]["question-1"]["delivery"], "delivered")

    def test_raw_rpc_question_preserves_request_identity(self) -> None:
        event = SUPERVISOR.normalize_factory_event(
            {"jsonrpc": "2.0", "id": "rpc-42", "method": "droid.ask_user", "params": {"question": "Runner?"}}
        )
        self.assertEqual(event["request_id"], "rpc-42")
        self.assertEqual(event["type"], "question")

    def test_model_policy_event_requires_and_records_all_roles(self) -> None:
        state = {"status": "running", "seen_event_ids": [], "events": []}
        with self.assertRaisesRegex(SUPERVISOR.SupervisorError, "all three"):
            SUPERVISOR.append_event(
                state,
                {"type": "model_policy_applied", "id": "bad", "roles": {"worker": "x"}},
            )
        action = SUPERVISOR.append_event(
            state,
            {
                "type": "model_policy_applied",
                "id": "good",
                "roles": {"orchestrator": "x", "worker": "x", "validator": "x"},
            },
        )
        self.assertEqual(action, "validate_model_policy")
        self.assertEqual(set(state["model_policy"]), {"orchestrator", "worker", "validator"})

    def test_evidence_invalidates_after_dirty_diff(self) -> None:
        manifest_path = self.root / "evidence.json"
        artifact = self.root / "test-output.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        manifest = SUPERVISOR.new_evidence_manifest(self.repo, ["VAL-1"], True, False)
        SUPERVISOR.atomic_write_json(manifest_path, manifest)
        SUPERVISOR.evidence_record(manifest_path, "assertion", "VAL-1", "test", 0, [artifact])
        SUPERVISOR.evidence_record(manifest_path, "validator", "scrutiny", "review", 0, [artifact])
        verified = SUPERVISOR.verify_evidence(SUPERVISOR.read_json(manifest_path))
        self.assertTrue(verified["complete"])

        (self.repo / "app.txt").write_text("changed after tests\n", encoding="utf-8")
        stale = SUPERVISOR.verify_evidence(SUPERVISOR.read_json(manifest_path))
        self.assertFalse(stale["complete"])
        self.assertTrue(any("dirty diff" in failure for failure in stale["failures"]))

    def test_evidence_invalidates_when_artifact_changes(self) -> None:
        manifest_path = self.root / "evidence.json"
        artifact = self.root / "test-output.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        SUPERVISOR.atomic_write_json(
            manifest_path,
            SUPERVISOR.new_evidence_manifest(self.repo, ["VAL-1"], False, False),
        )
        SUPERVISOR.evidence_record(manifest_path, "assertion", "VAL-1", "test", 0, [artifact])
        artifact.write_text("edited\n", encoding="utf-8")
        verified = SUPERVISOR.verify_evidence(SUPERVISOR.read_json(manifest_path))
        self.assertFalse(verified["complete"])
        self.assertTrue(any("artifact changed" in failure for failure in verified["failures"]))

    def test_evidence_run_records_actual_exit_and_output(self) -> None:
        manifest_path = self.root / "evidence.json"
        artifact = self.root / "command-output.txt"
        SUPERVISOR.atomic_write_json(
            manifest_path,
            SUPERVISOR.new_evidence_manifest(self.repo, ["VAL-1"], False, False),
        )
        result = SUPERVISOR.main(
            [
                "evidence-run",
                str(manifest_path),
                "--assertion",
                "VAL-1",
                "--artifact",
                str(artifact),
                "--",
                "git",
                "status",
                "--short",
            ]
        )
        self.assertEqual(result, 0)
        record = SUPERVISOR.read_json(manifest_path)["assertions"]["VAL-1"]
        self.assertTrue(record["passed"])
        self.assertEqual(record["exit_code"], 0)
        self.assertTrue(artifact.is_file())

    def test_completion_manifest_requires_an_assertion(self) -> None:
        with self.assertRaisesRegex(SUPERVISOR.SupervisorError, "At least one"):
            SUPERVISOR.new_evidence_manifest(self.repo, [], False, False)

    def test_checkpoint_completes_only_with_fresh_required_evidence(self) -> None:
        manifest_path = self.root / "evidence.json"
        artifact = self.root / "check.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        SUPERVISOR.atomic_write_json(
            manifest_path,
            SUPERVISOR.new_evidence_manifest(self.repo, ["VAL-1"], False, False),
        )
        SUPERVISOR.evidence_record(manifest_path, "assertion", "VAL-1", "test", 0, [artifact])
        result = SUPERVISOR.complete_checkpoint(
            self.checkpoint, "test-controller", manifest_path
        )
        self.assertTrue(result["complete"])
        self.assertEqual(result["state"]["status"], "complete")

    def test_checkpoint_refuses_stale_evidence(self) -> None:
        manifest_path = self.root / "evidence.json"
        artifact = self.root / "check.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        SUPERVISOR.atomic_write_json(
            manifest_path,
            SUPERVISOR.new_evidence_manifest(self.repo, ["VAL-1"], False, False),
        )
        SUPERVISOR.evidence_record(manifest_path, "assertion", "VAL-1", "test", 0, [artifact])
        (self.repo / "app.txt").write_text("changed\n", encoding="utf-8")
        result = SUPERVISOR.complete_checkpoint(
            self.checkpoint, "test-controller", manifest_path
        )
        self.assertFalse(result["complete"])
        self.assertEqual(result["state"]["status"], "verifying")

    def test_checkpoint_requires_all_declared_acceptance_ids(self) -> None:
        manifest_path = self.root / "evidence.json"
        artifact = self.root / "check.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        SUPERVISOR.atomic_write_json(
            manifest_path,
            SUPERVISOR.new_evidence_manifest(self.repo, ["OTHER"], False, False),
        )
        SUPERVISOR.evidence_record(manifest_path, "assertion", "OTHER", "test", 0, [artifact])
        result = SUPERVISOR.complete_checkpoint(
            self.checkpoint, "test-controller", manifest_path
        )
        self.assertFalse(result["complete"])
        self.assertTrue(any("VAL-1" in failure for failure in result["verification"]["failures"]))


if __name__ == "__main__":
    unittest.main()
