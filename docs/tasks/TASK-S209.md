# TASK-S209 — Add Answer Evaluation Verification Checklist

## Goal

Create a manual/API QA checklist for answer evaluation and fact-checking foundation.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/ANSWER_EVALUATION_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
S-S01 — Brand facts created from brand fields
S-S02 — Evaluation records created for successful runs
S-S03 — Failed/no-answer runs skipped
S-S04 — Rerun evaluation updates existing evaluations
S-S05 — Raw answers remain unchanged after evaluation
S-S06 — Parser/scoring remain unchanged after evaluation
S-S07 — Matrix cells include verdict/rationale
S-S08 — Summary accuracy updates after evaluation
S-S09 — Unknown/missing evaluations handled safely
S-S10 — No raw evaluator/provider data exposed
S-S11 — Rerun fact-checking endpoint auth/ownership
S-S12 — i18n-ready verdict codes
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| S-S01 | Not run |  |  |
```

Allowed statuses:

```text
Not run
Pass
Fail
Blocked
Partial
```

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/ANSWER_EVALUATION_VERIFICATION.md` exists.
- Scenarios S-S01 through S-S12 included.
- Result table included.
- Captured issue template included.
- Checklist verifies parser/scoring separation.
- Checklist verifies no raw data leakage.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix issues.
- Do not implement evaluation.
