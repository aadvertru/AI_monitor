# TASK-V211 — Verify and Stabilize Web5 Summary UI

## Goal

Run the Web5 summary verification checklist and fix only issues captured during verification.

This task closes Phase V.

---

## Required input

Read:

```text
docs/WEB5_SUMMARY_UI_CONTRACT.md
docs/WEB5_SUMMARY_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
summary data hook bugs
summary card bugs
model summary bugs
rerun fact-checking action bugs
action placeholder bugs
partial/failed state bugs
i18n label bugs
responsive layout bugs
provider diagnostic rendering bugs
safety/no raw data bugs
```

Not allowed:

```text
answer matrix UI
export backend implementation
evaluation backend changes
parser/scoring changes
source aggregation
competitor extraction
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
V-S01 through V-S14
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
summary card rendering
model summary rendering
null accuracy handling
rerun action
provider diagnostics
responsive/accessibility states
i18n labels
no raw provider data
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major Web5 issues fixed or deferred with rationale.
- Web5 summary page usable for completed/partial/failed audits.
- Metrics displayed from backend only.
- Rerun fact-checking works or is safely disabled.
- Export/repeat actions safe.
- No raw provider data exposed.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement Web6/Web7 matrix.
- Do not implement exports backend.
- Do not change backend metrics.
- Do not fix unrelated bugs.
