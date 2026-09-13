---
name: factory-mission
description: >-
  Create or audit Factory Mission briefs, and run authorized Missions through
  verified completion: answer Factory questions, unblock workers, resume work,
  and validate outcomes. Use for Factory Mission prompts, /missions plans,
  execution, takeover, or monitoring. A brief-only request never launches work;
  monitoring alone is read-only.
license: MIT
metadata:
  author: danieleceschi
  version: 1.1.0
  source-reviewed: 2026-09-13
---

# Factory Mission

Own the requested Mission lifecycle. A planning request ends with a usable
brief. A request to run a Mission ends with verified completion or a concrete
blocker that cannot be resolved within the user's authority and constraints.

## Route the request

- For a brief, prompt, plan, audit, or rewrite, use **Brief mode** and read
  [references/brief-authoring.md](references/brief-authoring.md).
- For a request to launch, run, finish, take over, resume, or bring a Mission to
  completion, use **Completion mode** and read
  [references/operation.md](references/operation.md).
- For status, monitoring, a pause, or one specific intervention, use **Scoped
  operation mode** in the same reference. Respect the narrower request.
- If the user asks only how Missions work, answer without creating or running
  one.
- If the request includes planning and execution, prepare and summarize the
  brief, then proceed under that existing authority. Do not insert another
  approval round for ordinary planning choices. Brief-only wording such as
  "write a prompt that runs to completion" still selects Brief mode.

## Shared workflow

1. Ground the request in the user's goal, supplied artifacts, repository
   instructions, current working tree, and capabilities that actually exist.
2. Decide whether the work belongs in a normal Droid session, one Mission, a
   sequence of Missions, or is blocked by a decision that materially changes
   scope or safety.
3. Preserve explicit non-goals, constraints, budgets, model policy, and
   external-action boundaries. Do not turn a preference or example into
   permission for a broader action.
4. Make validation observable and falsifiable before decomposing work.
5. Validate the produced brief or the operation's preconditions in proportion
   to risk, then report the result and remaining decisions plainly.

In Completion mode, keep observing, deciding, responding, and verifying after
launch. Resolve routine Factory questions from the user's instructions, the
approved brief, repository evidence, and reasonable reversible choices. Ask
the user only for a material decision or permission that cannot be inferred.
A launched process, an answered question, a completed agent turn, or Factory's
success message alone is not Mission completion.

## Non-negotiable boundaries

- Never launch merely because a Mission brief was requested or created.
- Never use `--skip-permissions-unsafe` unless the user explicitly requests it
  and the environment is positively verified as disposable or isolated.
- Mission launch normally requires `--auto high`; that autonomy level does not
  authorize unrequested pushes, merges, deployments, data deletion, purchases,
  messages, or production changes.
- Resolve the exact repository path before launch. Preserve existing work; do
  not reset, clean, stash, move, or overwrite it without explicit authority.
- Respect Factory's user and project model settings. Do not hardcode a personal
  model ID in a public brief or silently replace an unavailable model.
- Never print credentials or copy secret-bearing Factory configuration into a
  brief, log, artifact, or repository.
- Treat generated Markdown as an authoring contract, not a claim of formal
  Factory runtime validation.

## Completion

For Brief mode, return the recommended execution shape, the paste-ready brief,
assumptions or blocking questions, and the worker-run floor estimate.

For Completion mode, stay engaged until the accepted outcome is verified, the
user stops the work, or a genuine blocker needs user input or an external
change. Return the outcome, validation evidence, repository/worktree and
session identifiers, decisions made for the user, and any unresolved blocker.
For Scoped operation mode, report the requested observation or intervention
and the Mission's actual state. See the operation reference for persistence,
question handling, recovery, and the completion gate.

Consult [references/sources.md](references/sources.md) only when reviewing or
updating this skill's product assumptions.
