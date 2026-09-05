# Brief authoring and audit

Use this reference when creating, reviewing, or rewriting a Factory Mission
brief. The brief is a planning seed for the Mission conversation, not a formal
Factory schema.

## 1. Classify before drafting

Choose one outcome and state it:

- **Normal session:** narrow, linear work that does not benefit from worker
  decomposition or milestone validation. Provide a normal Droid prompt instead.
- **One Mission:** bounded, multi-feature work with independently verifiable
  outcomes and a workable validation harness.
- **Mission portfolio:** open-ended or operationally continuous work, or a plan
  beyond Factory's rough 1–500-feature heuristic. Describe the portfolio and
  draft only the first bounded Mission.
- **Blocked:** a missing decision changes architecture, scope, safety, budget,
  or external effects. Ask no more than five concise blocking questions.

An explicit request for a Mission does not suppress useful pushback when a
normal session or portfolio is a better fit.

Classify the work as greenfield, prototype, brownfield, research, or mixed.
That classification determines the validation evidence.

## 2. Draft validation before features

Use this order:

1. Title: three to eight words.
2. Mission type.
3. Outcome: one compact paragraph describing the end state, not the activity.
4. Validation contract: normally 5–15 stable assertion IDs.
5. Non-goals.
6. Invariants.
7. Environment and harness.
8. Features derived from assertions.
9. Milestones with assertion-based exit criteria.
10. Capabilities and execution policy.
11. Stop conditions.

Use the bundled [mission brief template](../assets/mission-brief-template.md) as
a starting point when useful.

## 3. Write strong assertions

Use IDs such as `VAL-AUTH-01`. Keep IDs stable when revising wording.

Each assertion must contain:

- **Behavior:** a singular, externally observable truth.
- **Check:** a command, interaction, query, inspection, or independent review
  capable of falsifying the behavior.
- **Evidence:** the exact artifact or observation that proves the check ran and
  what it showed.

Prefer this form:

```markdown
- **VAL-AUTH-01 — Expired sessions are rejected.** Behavior: An expired session
  cannot access a protected route. Check: Run the named integration test and an
  HTTP request against the local service. Evidence: Test output and a redacted
  response showing the expected status code.
```

Reject assertions that merely say code exists, a task ran, or a screen was
opened. A check must be able to fail. Evidence must prove behavior rather than
effort.

## 4. Derive features and milestones

- Size each feature for one fresh worker context and give it a stable ID such
  as `F1`.
- Make every feature claim one or more valid assertion IDs.
- Cover every assertion with a feature, unless it is explicitly identified as
  milestone-only and checked by a validator.
- Use two to five milestones by default. Never exceed seven without explaining
  why.
- Give every milestone an `Exit:` clause referencing assertion IDs.
- Order foundations and validation harnesses before dependent product work.
- Estimate the initial worker-run floor as:

  `features + 2 × milestones`

Call this a floor, not a budget or promise.

## 5. Apply mode-specific evidence

### Brownfield

State the behavior that must remain unchanged, capture a baseline before edits,
and require regression evidence. Do not assume a green test suite covers all
existing behavior.

### Greenfield or prototype

Require functional evidence through the real interface or a representative
scriptable harness. Avoid treating compilation or screenshots alone as proof.

### Research or documentation

Use source-coverage, provenance, contradiction, reproducibility, and claim-to-
evidence checks. Skip user-style testing when no product surface exists, but
retain independent scrutiny unless a named alternative is stronger.

### Mixed research and build

Separate outcome-blind research or specification freezing from implementation
and evaluation. Define the gate that permits transition between phases.

## 6. Ground the environment

Inspect the repository before naming commands, services, ports, scripts,
skills, MCP servers, or custom droids. Unknown capabilities remain unknown.
State how to:

- set up dependencies;
- start and stop relevant services;
- drive the product or research workflow;
- capture redacted logs and evidence;
- reset state safely;
- enforce resource and concurrency limits;
- source secrets without persisting them;
- preserve unrelated work and external systems.

Never invent a plausible command. If a missing command makes validation
impossible, surface it as a blocker or create a feature to build the harness.

## 7. Validate before returning

Run the standard-library validator when Python is available:

```text
python scripts/validate_brief.py path/to/brief.md
```

Resolve `scripts/validate_brief.py` relative to this skill directory. If Python
is unavailable, apply the same checks manually.

Then perform semantic review:

- mission classification is justified;
- assertions are observable, singular, and falsifiable;
- checks and evidence genuinely prove each assertion;
- features fit fresh worker contexts;
- milestone exits can detect integration drift;
- safety and external-action boundaries are explicit;
- repository facts and capability names are grounded;
- no unresolved assumption is presented as fact.

Revise critical failures before returning. The linter validates this package's
authoring contract only; it cannot certify semantic quality or Factory runtime
acceptance.

## 8. Output

Return:

1. A one-line classification and recommendation.
2. One paste-ready Markdown brief, normally no more than 900 words.
3. Assumptions and no more than five blocking questions, only when needed.
4. The worker-run floor estimate for a single Mission.

Do not launch the Mission in Brief mode.
