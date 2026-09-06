# Source references

Last reviewed: 2026-09-05.

Read this file when product behavior, packaging, or authoring rules need review.
Do not fetch every source during ordinary skill use.

## Factory

- [Factory Missions overview](https://docs.factory.ai/missions/overview) —
  mission fit, planning flow, feature scale, and prerequisites.
- [Planning and validation](https://docs.factory.ai/missions/planning) —
  milestone validation, QA harness guidance, and worker-run estimate.
- [Running in the CLI](https://docs.factory.ai/missions/running-cli) — Mission
  Control monitoring and intervention.
- [Interaction modes](https://docs.factory.ai/autonomy-and-safety/specification-mode)
  — Mission mode and autonomy separation.
- [Droid CLI reference](https://docs.factory.ai/droid-cli/cli-reference) —
  `droid exec --mission`, continuation, and model flags.
- [Droid settings](https://docs.factory.ai/droid-cli/settings) — orchestrator,
  worker, validator, and `modelFallbacks` settings.
- [Factory Router](https://docs.factory.ai/model-independence/factory-router) —
  Auto Model behavior.
- [Factory skills](https://docs.factory.ai/harness/skills) and
  [plugins](https://docs.factory.ai/harness/plugins) — discovery, packaging,
  precedence, and distribution.

## Agent Skill compatibility

- [Agent Skills specification](https://agentskills.io/specification)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [OpenAI skills catalog](https://github.com/openai/skills)

## Requirement quality

- [NASA Systems Engineering Handbook appendix](https://www.nasa.gov/reference/system-engineering-handbook-appendix/)
  — clear, singular, traceable, and verifiable requirements.

## Maintenance rule

Recheck the Factory CLI, Missions, settings, skill, and plugin references before
each minor release or at least quarterly. Update `source-reviewed`, fixtures,
and the changelog together. Avoid copying vendor documentation into the skill;
retain only the decisions that change behavior.
