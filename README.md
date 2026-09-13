# Factory Mission Skill

[![Validate](https://github.com/danieleceschi/factory-mission-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/danieleceschi/factory-mission-skill/actions/workflows/validate.yml)

**Plan a Factory Mission, then have your agent carry it through verified
completion and resolve Factory questions along the way.**

A focused coding task can fit in one agent session. Building an application,
modernizing a codebase, or coordinating a multi-part migration usually cannot.
Large projects need an agreed plan, clear checkpoints, continuous validation,
and a safe way to intervene when execution drifts.

Factory provides that orchestration through **Missions**. This open-source
Agent Skill makes Missions easier to plan and operate from Factory Droid,
Codex, or Claude Code. It helps you decide whether a Mission is appropriate,
turn a goal into a validation-first brief, audit the plan, and, when you ask to
run it, supervise the work through the Droid CLI until the outcome is verified
or a blocker requires your input.

> This is an unofficial open-source project, not an official Factory package.

## New to Factory?

[Factory](https://factory.ai/) is an AI software-development platform. Its
coding agent, **Droid**, can work with a repository from the Factory app or the
command line.

| Term | Plain-language meaning |
| --- | --- |
| **Factory** | The platform that provides Droid and the surrounding development workflow. |
| **Droid** | Factory's AI coding agent—the worker you collaborate with on software tasks. |
| **Factory Mission** | A structured, longer-running project organized into features, milestones, and validation checks. |
| **Mission Control** | The orchestration view that tracks execution and lets you monitor or redirect the work. |
| **Agent Skill** | A reusable set of instructions that teaches a compatible coding agent a specialized workflow. |

The basic flow is:

```text
your goal -> validated brief -> features and milestones -> orchestrated work -> evidence-backed completion
```

Unlike a one-shot prompt, a Mission is planned with Droid before execution.
Once you approve the plan, Factory coordinates the work, tracks progress, and
validates the result as it goes. See the official
[Factory Missions overview](https://docs.factory.ai/missions/overview) for the
product-level introduction.

## Why use this skill?

Long-running agent work often fails for predictable reasons: vague completion
criteria, oversized tasks, hidden dependencies, weak tests, or no recovery
plan. This skill addresses those problems before execution begins.

- Make “done” observable with traceable acceptance assertions.
- Break broad outcomes into worker-sized features and meaningful milestones.
- Plan validation early instead of treating testing as a final cleanup step.
- Answer routine Factory questions and recover workers within your instructions.
- Use the same Mission workflow from Factory Droid, Codex, or Claude Code.

## What it does

- Decides whether work belongs in a normal Droid session, one Mission, or a
  sequence of Missions.
- Creates and audits validation-first Mission briefs with traceable assertions,
  worker-sized features, milestone exits, harness instructions, and stop rules.
- Launches, monitors, answers Factory questions, resumes, and repairs authorized
  Missions through the installed Droid CLI until acceptance evidence is verified.
- Includes a standard-library structural linter and behavioral eval fixtures.

Planning and auditing are non-operational: asking for a brief or review never
launches a Mission. Operational actions use the installed Droid CLI and require
an explicit request.

## Example

Suppose you want to migrate a production API to a new framework while
preserving behavior. You can ask:

> Turn this migration goal into a Factory Mission brief. Define the behavior
> we must preserve, split the work into milestones, and specify how every
> milestone will be validated.

The skill can produce or audit that brief without launching anything. To hand
over execution, ask:

> Run this Mission to completion in the target repository. Resolve Factory's
> questions using the brief and repository conventions, unblock workers, and
> verify the final result.

You can also ask for planning and execution together. That request authorizes
routine planning decisions and continued supervision without another approval
round. The agent still brings you decisions that require new authority or
material product choices it cannot infer.

## Before you install

- For planning and brief audits, you need a compatible skill host such as
  Factory Droid, Codex, or Claude Code.
- To launch or operate a Mission, you also need the Factory Droid CLI installed,
  authenticated, and available on your `PATH`.
- Python is optional and is used only for the included deterministic brief
  linter and test suite.

When operating a Mission, the skill uses your installed Droid CLI and follows
your existing Factory authentication and model configuration.

## Install

### Factory Droid

```text
droid plugin marketplace add danieleceschi/factory-mission-skill
droid plugin install factory-mission@factory-mission-skill --scope user
```

### Codex

```text
codex plugin marketplace add danieleceschi/factory-mission-skill
codex plugin add factory-mission@factory-mission-skill
```

Start a new Codex task after installation so the skill is discovered.

### Claude Code

```text
claude plugin marketplace add danieleceschi/factory-mission-skill
claude plugin install factory-mission@factory-mission-skill
```

Restart Claude Code after installation.

## Use

Ask naturally or invoke `$factory-mission` where the host supports explicit
skill invocation:

- “Turn these five actions into a Factory Mission brief.”
- “Audit this Mission plan for weak validation.”
- “Run this Factory Mission to completion in `C:\path\to\repo`.”
- “Take over this existing Mission and resolve its pending questions.”
- “Monitor the Factory Mission you started and intervene if it blocks.”

## What completion mode does

1. Confirms the target, existing session, constraints, models, and validation.
2. Follows progress and answers routine questions using your instructions and
   repository evidence. It accepts compatible plans and repairs local blockers.
3. Continues the same session after handoffs or recoverable failures, retaining
   a checkpoint so context recovery does not duplicate work.
4. Checks the delivered artifacts and acceptance evidence before declaring done.
   A successful CLI exit or Factory's completion message alone is insufficient.

“Monitor and tell me when input is needed” remains read-only. “Launch only” or
“answer this one question” stays limited to that action. Asking for a prompt
that runs to completion still produces a prompt without launching it.

The skill runs inside your agent host; it does not install a standalone daemon.
It stays engaged during the task and uses a supported host continuation mechanism
when authorized and needed. If the host cannot continue unattended, it reports
that limit, the actual Factory state, and how to resume from the checkpoint.

## Validate a brief

Python is optional for skill use and required only for deterministic linting:

```text
python plugins/factory-mission/skills/factory-mission/scripts/validate_brief.py path/to/brief.md
```

The linter validates this repository's structural authoring contract. It does
not certify semantic quality or Factory runtime acceptance.

Run the package tests with:

```text
python -m unittest discover -s tests -v
```

## Safety boundary

Mission operations require an explicit action request and normally use
`--auto high`. That autonomy setting is not permission to push, merge, deploy,
delete data, purchase services, contact people, or touch production unless the
user separately requests those actions. The skill never uses
`--skip-permissions-unsafe` as a convenience.

## Contributing

Contributions are welcome, including bug reports, compatibility findings,
documentation improvements, and tested workflow changes. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the development and review process.

## License

MIT. See [LICENSE](LICENSE).
