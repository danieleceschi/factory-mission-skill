# Supervisor and evidence tooling

Read this reference in Completion mode when Python is available. The helper
makes supervision state durable and evidence testable. It does not decide what
the user authorized, infer answers, or turn a brief-only request into a launch.

Resolve `../scripts/mission_supervisor.py` relative to this file. Keep the
checkpoint, JSONL log, evidence manifest, and evidence artifacts in a private
host-owned directory outside the target repository. This avoids worker edits
and prevents evidence files from changing the repository fingerprint.

## Start or attach

Initialize once with the exact repository or Mission worktree and stable
acceptance IDs:

```text
python scripts/mission_supervisor.py init <checkpoint.json> --repo <repo> --worktree <worktree> --objective <objective> --acceptance-id VAL-1 --session-id <session>
python scripts/mission_supervisor.py lease <checkpoint.json> --owner <unique-controller-id> --ttl 300
```

Add model flags to `init` only when the effective policy requires explicit
orchestrator, worker, or validator models. A lease prevents a second controller
from acting. `run-turn` renews its lease while Droid is active and refuses a
new turn if the checkpoint identifies a still-running process.

For a new or continued authorized turn:

```text
python scripts/mission_supervisor.py run-turn <checkpoint.json> --owner <controller> --prompt-file <prompt.md>
```

The helper invokes `droid exec --mission --auto high` without a shell, preserves
the checkpoint's session, worktree, and explicit models, streams output to a
JSONL log, and records the process and exit. A successful turn still requires
outcome inspection and evidence verification.

## Questions and events

Raw structured `droid.ask_user` and `droid.request_permission` requests retain
their request IDs. One-shot text questions still require the host agent to
inspect the result and normalize the observation:

```text
python scripts/mission_supervisor.py event <checkpoint.json> --owner <controller> --json <normalized-event-json>
python scripts/mission_supervisor.py answer <checkpoint.json> --owner <controller> --request-id <id> --answer <answer> --delivery prepared
```

Pass `--answers-request <id>` to `run-turn` when a prepared answer is submitted
as the continuation prompt. Mark it `delivered` only after Factory acknowledges
the answer or advances past the request. Delivered request IDs are not answered
again after recovery. Permission requests still require an authority review.

Supported normalized event types include `scope_selected`,
`model_policy_applied`, `worker_started`, `worker_completed`, `heartbeat`, `question`, `permission_request`,
`validation`, `failure`, `mission_reported_complete`, `stopped`, and
`host_continuity_unavailable`. Each event needs a stable `id` when available.
Replay a JSONL sequence with `replay`; duplicate event IDs are ignored and a
third identical failure becomes a blocker. Set `recoverable` to `false` on a
known terminal failure such as a required unavailable model.

## Bind evidence to the final repository state

Create a manifest with every required acceptance assertion and applicable
validators:

```text
python scripts/mission_supervisor.py evidence-init <evidence.json> --repo <worktree> --required VAL-1 --require-scrutiny
python scripts/mission_supervisor.py evidence-run <evidence.json> --assertion VAL-1 --artifact <outside-repo/test-output.txt> -- <test-command>
python scripts/mission_supervisor.py evidence-run <evidence.json> --validator scrutiny --artifact <outside-repo/scrutiny.txt> -- <review-command>
python scripts/mission_supervisor.py evidence-verify <evidence.json>
python scripts/mission_supervisor.py complete <checkpoint.json> --owner <controller> --evidence <evidence.json>
```

`evidence-run` executes the exact argument list without a shell, captures its
combined output, and records the exit code. Each record includes the Git commit,
a fingerprint of staged, unstaged, and untracked content, and artifact hashes.
Verification fails when a required check failed or is missing, an artifact
changed, or the final commit or dirty diff no longer matches. Rerun only the
evidence invalidated by an intentional final change.

`complete` also verifies that the manifest requires every acceptance ID in the
checkpoint. It leaves the Mission in `verifying` with a repair action when any
proof is missing or stale; only a fresh, complete manifest makes the checkpoint
terminally `complete`.

Use `evidence-record` only when another trusted runner already produced an exit
code and artifact. It requires at least one artifact and binds it to the current
repository state.

Release the lease when supervision stops:

```text
python scripts/mission_supervisor.py release <checkpoint.json> --owner <controller>
```

The helper is not a background service. If the host cannot remain active or
schedule a continuation, preserve the checkpoint and report that supervision
ended while Factory may still be running.
