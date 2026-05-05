# TASK-Z211 — Verify and Stabilize Longitudinal Analytics

## Goal

Run the longitudinal analytics verification checklist and fix only issues captured during verification.

This task closes Phase Z.

---

## Required input

Read:

```text
docs/LONGITUDINAL_ANALYTICS_CONTRACT.md
docs/LONGITUDINAL_ANALYTICS_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
snapshot bugs
comparison endpoint bugs
trend endpoint bugs
source/concept/competitor diff bugs
frontend comparison UI bugs
trend chart/table bugs
missing-data handling bugs
legacy compatibility bugs
safety/no raw data bugs
```

Not allowed:

```text
new scoring methodology
new provider adapters
exports
background worker redesign
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
Z-S01 through Z-S12
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
snapshot creation
candidate filtering
comparison deltas
trend points
source/concept/competitor diffs
missing data safe
legacy audits safe
frontend rendering
no raw data exposed
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major longitudinal analytics issues fixed or deferred with rationale.
- Comparison works.
- Trends work.
- Missing data safe.
- Legacy audits safe.
- No raw provider data exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not change scoring methodology.
- Do not add unrelated analytics.
- Do not fix unrelated bugs.
