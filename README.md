# Factory Mission Skill

A portable Agent Skill for planning and operating
[Factory Missions](https://docs.factory.ai/missions/overview) from Factory
Droid, Codex, or Claude Code.

## What it does

- Decides whether work belongs in a normal Droid session, one Mission, or a
  sequence of Missions.
- Creates and audits validation-first Mission briefs with traceable assertions,
  worker-sized features, milestone exits, harness instructions, and stop rules.
- Launches, monitors, resumes, and steers Missions through the installed Droid
  CLI—but only after an explicit operational request.
- Includes a standard-library structural linter and behavioral eval fixtures.

The skill never treats a request for a prompt as permission to start work. It
does not add an MCP server, embed credentials, or hardcode a maintainer's model.

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

## Personal model policy

Keep machine-specific model preferences in Factory's user-local settings, not
in this public package. For example, `%USERPROFILE%\.factory\settings.local.json`
on Windows or `~/.factory/settings.local.json` elsewhere can contain:

```json
{
  "sessionDefaultSettings": {
    "model": "auto"
  },
  "missionOrchestratorModel": "auto",
  "missionModelSettings": {
    "workerModel": "auto",
    "validationWorkerModel": "auto"
  },
  "modelFallbacks": {
    "auto": "<your-fallback-model-id>"
  }
}
```

The operator omits model flags by default so Factory resolves these settings.
This also supports Droid versions that accept Auto in settings but reject
`--model auto` on the command line.

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

## License

MIT. See [LICENSE](LICENSE).
