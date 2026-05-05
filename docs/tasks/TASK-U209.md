# TASK-U209 — Add Concepts and Competitors Verification Checklist

## Goal

Create a manual QA checklist for Concepts vs Competitor Candidates.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/CONCEPTS_COMPETITORS_VERIFICATION.md
```

---

## Required scenarios

Use standard format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
U-S01 — Generic phrases appear as concepts
U-S02 — Generic phrases do not appear as competitors
U-S03 — Competitor candidate appears with comparison context
U-S04 — Known competitor list match if available
U-S05 — Competitor evidence is displayed/summarized
U-S06 — Empty concepts state
U-S07 — Empty competitors state
U-S08 — Legacy audit compatibility
U-S09 — Results Details labels are correct
U-S10 — Raw provider data not exposed
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| U-S01 | Not run |  |  |
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

- `docs/CONCEPTS_COMPETITORS_VERIFICATION.md` exists.
- Scenarios U-S01 through U-S10 included.
- Result table included.
- Captured issue template included.
- Checklist verifies semantic split.
- Checklist verifies UI labels.
- Checklist verifies safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix issues.
- Do not implement extraction/UI.
