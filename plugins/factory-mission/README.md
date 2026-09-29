# Factory Mission

This plugin packages the `factory-mission` Agent Skill. It creates or audits
validation-first Factory Mission briefs and carries authorized Missions through
verified completion: answering Factory questions, recovering blocked work, and
checking outcomes through the installed Droid CLI.

The shared skill body is under `skills/factory-mission/`. Mission operations
use the installed Droid CLI and follow the user's existing Factory
authentication and model configuration. The bundled supervisor helper provides
durable checkpoints, question deduplication, bounded recovery, and a
revision-bound completion evidence gate.

See the repository [README](https://github.com/danieleceschi/factory-mission-skill)
for installation, usage, validation, and safety guidance.
