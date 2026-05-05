# TASK-P205 — Add Profile / Account Shell Verification Checklist

## Goal

Create a manual QA checklist for the Profile / Account shell.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/PROFILE_ACCOUNT_VERIFICATION.md
```

---

## Required scenarios

Use this format for each scenario:

```markdown
## P-S01 — Scenario title

### Purpose
What this verifies.

### Preconditions
- User/auth state
- Backend/frontend state

### Steps
1. Step one
2. Step two

### Expected result
- Expected UI/API behavior

### Actual result
To be filled during verification.

### Status
Not run | Pass | Fail | Blocked | Partial

### Issue ID
Optional
```

Scenarios:

```text
P-S01 — Authenticated user can open profile
P-S02 — Unauthenticated user cannot open profile
P-S03 — Profile displays user identity
P-S04 — Demo plan and token usage render clearly
P-S05 — Notification preferences render
P-S06 — Editable preferences save/cancel works
P-S07 — Non-editable fields cannot be changed
P-S08 — Language preference works if i18n is available
P-S09 — Unsafe fields are not rendered
P-S10 — Mobile/profile layout smoke test
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| P-S01 | Not run |  |  |
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

Use:

```markdown
# Captured Issues

## ISSUE-P-001 — Short title

### Scenario
P-Sxx

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

- `docs/PROFILE_ACCOUNT_VERIFICATION.md` exists.
- All scenarios P-S01 through P-S10 are included.
- Result table exists.
- Captured issue template exists.
- Checklist states that profile plan/tokens are demo data.
- Checklist verifies no sensitive fields are exposed.
- No runtime code is changed.

---

## Non-goals

- Do not run the checklist in this task.
- Do not fix profile bugs.
- Do not implement profile UI/backend.
- Do not add billing.
