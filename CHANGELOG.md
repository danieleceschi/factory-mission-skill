# Changelog

## 1.2.0 - 2026-09-30

- Add a crash-safe Mission supervisor with controller leases, session-aware
  Droid execution, question deduplication, bounded recovery, and resumable
  checkpoints.
- Bind completion to an executable evidence manifest covering every acceptance
  assertion, required validator, final commit, dirty diff, and output artifact.
- Convert all 23 behavioral scenarios into deterministic controller replays.
- Add drift-safe public-to-private synchronization with external overlays,
  atomic replacement, dry runs, backups, and first-sync adoption controls.

## 1.1.0 - 2026-09-13

- Add completion mode for run, launch, resume, and takeover requests, including
  routine question resolution, targeted recovery, and final evidence checks.
- Preserve brief-only, read-only monitoring, and explicitly bounded operations.
- Add session identity, question delivery, single-controller, checkpoint, and
  honest host-continuation guidance; retain model and external-action limits.
- Extend behavioral eval scenarios for questions, recovery, false completion,
  resumption, stop requests, and permission boundaries.
- Refresh CLI and Mission references against current docs and Droid 0.198.0.

- Clarify the public positioning for newcomers and remove private,
  machine-specific model configuration from the README.
- Add contribution guidance and explain how changes are reviewed.
- Replace “portable” positioning with explicit support for Droid, Codex, and
  Claude Code.

## 1.0.0 - 2026-09-05

- Add Mission-fit classification and validation-first brief authoring.
- Add structural Mission-brief linting with fixtures and tests.
- Add explicit-authority CLI launch, monitoring, resumption, and steering guidance.
- Add Factory, Codex, and Claude Code plugin metadata.
