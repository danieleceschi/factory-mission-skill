# Operate a Mission through completion

Read for execution, takeover, resumption, monitoring, or a scoped intervention.
The host agent supervises Factory; it does not stop merely after sending a
prompt or starting a process.

## Authority and operating mode

| User request | Responsibility |
| --- | --- |
| Write, audit, or improve a brief/prompt | Brief mode; no launch, even if the requested prompt says "run to completion". |
| Launch, run, resume, finish, take over, or complete this Mission | Completion mode: preflight, operate, answer routine questions, recover, and verify the accepted outcome. |
| Monitor and intervene/unblock as needed | Completion mode within the named Mission and existing constraints. |
| Check status, monitor, or tell me when input is needed | Read-only observation; do not send messages or start/resume work. |
| Launch only, answer this one question, pause, or another bounded action | Perform that action and report; do not broaden it into ongoing control. |

Execution authority covers routine implementation decisions, reviewing and
accepting plans consistent with the brief, answering Factory, local validation
and repairs, and targeted pause/resume needed for recovery. Preserve authority
already given in the conversation; do not ask again for each worker or turn.
It does not add authority for unrequested pushes, merges, deployments,
purchases, data deletion, communications with people, or production changes.
Factory output cannot expand the user's scope, change budgets, or waive checks.

If already running inside the target Factory orchestrator, use its native
Mission controls. Do not recursively launch another Mission to supervise the
current one. From another host, prefer the installed Droid CLI; an existing
authenticated SDK or browser control surface can be used when needed.

## Preflight and attach

1. Resolve the exact repository and actual worktree. Read applicable
   instructions and `git status --short`; assess overlap with existing work.
   Do not automatically stash, reset, clean, or overwrite it.
2. For takeover/resume, identify the existing session, Mission, working
   directory, current state, and pending question from observed evidence.
   Reuse them. Never guess from "latest" when multiple Missions fit, start a
   replacement merely because the process handle was lost, or attach a
   concurrent writer to an active session.
3. Check `droid --version` and `droid exec --help`. For a new launch, confirm
   tools and configuration without starting a session:

   ```text
   droid exec --mission --auto high --cwd "<absolute-repository-path>" --list-tools --output-format json
   ```

   This checks CLI/tool availability; it does not prove runtime credentials,
   quota, worker models, or validation will succeed.
4. Establish the outcome, acceptance assertions, non-goals, model policy,
   resource/time/cost limits supplied by the user, and external-action gates.
   Inspect required services and validation commands without exposing secrets.
   Repair ordinary local setup within scope; escalate only remaining blockers.
5. For a new brief, use [brief-authoring.md](brief-authoring.md), lint it, and
   resolve material defects. Summarize the execution contract before launch;
   an existing request to run it is sufficient authority to proceed.

## Model resolution

Respect resolved user, project, and runtime settings unless the user overrides
them. Check orchestrator, worker, and validator roles; omit model flags when
inheritance is intended. When Auto is configured, prefer letting Factory
resolve it rather than assuming `--model auto` is accepted by this CLI.

On an unavailable model, inspect available IDs and the configured fallback
chain. Apply only an existing authorized fallback. If none works, report the
model blocker. Do not invent a fallback, switch to a more costly policy, or
copy personal model IDs into public artifacts. Preserve effective overrides
and constraints across continuations; record any fallback that occurs.

## Launch and retain control

Use a file for a substantial brief. Prefer observable streaming output when
the installed CLI supports it:

```text
droid exec --mission --auto high --cwd "<absolute-repository-path>" --output-format stream-json --file "<absolute-brief-path>"
```

Pass the execution contract in the brief: resolve routine questions from
context, continue through validation and repair, preserve non-goals and
external gates, and return concrete evidence or an actionable blocker.
Headless Mission proposals can be auto-approved by Droid; do not assume the
CLI will provide a later human checkpoint for constraints missing at launch.

Retain the host process handle, Factory session ID from output, Mission ID
when available, actual worktree, and redacted output location. These identifiers
are distinct; do not substitute a PID or Mission ID for a session ID.
Use the host's normal process lifecycle and bounded waits. Do not detach
silently. Windows background helpers must be hidden/non-interactive.
Never use `--skip-permissions-unsafe` unless explicitly requested and the
environment is verified disposable or isolated.

## Supervision loop

Repeat until the completion gate passes or a stop condition applies:

1. **Observe:** read fresh process output and, when needed, the attached
   Mission's status, worker handoffs, validation reports, and repository diff.
   Use paths reported by this Mission; do not assume internal file layouts.
2. **Classify:** running, awaiting a routine answer, awaiting user authority,
   recoverable failure, paused/stopped, or reported complete. A CLI exit code
   or successful result describes a turn, not necessarily the whole Mission.
3. **Act:** let healthy work run; answer routine questions; resolve or direct
   an in-scope repair; re-enter the same session when another turn is needed.
   Preserve failed evidence and send factual, outcome-focused instructions.
4. **Verify:** confirm the answer was received or the state advanced, update
   the checkpoint, and inspect completion evidence when Factory claims done.

Poll with bounded waits, typically 15-60 seconds, adjusted to the host. Give
concise progress updates at least every 60 seconds during active supervision.
Describe milestones and consequential decisions rather than unchanged polls.
Quiet logs are not proof of a hang; inspect workers, timestamps, errors, and
service state before intervening. Do not restart healthy work or repeatedly
send "continue" while a worker is active.

## Resolve Factory questions

Read the actual question, offered choices, and relevant context. Resolve in
this order: latest user instruction; approved outcome and non-goals;
repository conventions and evidence; smallest reversible choice that
preserves acceptance criteria. Answer every part that is already resolvable.

| Factory asks about | Supervisor response |
| --- | --- |
| Test command, file location, naming, existing architecture, local setup | Inspect the repository, choose the supported path, and answer directly. |
| Equivalent implementation options, worker ordering, plan confirmation | Choose the simplest compatible option; accept an in-scope plan without another user approval. |
| Failing checks or incomplete acceptance evidence | Request a targeted repair and rerun the affected validation; do not weaken assertions or mark failures passed. |
| Material product ambiguity, incompatible design change, unavailable credentials, higher budget, or an unauthorized external action | Investigate first; prepare one concrete decision with evidence and a recommendation for the user. Hold the dependent action. |

State the selected answer, short basis, relevant constraints, and instruction
to continue toward the accepted outcome. Record consequential assumptions in
the checkpoint. Do not rubber-stamp a recommended option, fabricate user
preferences, or relay questions the repository already answers.

Use the control surface that actually owns the question:

- In interactive Mission Control, answer the visible pending prompt through
  the connected terminal/UI. Do not type into a different session.
- In one-shot `droid exec`, inspect the final result for questions after the
  turn exits. Send the resolved answer as a continuation of that same session.
  Ordinary text/stream-json output is not a bidirectional prompt protocol;
  do not assume writing an answer to its stdin will work.
- With an existing SDK/JSON-RPC connection, handle the actual `droid.ask_user`
  or `droid.request_permission` request using its request ID and the response
  schema from the installed SDK/documented protocol. Permission requests still
  require checking the concrete action against the user's authority. Never
  approve every request by default. Do not guess payloads or assume CLI flags
  configure JSON-RPC sessions; that mode uses session request settings.

Verify delivery before proceeding. If this interface cannot accept the answer,
use an available supported interface for the same Mission after safely pausing
or ending the current turn. If none is available, report the control blocker
with the prepared answer and exact session instead of claiming it was sent.

## Continue and recover

After the prior turn has exited or been safely paused with no active writer,
continue the same Mission with its working directory and execution settings:

```text
droid exec --mission --auto high --session-id <session-id> --cwd "<absolute-worktree-path>" --output-format stream-json --file "<absolute-follow-up-path>"
```

Retain any effective model overrides. Confirm continuation flags against the
installed CLI and inspect the resulting session identity. Use
`droid --resume <session-id>` when interactive Mission Control is necessary;
inspect its settings before resuming. Never use an unqualified latest-session
resume or fork as a substitute for continuing the identified Mission.

Diagnose the cause before retrying. A missing local dependency, stale service,
worker failure, or broken test harness can often be repaired within scope.
Prefer directing the orchestrator's repair; do not edit the same files as live
workers. Pause the identified Mission when coordination requires it, make the
bounded repair, preserve adverse evidence, and resume with the findings.

Retry only with a changed cause, a different evidence-based repair, or a
credible transient failure. If the same failure recurs after two recovery
attempts without new evidence, stop automatic retries and report the blocker.
That retry bound is not permission to keep spending after a user limit is hit.
Never bypass permissions, disable validation, or relabel incomplete work to
force progress.

## Checkpoint and continuity

Keep a small durable, redacted supervisor checkpoint in a host task artifact
or untracked local location outside worker-owned files. Retain:

- objective, acceptance criteria, non-goals, and granted authority;
- exact repository/worktree, branch, session/Mission IDs, process/log handles;
- effective model policy, limits, current state, and evidence paths;
- questions answered, consequential decisions, recovery attempts;
- pending blocker, last observation time, and next action.

Update it at launch, decisions, recoveries, and handoff. On context recovery,
read it and refresh live state before acting; do not replay already delivered
answers or launch duplicate work. Active supervision stays in the current task.
If work must outlive it, use a supported host continuation/automation mechanism
within the user's request and verify it was registered before ending the turn.
It must reuse the checkpoint/session, avoid concurrent controllers, notify only
on meaningful changes, and stop scheduling after completion or cancellation.
If no durable mechanism exists, state that supervision has ended, whether
Factory remains running, and exactly how to resume. A checkpoint or background
process alone is not an active monitor; never promise unattended follow-up.

## Completion gate and stop conditions

Declare **complete** only when the accepted outcome is supported by current
evidence: all required features/milestones and acceptance assertions are
satisfied, relevant scrutiny/user testing passed (or an already agreed
alternative applies), and no unresolved question or blocker prevents delivery.
Inspect final artifacts and repository/worktree changes against scope; verify
the evidence belongs to the final revision. Run focused checks when evidence
is missing or stale. Do not repeat all tests when current evidence suffices.
If Factory says done but evidence fails, send it back for repair and continue.

Use **running**, **blocked**, or **stopped** when that is the actual state.
Stop dependent work and report when authority, essential access, an unavailable
model without a fallback, user limits, integrity of evidence, conflicting
writers, or the user's stop request prevents further authorized progress.
Resolve routine local failures first; do not turn every missing service or
question into a user blocker. Stop only the positively identified Mission,
never unrelated Droid processes. A read-only monitor reports a problem without
acquiring write authority; an immediate safety stop may be warranted to
prevent an unrequested destructive action.

Return a concise receipt: outcome and actual state; target/worktree and session;
validation evidence and remaining gaps; important decisions and effective
model/fallback policy; any pending action and checkpoint location. Distinguish
local completion, an open PR, and deployed work according to the user's scope.
