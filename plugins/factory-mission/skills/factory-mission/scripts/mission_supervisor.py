#!/usr/bin/env python3
"""Crash-safe state and evidence helper for Factory Mission supervision.

This module never grants authority or chooses an answer.  It makes the host
agent's decisions durable, prevents concurrent controllers, records Factory
events, and verifies that acceptance evidence still matches the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
TERMINAL_STATES = {"complete", "blocked", "stopped"}
MODEL_FLAGS = {
    "orchestrator": "--model",
    "worker": "--worker-model",
    "validator": "--validator-model",
}


class SupervisorError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SupervisorError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SupervisorError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise SupervisorError(f"Unsupported schema in {path}")
    return data


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def checkpoint_lock(path: Path, timeout: float = 5.0) -> Iterable[None]:
    lock = path.with_name(path.name + ".lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
                if age > 60:
                    lock.rmdir()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise SupervisorError(f"Checkpoint is locked: {path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def repository_identity(repo: Path) -> dict[str, str]:
    repo = repo.resolve()
    root = Path(run_git(repo, "rev-parse", "--show-toplevel").stdout.decode().strip()).resolve()
    head = run_git(root, "rev-parse", "HEAD").stdout.decode().strip()
    return {"root": str(root), "head": head}


def repository_fingerprint(repo: Path) -> dict[str, str]:
    identity = repository_identity(repo)
    root = Path(identity["root"])
    digest = hashlib.sha256()
    digest.update(identity["head"].encode())
    diff = run_git(root, "diff", "--binary", "HEAD", "--").stdout
    digest.update(diff)
    untracked = run_git(
        root, "ls-files", "--others", "--exclude-standard", "-z"
    ).stdout.split(b"\0")
    for raw_name in sorted(name for name in untracked if name):
        digest.update(b"\0path\0" + raw_name)
        file_path = root / os.fsdecode(raw_name)
        if file_path.is_file():
            digest.update(file_path.read_bytes())
        elif file_path.exists():
            digest.update(b"<non-file>")
    return {
        "root": identity["root"],
        "head": identity["head"],
        "worktree_sha256": digest.hexdigest(),
    }


def assert_owner(state: dict[str, Any], owner: str) -> None:
    controller = state["controller"]
    expires = parse_time(controller.get("lease_expires_at"))
    if controller.get("owner") != owner or not expires or expires <= datetime.now(timezone.utc):
        raise SupervisorError("An active lease for this owner is required")


def mutate_checkpoint(path: Path, owner: str, mutator: Any) -> dict[str, Any]:
    with checkpoint_lock(path):
        state = read_json(path)
        assert_owner(state, owner)
        mutator(state)
        state["updated_at"] = utc_now()
        atomic_write_json(path, state)
        return state


def acquire_lease(path: Path, owner: str, ttl_seconds: int) -> dict[str, Any]:
    if ttl_seconds < 30:
        raise SupervisorError("Lease TTL must be at least 30 seconds")
    with checkpoint_lock(path):
        state = read_json(path)
        controller = state["controller"]
        expires = parse_time(controller.get("lease_expires_at"))
        now = datetime.now(timezone.utc)
        held_by_other = controller.get("owner") not in (None, owner) and expires and expires > now
        if held_by_other:
            raise SupervisorError(
                f"Controller lease is held by {controller['owner']} until "
                f"{controller['lease_expires_at']}"
            )
        controller.update(
            {
                "owner": owner,
                "lease_expires_at": (now + timedelta(seconds=ttl_seconds))
                .isoformat()
                .replace("+00:00", "Z"),
            }
        )
        state["updated_at"] = utc_now()
        atomic_write_json(path, state)
        return state


def release_lease(path: Path, owner: str) -> dict[str, Any]:
    def release(state: dict[str, Any]) -> None:
        state["controller"] = {"owner": None, "lease_expires_at": None}

    return mutate_checkpoint(path, owner, release)


def append_event(state: dict[str, Any], event: dict[str, Any]) -> str:
    event_type = event.get("type")
    if not isinstance(event_type, str):
        raise SupervisorError("Event requires a string type")
    event_id = str(event.get("id") or hashlib.sha256(
        json.dumps(event, sort_keys=True).encode()
    ).hexdigest()[:16])
    seen = state.setdefault("seen_event_ids", [])
    if event_id in seen:
        return "ignore_duplicate_event"
    seen.append(event_id)
    if len(seen) > 1000:
        del seen[:-1000]
    event = {**event, "id": event_id, "observed_at": utc_now()}
    state.setdefault("events", []).append(event)
    state["events"] = state["events"][-200:]
    state["last_observation_at"] = event["observed_at"]

    workers = state.setdefault("active_workers", [])
    requests = state.setdefault("requests", {})
    action = "observe"
    if event_type == "scope_selected":
        mode = str(event.get("mode", ""))
        actions = {
            "brief": "draft_brief",
            "audit": "audit_brief",
            "explain": "explain_only",
            "direct_session": "recommend_direct_session",
            "portfolio": "draft_bounded_portfolio",
            "safety_gated_brief": "draft_safety_gated_brief",
            "completion": "prepare_and_supervise",
            "launch": "launch_and_supervise",
            "monitor": "observe",
            "launch_only": "launch_and_return",
        }
        if mode not in actions:
            raise SupervisorError(f"Unknown scope mode: {mode}")
        state["operating_mode"] = mode
        if mode in {"completion", "launch", "monitor", "launch_only"}:
            state["status"] = "running"
        else:
            state["status"] = "ready"
        action = actions[mode]
    elif event_type == "model_policy_applied":
        roles = event.get("roles")
        required_roles = {"orchestrator", "worker", "validator"}
        if not isinstance(roles, dict) or not required_roles.issubset(roles):
            raise SupervisorError("Model policy event requires all three Mission roles")
        state["model_policy"] = {role: str(roles[role]) for role in sorted(required_roles)}
        action = "validate_model_policy"
    elif event_type == "worker_started":
        worker = str(event.get("worker_id", "unknown"))
        if worker not in workers:
            workers.append(worker)
        state["status"] = "running"
    elif event_type == "worker_completed":
        worker = str(event.get("worker_id", "unknown"))
        if worker in workers:
            workers.remove(worker)
        state["status"] = "running" if workers else "turn_complete"
        action = "inspect_outcome"
    elif event_type in {"question", "permission_request"}:
        request_id = str(event.get("request_id") or event_id)
        prior = requests.get(request_id)
        if prior and prior.get("delivery") == "delivered":
            return "ignore_delivered_request"
        requests[request_id] = {
            "kind": event_type,
            "text": str(event.get("text", "")),
            "delivery": prior.get("delivery", "pending") if prior else "pending",
            "answer": prior.get("answer") if prior else None,
            "observed_at": event["observed_at"],
        }
        if event_type == "permission_request":
            state["status"] = "awaiting_authority"
            action = "review_authority"
        else:
            state["status"] = "awaiting_answer"
            action = "resolve_question"
    elif event_type == "validation":
        state.setdefault("latest_validation", {})[str(event.get("assertion_id"))] = event
        if event.get("passed") is True:
            action = "observe"
        else:
            state["status"] = "recovering"
            action = "repair_and_revalidate"
    elif event_type == "failure":
        cause = str(event.get("cause", "unknown"))
        attempts = state.setdefault("recovery_attempts", {})
        attempts[cause] = attempts.get(cause, 0) + 1
        if event.get("recoverable") is False:
            state["status"] = "blocked"
            action = "report_blocker"
        elif attempts[cause] > 2:
            state["status"] = "blocked"
            action = "report_repeated_blocker"
        else:
            state["status"] = "recovering"
            action = "diagnose_and_repair"
    elif event_type == "mission_reported_complete":
        state["status"] = "verifying"
        action = "verify_evidence"
    elif event_type == "stopped":
        state["status"] = "stopped"
        action = "stop"
    elif event_type == "host_continuity_unavailable":
        state["status"] = "stopped"
        action = "report_resume_context"
    elif event_type == "heartbeat":
        action = "observe"
    else:
        action = "inspect_event"
    state["next_action"] = action
    return action


def normalize_factory_event(raw: dict[str, Any]) -> dict[str, Any] | None:
    method = raw.get("method")
    if method in {"droid.ask_user", "droid.request_permission"}:
        params = raw.get("params") if isinstance(raw.get("params"), dict) else {}
        return {
            "type": "question" if method == "droid.ask_user" else "permission_request",
            "id": f"rpc:{raw.get('id')}",
            "request_id": str(raw.get("id")),
            "text": str(params.get("question") or params.get("prompt") or params),
            "raw_method": method,
        }
    if raw.get("type") == "result":
        result = raw.get("result")
        return {
            "type": "turn_result",
            "id": f"result:{raw.get('session_id')}:{raw.get('duration_ms')}:{raw.get('num_turns')}",
            "session_id": raw.get("session_id"),
            "success": not bool(raw.get("is_error")),
            "text": result if isinstance(result, str) else "",
        }
    return None


def record_answer(path: Path, owner: str, request_id: str, answer: str, delivery: str) -> dict[str, Any]:
    if delivery not in {"prepared", "submitted", "delivered"}:
        raise SupervisorError("Delivery must be prepared, submitted, or delivered")

    def record(state: dict[str, Any]) -> None:
        request = state.setdefault("requests", {}).get(request_id)
        if not request:
            raise SupervisorError(f"Unknown request: {request_id}")
        if request.get("delivery") == "delivered" and delivery != "delivered":
            raise SupervisorError(f"Request {request_id} is already delivered")
        request.update({"answer": answer, "delivery": delivery, "updated_at": utc_now()})
        waiting = "awaiting_authority" if request.get("kind") == "permission_request" else "awaiting_answer"
        state["status"] = "running" if delivery == "delivered" else waiting
        state["next_action"] = "observe" if delivery == "delivered" else "deliver_answer"

    return mutate_checkpoint(path, owner, record)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_evidence_manifest(repo: Path, required: list[str], scrutiny: bool, user_testing: bool) -> dict[str, Any]:
    if not required:
        raise SupervisorError("At least one required acceptance assertion is needed")
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repo.resolve()),
        "required_assertions": sorted(set(required)),
        "required_validators": {
            "scrutiny": scrutiny,
            "user_testing": user_testing,
        },
        "assertions": {},
        "validators": {},
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def evidence_record(
    manifest_path: Path,
    category: str,
    item_id: str,
    command: str,
    exit_code: int,
    artifacts: list[Path],
) -> dict[str, Any]:
    if not artifacts:
        raise SupervisorError("At least one evidence artifact is required")
    with checkpoint_lock(manifest_path):
        manifest = read_json(manifest_path)
        repository = Path(manifest["repository"]).resolve()
        fingerprint = repository_fingerprint(repository)
        artifact_records = []
        for artifact in artifacts:
            artifact = artifact.resolve()
            if not artifact.is_file():
                raise SupervisorError(f"Evidence artifact is not a file: {artifact}")
            if artifact.is_relative_to(repository):
                raise SupervisorError("Evidence artifacts must be outside the repository")
            artifact_records.append({"path": str(artifact), "sha256": sha256_file(artifact)})
        record = {
            "command": command,
            "exit_code": exit_code,
            "passed": exit_code == 0,
            "revision": fingerprint,
            "artifacts": artifact_records,
            "recorded_at": utc_now(),
        }
        bucket = manifest["assertions"] if category == "assertion" else manifest["validators"]
        bucket[item_id] = record
        manifest["updated_at"] = utc_now()
        atomic_write_json(manifest_path, manifest)
        return manifest


def verify_evidence(manifest: dict[str, Any]) -> dict[str, Any]:
    current = repository_fingerprint(Path(manifest["repository"]))
    failures: list[str] = []
    checked: list[str] = []

    def check_record(label: str, record: Any) -> None:
        if not isinstance(record, dict):
            failures.append(f"{label}: missing evidence")
            return
        if record.get("passed") is not True:
            failures.append(f"{label}: check failed")
        revision = record.get("revision", {})
        if revision.get("head") != current["head"] or revision.get("worktree_sha256") != current["worktree_sha256"]:
            failures.append(f"{label}: evidence is stale for the current commit or dirty diff")
        for artifact in record.get("artifacts", []):
            path = Path(artifact.get("path", ""))
            if not path.is_file():
                failures.append(f"{label}: artifact missing: {path}")
            elif sha256_file(path) != artifact.get("sha256"):
                failures.append(f"{label}: artifact changed: {path}")
        checked.append(label)

    for assertion in manifest.get("required_assertions", []):
        check_record(f"assertion:{assertion}", manifest.get("assertions", {}).get(assertion))
    for validator, required in manifest.get("required_validators", {}).items():
        if required:
            check_record(f"validator:{validator}", manifest.get("validators", {}).get(validator))
    return {
        "complete": not failures,
        "current_revision": current,
        "checked": checked,
        "failures": failures,
    }


def update_from_raw_line(state: dict[str, Any], line: str) -> None:
    try:
        raw = json.loads(line)
    except json.JSONDecodeError:
        return
    if not isinstance(raw, dict):
        return
    session_id = raw.get("session_id")
    if session_id:
        current = state.get("session_id")
        if current and current != session_id:
            raise SupervisorError(f"Session changed from {current} to {session_id}")
        state["session_id"] = session_id
    event = normalize_factory_event(raw)
    if event:
        append_event(state, event)


def complete_checkpoint(
    checkpoint: Path, owner: str, manifest_path: Path
) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    report = verify_evidence(manifest)

    def complete(state: dict[str, Any]) -> None:
        missing = sorted(
            set(state.get("acceptance_ids", []))
            - set(manifest.get("required_assertions", []))
        )
        if missing:
            report["complete"] = False
            report["failures"].append(
                "manifest does not require checkpoint acceptance IDs: " + ", ".join(missing)
            )
        state["completion_evidence"] = {
            "manifest": str(manifest_path.resolve()),
            "verified_at": utc_now(),
            "revision": report["current_revision"],
            "failures": report["failures"],
        }
        if report["complete"]:
            state["status"] = "complete"
            state["next_action"] = None
        else:
            state["status"] = "verifying"
            state["next_action"] = "repair_and_revalidate"

    state = mutate_checkpoint(checkpoint, owner, complete)
    return {"complete": report["complete"], "verification": report, "state": state}


def build_droid_command(
    state: dict[str, Any], args: argparse.Namespace, prompt: Path
) -> list[str]:
    command = [args.droid, "exec", "--mission", "--auto", "high"]
    command += ["--cwd", state["worktree"], "--output-format", "stream-json"]
    if state.get("session_id"):
        command += ["--session-id", state["session_id"]]
    for role, model in state.get("model_policy", {}).items():
        if role in MODEL_FLAGS and model:
            command += [MODEL_FLAGS[role], model]
    command += ["--file", str(prompt)]
    return command


def run_turn(args: argparse.Namespace) -> int:
    checkpoint = Path(args.checkpoint).resolve()
    prompt = Path(args.prompt_file).resolve()
    if not prompt.is_file():
        raise SupervisorError(f"Prompt file is missing: {prompt}")
    acquire_lease(checkpoint, args.owner, args.lease_ttl)
    state = read_json(checkpoint)
    if state.get("status") in TERMINAL_STATES:
        raise SupervisorError(f"Cannot run a turn from terminal state {state['status']}")
    prior_process = state.get("process") or {}
    prior_pid = prior_process.get("pid")
    if prior_pid and not prior_process.get("ended_at") and process_alive(int(prior_pid)):
        raise SupervisorError(f"Recorded Droid process is still active: {prior_pid}")
    command = build_droid_command(state, args, prompt)
    log_path = Path(args.log).resolve() if args.log else checkpoint.with_suffix(".jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def mark_start(current: dict[str, Any]) -> None:
        current["status"] = "running"
        current["process"] = {"pid": None, "log": str(log_path), "started_at": utc_now()}
        if args.answers_request:
            request = current.setdefault("requests", {}).get(args.answers_request)
            if not request or request.get("delivery") != "prepared":
                raise SupervisorError("The answered request must exist in prepared state")
            request["delivery"] = "submitted"

    mutate_checkpoint(checkpoint, args.owner, mark_start)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    renewal_stop = threading.Event()
    renewal_error: list[BaseException] = []

    def renew_lease() -> None:
        while not renewal_stop.wait(max(10, args.lease_ttl // 3)):
            try:
                acquire_lease(checkpoint, args.owner, args.lease_ttl)
            except BaseException as exc:  # Surface loss of exclusive control to the main thread.
                renewal_error.append(exc)
                try:
                    process.terminate()
                except OSError:
                    pass
                return

    renewal = threading.Thread(target=renew_lease, name="mission-lease-renewal", daemon=True)
    renewal.start()

    def save_pid(current: dict[str, Any]) -> None:
        current["process"]["pid"] = process.pid

    mutate_checkpoint(checkpoint, args.owner, save_pid)
    try:
        with log_path.open("a", encoding="utf-8", newline="\n") as log:
            assert process.stdout is not None
            for line in process.stdout:
                sys.stdout.write(line)
                log.write(line)
                log.flush()

                def observe(current: dict[str, Any], value: str = line) -> None:
                    update_from_raw_line(current, value)

                mutate_checkpoint(checkpoint, args.owner, observe)
        exit_code = process.wait()
    except BaseException:
        try:
            process.terminate()
            process.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
        raise
    finally:
        renewal_stop.set()
        renewal.join(timeout=5)
    if renewal_error:
        raise SupervisorError(f"Lost controller lease while Droid was active: {renewal_error[0]}")

    def mark_exit(current: dict[str, Any]) -> None:
        current["process"]["exit_code"] = exit_code
        current["process"]["ended_at"] = utc_now()
        pending = any(
            request.get("delivery") != "delivered"
            for request in current.get("requests", {}).values()
        )
        if pending:
            current["status"] = "awaiting_answer"
            current["next_action"] = "resolve_or_verify_request"
        elif exit_code:
            append_event(current, {"type": "failure", "cause": f"droid-exit-{exit_code}"})
        else:
            current["status"] = "turn_complete"
            current["next_action"] = "inspect_outcome"

    mutate_checkpoint(checkpoint, args.owner, mark_exit)
    return exit_code


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a supervisor checkpoint")
    init.add_argument("checkpoint")
    init.add_argument("--repo", required=True)
    init.add_argument("--worktree")
    init.add_argument("--objective", required=True)
    init.add_argument("--acceptance-id", action="append", default=[])
    init.add_argument("--session-id")
    init.add_argument("--mission-id")
    init.add_argument("--orchestrator-model")
    init.add_argument("--worker-model")
    init.add_argument("--validator-model")

    lease = sub.add_parser("lease", help="Acquire or renew a controller lease")
    lease.add_argument("checkpoint")
    lease.add_argument("--owner", required=True)
    lease.add_argument("--ttl", type=int, default=300)

    release = sub.add_parser("release", help="Release a controller lease")
    release.add_argument("checkpoint")
    release.add_argument("--owner", required=True)

    event = sub.add_parser("event", help="Record one normalized Factory event")
    event.add_argument("checkpoint")
    event.add_argument("--owner", required=True)
    event.add_argument("--json", required=True)

    replay = sub.add_parser("replay", help="Replay normalized JSONL events")
    replay.add_argument("checkpoint")
    replay.add_argument("events")
    replay.add_argument("--owner", required=True)

    answer = sub.add_parser("answer", help="Record answer preparation and delivery")
    answer.add_argument("checkpoint")
    answer.add_argument("--owner", required=True)
    answer.add_argument("--request-id", required=True)
    answer.add_argument("--answer", required=True)
    answer.add_argument("--delivery", choices=["prepared", "submitted", "delivered"], required=True)

    run = sub.add_parser("run-turn", help="Run one authorized Droid Mission turn")
    run.add_argument("checkpoint")
    run.add_argument("--owner", required=True)
    run.add_argument("--prompt-file", required=True)
    run.add_argument("--answers-request")
    run.add_argument("--log")
    run.add_argument("--droid", default="droid")
    run.add_argument("--lease-ttl", type=int, default=300)

    status = sub.add_parser("status", help="Print checkpoint state")
    status.add_argument("checkpoint")

    evidence_init = sub.add_parser("evidence-init", help="Create an evidence manifest")
    evidence_init.add_argument("manifest")
    evidence_init.add_argument("--repo", required=True)
    evidence_init.add_argument("--required", action="append", default=[])
    evidence_init.add_argument("--require-scrutiny", action="store_true")
    evidence_init.add_argument("--require-user-testing", action="store_true")

    evidence_add = sub.add_parser("evidence-record", help="Record revision-bound evidence")
    evidence_add.add_argument("manifest")
    group = evidence_add.add_mutually_exclusive_group(required=True)
    group.add_argument("--assertion")
    group.add_argument("--validator", choices=["scrutiny", "user_testing"])
    evidence_add.add_argument("--command", required=True)
    evidence_add.add_argument("--exit-code", type=int, required=True)
    evidence_add.add_argument("--artifact", action="append", required=True)

    evidence_run = sub.add_parser("evidence-run", help="Run a check and record its output")
    evidence_run.add_argument("manifest")
    run_group = evidence_run.add_mutually_exclusive_group(required=True)
    run_group.add_argument("--assertion")
    run_group.add_argument("--validator", choices=["scrutiny", "user_testing"])
    evidence_run.add_argument("--artifact", required=True)

    evidence_verify = sub.add_parser("evidence-verify", help="Verify completion evidence")
    evidence_verify.add_argument("manifest")

    complete = sub.add_parser("complete", help="Mark a checkpoint complete from fresh evidence")
    complete.add_argument("checkpoint")
    complete.add_argument("--owner", required=True)
    complete.add_argument("--evidence", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    evidence_check: list[str] | None = None
    if raw_argv[:1] == ["evidence-run"] and "--" in raw_argv:
        delimiter = raw_argv.index("--")
        evidence_check = raw_argv[delimiter + 1 :]
        raw_argv = raw_argv[:delimiter]
    args = build_parser().parse_args(raw_argv)
    try:
        if args.command == "init":
            repo = Path(args.repo).resolve()
            worktree = Path(args.worktree).resolve() if args.worktree else repo
            identity = repository_identity(worktree)
            state = {
                "schema_version": SCHEMA_VERSION,
                "objective": args.objective,
                "acceptance_ids": sorted(set(args.acceptance_id)),
                "repository": str(repo),
                "worktree": identity["root"],
                "branch": run_git(Path(identity["root"]), "branch", "--show-current").stdout.decode().strip(),
                "session_id": args.session_id,
                "mission_id": args.mission_id,
                "model_policy": {
                    key: value
                    for key, value in {
                        "orchestrator": args.orchestrator_model,
                        "worker": args.worker_model,
                        "validator": args.validator_model,
                    }.items()
                    if value
                },
                "status": "ready",
                "controller": {"owner": None, "lease_expires_at": None},
                "active_workers": [],
                "requests": {},
                "recovery_attempts": {},
                "seen_event_ids": [],
                "events": [],
                "next_action": "acquire_lease",
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
            checkpoint = Path(args.checkpoint).resolve()
            if checkpoint.exists():
                raise SupervisorError(f"Checkpoint already exists: {checkpoint}")
            atomic_write_json(checkpoint, state)
            output = state
        elif args.command == "lease":
            output = acquire_lease(Path(args.checkpoint).resolve(), args.owner, args.ttl)
        elif args.command == "release":
            output = release_lease(Path(args.checkpoint).resolve(), args.owner)
        elif args.command == "event":
            event_data = json.loads(args.json)
            action_box: list[str] = []

            def record(state: dict[str, Any]) -> None:
                action_box.append(append_event(state, event_data))

            output = mutate_checkpoint(Path(args.checkpoint).resolve(), args.owner, record)
            output = {"action": action_box[0], "state": output}
        elif args.command == "replay":
            event_path = Path(args.events)
            actions: list[str] = []

            def replay_events(state: dict[str, Any]) -> None:
                for number, line in enumerate(event_path.read_text(encoding="utf-8").splitlines(), 1):
                    if line.strip():
                        try:
                            actions.append(append_event(state, json.loads(line)))
                        except json.JSONDecodeError as exc:
                            raise SupervisorError(f"Invalid event JSON on line {number}") from exc

            output = mutate_checkpoint(Path(args.checkpoint).resolve(), args.owner, replay_events)
            output = {"actions": actions, "state": output}
        elif args.command == "answer":
            output = record_answer(
                Path(args.checkpoint).resolve(), args.owner, args.request_id, args.answer, args.delivery
            )
        elif args.command == "run-turn":
            return run_turn(args)
        elif args.command == "status":
            output = read_json(Path(args.checkpoint).resolve())
        elif args.command == "evidence-init":
            output = new_evidence_manifest(
                Path(args.repo), args.required, args.require_scrutiny, args.require_user_testing
            )
            manifest = Path(args.manifest).resolve()
            if manifest.exists():
                raise SupervisorError(f"Manifest already exists: {manifest}")
            atomic_write_json(manifest, output)
        elif args.command == "evidence-record":
            category = "assertion" if args.assertion else "validator"
            output = evidence_record(
                Path(args.manifest).resolve(),
                category,
                args.assertion or args.validator,
                args.command,
                args.exit_code,
                [Path(item) for item in args.artifact],
            )
        elif args.command == "evidence-run":
            command = evidence_check or []
            if not command:
                raise SupervisorError("evidence-run requires a command after --")
            manifest_path = Path(args.manifest).resolve()
            manifest = read_json(manifest_path)
            artifact = Path(args.artifact).resolve()
            repository = Path(manifest["repository"]).resolve()
            if artifact.is_relative_to(repository):
                raise SupervisorError("Evidence artifacts must be outside the repository")
            artifact.parent.mkdir(parents=True, exist_ok=True)
            with artifact.open("w", encoding="utf-8", newline="\n") as stream:
                result = subprocess.run(
                    command,
                    cwd=repository,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    shell=False,
                    check=False,
                )
            category = "assertion" if args.assertion else "validator"
            output = evidence_record(
                manifest_path,
                category,
                args.assertion or args.validator,
                subprocess.list2cmdline(command),
                result.returncode,
                [artifact],
            )
        elif args.command == "evidence-verify":
            output = verify_evidence(read_json(Path(args.manifest).resolve()))
            print(json.dumps(output, indent=2))
            return 0 if output["complete"] else 1
        elif args.command == "complete":
            output = complete_checkpoint(
                Path(args.checkpoint).resolve(), args.owner, Path(args.evidence).resolve()
            )
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0 if output["complete"] else 1
        else:
            raise AssertionError(args.command)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (SupervisorError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
