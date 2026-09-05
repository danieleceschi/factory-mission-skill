# Reliable Session Expiry Upgrade

## Mission type

Brownfield service Mission. The work spans storage, request handling, migration,
and observable regression checks, so milestone validation is useful.

## Outcome

Users with valid sessions retain access while expired or revoked sessions are
rejected consistently, existing accounts migrate without data loss, and the
service remains reproducibly testable through the repository's documented
commands.

## Validation contract

- **VAL-AUTH-01 — Valid sessions retain access.** Behavior: A valid session can access the protected profile route. Check: Run the existing authenticated-route integration test. Evidence: Test output naming the protected route and successful response assertion.
- **VAL-AUTH-02 — Expired sessions are rejected.** Behavior: An expired session cannot access a protected route. Check: Run the expiry integration test and a local HTTP request. Evidence: Test output and a redacted response showing the expected unauthorized status.
- **VAL-AUTH-03 — Revoked sessions are rejected.** Behavior: A revoked session cannot be reused. Check: Revoke a fixture session and retry the protected request. Evidence: Redacted request transcript and persisted revocation record.
- **VAL-DATA-01 — Existing sessions migrate safely.** Behavior: Migration preserves valid records and marks unconvertible records without dropping them. Check: Run the migration against the versioned fixture database. Evidence: Before-and-after row counts and migration report.
- **VAL-REG-01 — Existing login behavior remains stable.** Behavior: Supported login and logout flows retain their documented responses. Check: Run the repository's authentication regression suite. Evidence: Named test results and coverage of login and logout paths.

## Non-goals

- No identity-provider replacement, production deployment, or unrelated user-interface redesign.

## Invariants

- Preserve public route contracts and existing user records. Never log session tokens.

## Environment and harness

Use the repository's documented dependency install, migration fixture, service
start command, and authentication test suite. Route redacted service logs to the
test artifact directory and restore only fixture state between runs.

## Features

1. **F1 — Implement expiry enforcement:** VAL-AUTH-01, VAL-AUTH-02.
2. **F2 — Implement revocation and migration:** VAL-AUTH-03, VAL-DATA-01.
3. **F3 — Preserve authentication behavior:** VAL-REG-01.

## Milestones

- **M1 — Storage and enforcement foundation.** Exit: VAL-AUTH-01, VAL-AUTH-02, VAL-AUTH-03, VAL-DATA-01.
- **M2 — Integrated regression validation.** Exit: VAL-REG-01.

## Capabilities and execution

Read repository instructions first. Work on a dedicated branch, use only
verified repository commands, commit milestone-sized changes, and do not push,
merge, or deploy without separate authorization.

## Stop conditions

- Pause if the fixture migration loses records, the documented harness cannot run, secrets appear in logs, or requested work requires a production change.
