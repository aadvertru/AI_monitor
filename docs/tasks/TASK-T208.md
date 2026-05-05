# TASK-T208 — Add Source Intelligence v2 Verification Checklist

## Goal

Create a manual QA checklist for Source Intelligence v2.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/SOURCE_INTELLIGENCE_V2_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
T-S01 — L1 audit shows no-source empty state
T-S02 — L2 audit shows domain source groups
T-S03 — Same domain with multiple URLs groups into one row
T-S04 — Domain row expands to URL evidence
T-S05 — Duplicate URLs deduplicated
T-S06 — OpenRouter L2 answer without citations shows safe empty state
T-S07 — Partial audit still shows available sources
T-S08 — Invalid/unsafe URLs do not crash UI
T-S09 — Source counts match API
T-S10 — Raw provider/tool payloads not exposed
T-S11 — Mobile sources view smoke test
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| T-S01 | Not run |  |  |
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

- `docs/SOURCE_INTELLIGENCE_V2_VERIFICATION.md` exists.
- Scenarios T-S01 through T-S11 included.
- Result table included.
- Captured issue template included.
- Checklist verifies domain grouping, expand behavior, empty states, safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix source bugs.
- Do not implement source aggregation/UI.
