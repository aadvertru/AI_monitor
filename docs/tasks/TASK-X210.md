# TASK-X210 — Verify and Stabilize Exports

## Goal

Run the export verification checklist and fix only issues captured during verification.

This task closes Phase X.

---

## Required input

Read:

```text
docs/EXPORTS_CONTRACT.md
docs/EXPORTS_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
export data builder bugs
Excel generation bugs
DOCX generation bugs
download endpoint bugs
frontend download bugs
repeat audit bugs
auth/ownership bugs
file safety bugs
missing section bugs
```

Not allowed:

```text
PDF export
async export queue
billing/cost accounting
result aggregation redesign
parser/scoring changes
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
X-S01 through X-S14
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
file generation
file content sections
auth/ownership
partial/no-evaluation/no-source cases
no raw provider data
download UI
repeat audit config-only copy
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major export issues fixed or deferred with rationale.
- Excel export works.
- DOCX export works.
- Repeat audit action works if in scope.
- No raw provider data/secrets in exports.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not implement PDF.
- Do not implement export history.
- Do not add background export queue.
- Do not fix unrelated bugs.
