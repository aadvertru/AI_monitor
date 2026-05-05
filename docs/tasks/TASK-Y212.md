# TASK-Y212 — Verify and Stabilize Execution, Usage, Cancel, and Retry

## Goal

Run the execution/usage verification checklist and fix only issues captured during verification.

This task closes Phase Y.

---

## Required input

Read:

```text
docs/EXECUTION_USAGE_CONTRACT.md
docs/EXECUTION_USAGE_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
usage aggregation bugs
run estimate bugs
background job bugs
progress API/UI bugs
cancel bugs
retry failed bugs
duplicate run bugs
status transition bugs
safe diagnostics bugs
profile usage display bugs
```

Not allowed:

```text
real billing
payment integration
new provider adapters
parser/scoring redesign
exports
longitudinal analytics
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
Y-S01 through Y-S12
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
estimate/caps
background enqueue/run
progress counts
cancel status
retry failed only
usage aggregation
no duplicate successful runs
no raw provider data
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major execution/usage issues fixed or deferred with rationale.
- Background execution works.
- Progress works.
- Cancel works.
- Retry failed works.
- Usage aggregation safe.
- No raw provider data exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not implement billing.
- Do not implement payment.
- Do not add unrelated features.
