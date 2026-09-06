# Mission operation through Droid CLI

Use this reference only when the user explicitly asks to launch, run, monitor,
wait for, resume, pause, or steer a Factory Mission.

## Authority model

- Writing or auditing a brief is not launch authority.
- Launch authority covers starting the described Mission in the named target;
  it does not imply permission to push, merge, deploy, purchase, delete data,
  contact people, or modify production unless separately requested.
- Monitoring authority is read-only. Steering authority covers only the stated
  intervention. Pausing or terminating requires an explicit request unless an
  immediate stop is necessary to prevent an unrequested or destructive action.

## Preflight

1. Resolve the exact working directory and confirm it is the intended target.
2. Read applicable repository instructions and inspect `git status --short`
   when the target is a Git repository. Preserve unrelated changes.
3. Confirm Droid exists with `droid --version` and supports Missions with
   `droid exec --help`.
4. Validate the effective model and tool configuration without creating a
   session:

   ```text
   droid exec --mission --auto high --list-tools --output-format json
   ```

5. Confirm any required services, credentials, network access, resource limits,
   and validation commands. Do not print secret values.
6. Run the brief linter and semantic review when launching from a structured
   brief. Surface material defects before launch.

If the target is dirty, report the relevant paths and assess overlap. Do not
stash, reset, clean, move, or overwrite existing work automatically.

## Model resolution

Respect Factory's resolved user, project, and runtime settings unless the user
explicitly overrides them. Factory Missions have separate orchestrator, worker,
and validator model settings, so verify all three inherit or match the intended
policy.

When Auto Model is configured, prefer omitting model flags and let Factory
resolve the settings and `modelFallbacks`. This is more reliable than passing
`--model auto`, which some Droid CLI versions reject even when the Auto setting
is valid. If preflight reports an unavailable model:

1. Inspect the available model IDs reported by Droid.
2. Use the configured fallback chain when present.
3. If no configured fallback is valid, stop and ask for a model choice.

Never invent or silently substitute a fallback. Do not copy personal custom
model IDs into a public brief or skill.

## Launch

Prefer a file for a long approved brief so shell quoting and command-length
limits cannot corrupt it:

```text
droid exec --mission --auto high --cwd "<absolute-repository-path>" --file "<absolute-brief-path>"
```

For a short objective:

```text
droid exec --mission --auto high --cwd "<absolute-repository-path>" "<objective>"
```

Use the host's normal long-running process mechanism. Keep the process handle,
Factory session ID, working directory, and redacted output together. Do not
detach silently. If durable background execution is requested, use an explicit
log file and a hidden/non-interactive process on Windows.

`--skip-permissions-unsafe` is not a convenience flag. Use it only when the
user explicitly requests it and the environment is verified as disposable or
isolated.

## Monitor and communicate

- Stream or poll the retained process at reasonable intervals; do not busy
  poll.
- Give the user a concise progress update at least every 60 seconds while work
  is active, emphasizing completed milestones, current worker, blockers, and
  decisions.
- Treat unchanged output as expected. Do not restart a healthy Mission merely
  because it is quiet.
- Inspect logs and repository state before declaring the Mission stuck.
- Preserve worker handoffs, validation failures, and adverse findings. Do not
  dismiss them merely to advance the run.

## Resume or steer

Use the saved Factory session ID for a scoped follow-up:

```text
droid exec --session-id <session-id> "<instruction>"
```

Use `droid --resume <session-id>` only when an interactive Mission Control
session is appropriate. State the observed problem and desired outcome in the
steering instruction; avoid prescribing implementation details unless they are
required constraints.

Before retrying a failed step, determine whether the cause changed. Do not loop
the same failing action indefinitely. A repeated blocker that requires user
input should be reported with evidence and a concrete decision request.

## Stop conditions

Pause and report when:

- the Mission requests authority outside the user's scope;
- the resolved repository is wrong or existing work is at risk;
- required credentials, services, or validation paths are unavailable;
- the chosen model and configured fallbacks are unavailable;
- resource, cost, time, or concurrency limits are reached;
- validation reveals that continuing would make the evidence less reliable;
- the user asks to pause or stop.

Terminate only the positively identified Mission process. Never kill unrelated
Droid sessions or broad process groups.

## Operation receipt

Report:

- action taken and exact target;
- Factory session ID and local process handle when available;
- effective model policy and whether fallback occurred;
- current feature or milestone state;
- validation evidence and repository status;
- any pending user decision or next intervention point.
