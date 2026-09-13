# Contributing

Thanks for helping improve Factory Mission Skill. Contributions are welcome
through GitHub issues and pull requests.

## Good contribution areas

- Reproducible Factory Droid CLI compatibility findings
- Improvements to Mission brief structure or validation
- Safer launch, monitoring, steering, and recovery guidance
- Tests and eval cases for real-world Mission workflows
- Clearer installation, examples, and troubleshooting documentation

## Before opening a pull request

For behavior or brief-contract changes, open an issue first so the intended
outcome and compatibility impact can be discussed. Small documentation fixes
can go directly to a pull request.

Do not include credentials, personal model identifiers, absolute machine paths,
private repository content, or generated session data.

## Development

The package tests use only Python's standard library:

```text
python -m unittest discover -s tests -v
```

To validate a Mission brief directly:

```text
python plugins/factory-mission/skills/factory-mission/scripts/validate_brief.py path/to/brief.md
```

Before submitting a change:

1. Run the complete test suite.
2. Add or update tests when behavior changes.
3. Keep the Factory, Codex, and Claude Code manifests aligned.
4. Preserve the explicit authorization boundary for operational actions.
5. Update the README or changelog when users need to know about the change.

## Behavioral evaluation

The package tests validate metadata and brief structure. They do not execute
Mission supervision. Scenarios in
`plugins/factory-mission/skills/factory-mission/evals/evals.json` separately
exercise routing, question handling, recovery, and completion decisions.

For workflow changes, give a fresh evaluator the skill plus each selected
scenario's `prompt` and `context` before showing its `expectations`. Simulate
session output offline unless a live run is explicitly authorized. Check the
actual decisions and report which cases ran; do not call all fixtures passed
merely because the JSON parsed or unit tests passed.

## Pull requests

Explain the problem, the chosen solution, and how you verified it. Keep pull
requests focused enough to review independently. Screenshots or command output
are useful when they demonstrate installation or host compatibility.

## How changes are handled

Changes are proposed and reviewed through issues and pull requests. Releases
are published after the relevant tests and package validators pass. Shared
review or release responsibilities can be documented if and when the project
needs them.
