# TASK-P206 — Verify and Stabilize Profile / Account Shell

## Goal

Run the profile verification checklist and fix only issues captured during verification.

This task closes Phase P.

---

## Required input

Read:

```text
docs/PROFILE_ACCOUNT_VERIFICATION.md
docs/PROFILE_ACCOUNT_CONTRACT.md
```

Use captured issues from the verification document.

---

## Scope

Allowed fixes:

```text
profile route protection
profile API/client bugs
profile loading/error state bugs
demo plan/token rendering bugs
notification preference form bugs
language preference bugs
unsafe field rendering bugs
mobile layout blockers
```

Not allowed:

```text
real billing
real token accounting
payment integration
auth redesign
password/email change
real notification delivery
unrelated frontend/backend fixes
```

---

## Verification expectations

Run all scenarios:

```text
P-S01 through P-S10
```

Mark each:

```text
Pass
Fail
Blocked
Partial
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests for actual issues.

Likely tests:

```text
protected route behavior
profile response rendering
demo plan/token rendering
preferences save/cancel
unsafe field not rendered
mobile critical controls accessible if testable
```

---

## Acceptance criteria

- Profile verification document updated with final results.
- Blocker/major profile issues fixed or explicitly deferred with rationale.
- Profile route works for authenticated users.
- Unauthenticated users are blocked.
- Demo plan/token usage renders clearly.
- Editable preferences work if implemented.
- Sensitive fields are not exposed.
- Task-scoped tests pass.
- TypeScript/backend checks for touched files pass.

---

## Non-goals

- Do not implement real billing.
- Do not implement real token accounting.
- Do not add payment provider integration.
- Do not fix unrelated bugs.
