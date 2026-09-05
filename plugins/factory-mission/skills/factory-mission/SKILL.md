---
name: factory-mission
description: >-
  Create, audit, launch, monitor, resume, or steer Factory Missions. Use when
  the user asks for a Factory Mission brief or /missions plan, wants an
  existing Mission checked, or explicitly asks to operate a Mission through
  the installed Droid CLI. Creating or auditing a brief never authorizes
  launching it.
license: MIT
metadata:
  author: danieleceschi
  version: 1.0.0
  source-reviewed: 2026-09-05
---

# Factory Mission

Handle a Factory Mission as a lifecycle with two boundaries: planning produces
a reviewable brief, while operation requires an explicit user request to act.

## Route the request

- For a brief, prompt, plan, audit, or rewrite, use **Brief mode** and read
  [references/brief-authoring.md](references/brief-authoring.md).
- For an explicit request to launch, run, monitor, wait for, resume, pause, or
  steer a Mission, use **Operation mode** and read
  [references/operation.md](references/operation.md).
- If the user asks only how Missions work, answer without creating or running
  one.
- If the request mixes planning and launch, finish and show the brief first.
  Launch only when the same request clearly authorizes execution or after the
  user approves the resulting brief.

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
assumptions or blocking questions, and the worker-run floor estimate. For
Operation mode, return a concise receipt containing the target repository,
Factory session or process identifier when available, effective model policy,
current state, evidence collected, and the next intervention point.

Consult [references/sources.md](references/sources.md) only when reviewing or
updating this skill's product assumptions.
