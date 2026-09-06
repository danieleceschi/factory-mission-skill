# Factory Mission Skill

[![Validate](https://github.com/danieleceschi/factory-mission-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/danieleceschi/factory-mission-skill/actions/workflows/validate.yml)

**Turn an ambitious software goal into a plan that AI coding agents can
execute, verify, and recover—without giving up control.**

A focused coding task can fit in one agent session. Building an application,
modernizing a codebase, or coordinating a multi-part migration usually cannot.
Large projects need an agreed plan, clear checkpoints, continuous validation,
and a safe way to intervene when execution drifts.

Factory provides that orchestration through **Missions**. This open-source
Agent Skill makes Missions easier to plan and operate from Factory Droid,
Codex, or Claude Code. It helps you decide whether a Mission is appropriate,
turn a goal into a validation-first brief, audit the plan, and—only when you
explicitly ask—launch and steer the work through the Droid CLI.

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
- Keep launches and operational actions behind explicit user approval.
- Use the same Mission workflow from Factory Droid, Codex, or Claude Code.

## What it does

- Decides whether work belongs in a normal Droid session, one Mission, or a
  sequence of Missions.
- Creates and audits validation-first Mission briefs with traceable assertions,
  worker-sized features, milestone exits, harness instructions, and stop rules.
- Launches, monitors, resumes, and steers Missions through the installed Droid
  CLI—but only after an explicit operational request.
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

The skill can produce or audit that brief without launching anything. When the
plan is ready, a separate explicit request such as “Launch this approved
Mission” authorizes the operational workflow.

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
- “Launch this approved Factory Mission in `C:\path\to\repo`.”
- “Monitor the Factory Mission you started and intervene if it blocks.”

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

This project is currently maintainer-led and open to contributors. Bug reports,
compatibility findings, documentation improvements, and tested workflow changes
are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development and
review process.

## License

MIT. See [LICENSE](LICENSE).
