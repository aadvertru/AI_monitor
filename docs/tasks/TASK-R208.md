# TASK-R208 — Add Results v2 Verification Checklist

## Goal

Create a manual/API QA checklist for Results Data Contracts v2.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/RESULTS_V2_VERIFICATION.md
```

---

## Required scenarios

Use standard format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
R-S01 — Summary v2 empty audit
R-S02 — Summary v2 completed mock audit
R-S03 — Summary v2 partial audit
R-S04 — Matrix for single model L1
R-S05 — Matrix for same model L1+L2
R-S06 — Matrix for multi-model audit
R-S07 — Failed cell provider diagnostics
R-S08 — OpenRouter gateway metadata in matrix
R-S09 — Source-domain placeholder endpoint
R-S10 — Concepts/competitors placeholder fields
R-S11 — Legacy audit compatibility
R-S12 — Raw provider data is not exposed
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| R-S01 | Not run |  |  |
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

Include standard issue template:

```markdown
# Captured Issues

## ISSUE-R-001 — Short title

### Scenario
R-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Actual result
...

### Expected result
...

### Evidence
...

### Suggested next step
...
```

---

## Acceptance criteria

- `docs/RESULTS_V2_VERIFICATION.md` exists.
- Scenarios R-S01 through R-S12 included.
- Result table included.
- Captured issue template included.
- Checklist verifies summary, matrix, source placeholders, concepts/competitors placeholders, legacy compatibility, and safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix issues.
- Do not implement endpoints/UI.
