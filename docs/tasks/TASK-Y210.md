# TASK-Y210 — Integrate Usage Summary with Profile Demo Tokens

## Goal

Integrate provider usage aggregation into the Profile/Account shell in a safe, non-billing way.

This should display usage information but must not implement real billing or token enforcement.

---

## Scope

Implement:

```text
usage summary endpoint or profile extension
profile usage display update
demo vs real usage distinction
task-scoped tests
```

---

## Rules

- If real usage data exists, display it separately from demo token quota.
- Do not decrement paid balance.
- Do not enforce billing limits.
- Clearly mark demo/estimated values.
- No provider secrets exposed.

---

## Suggested fields

```json
{
  "usage": {
    "tokens_remaining": 10000,
    "tokens_total": 10000,
    "is_demo": true,
    "actual_usage": {
      "total_tokens_used": 12345,
      "audit_count": 12,
      "last_updated_at": "..."
    }
  }
}
```

Adapt to project conventions.

---

## Tests

Backend/frontend tests:

```text
usage aggregation shown in profile
demo tokens still marked demo
actual usage values safe
no billing enforcement
missing usage safe
unsafe fields not exposed
```

---

## Acceptance criteria

- Profile can show actual usage summary if available.
- Demo token display remains clearly demo.
- No billing enforcement.
- No secrets exposed.
- Task-scoped tests pass.
- Touched-file typecheck/ruff passes.

---

## Non-goals

- Do not implement real billing.
- Do not implement payment.
- Do not enforce token limits.
