# TASK-P201 — Define Profile / Account Shell Contract

## Goal

Define the product and API contract for the user Profile / Account shell.

This phase uses mostly fake/demo account data, but the contract must be clean enough to support future real billing, usage accounting, preferences, and notifications.

This task is documentation/contract only. Do not change runtime code.

---

## Context

The product currently has authenticated users and protected app routes. The next step is to add a user-facing account/profile area.

The first version should show:

- user name
- email
- current plan
- remaining tokens/usage
- notification settings
- language/preference settings if i18n is available
- basic editable account fields

The plan/tokens data is fake/demo for now. It must not imply real billing or enforce real usage limits yet.

---

## Files to update/create

Preferred new file:

```text
docs/PROFILE_ACCOUNT_CONTRACT.md
```

If the project keeps product contracts elsewhere, update:

```text
docs/PRODUCT_SPEC.md
docs/FRONTEND_CONTEXT.md
docs/BACKEND_CONTEXT.md
docs/TASKS.md
```

---

## Required contract decisions

### 1. Identity source

Document:

```text
name/display_name and email come from authenticated user identity where available.
email should be read from /auth/me or equivalent authenticated user endpoint.
profile must require login.
```

### 2. Demo account data

Document that these are fake/demo fields in this phase:

```text
current plan
remaining tokens
token quota
billing status
notification preferences if not persisted yet
```

Recommended wording:

```text
Profile/account shell displays demo usage/billing data until real cost accounting and billing are implemented.
```

### 3. Suggested profile response shape

Define a DTO similar to:

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "Ivan"
  },
  "plan": {
    "name": "Starter",
    "status": "demo",
    "is_demo": true
  },
  "usage": {
    "tokens_remaining": 10000,
    "tokens_total": 10000,
    "reset_at": null,
    "is_demo": true
  },
  "preferences": {
    "locale": "ru",
    "email_notifications": true,
    "audit_completed_notifications": true,
    "provider_error_notifications": false
  }
}
```

Use existing naming conventions if different.

### 4. Suggested endpoints

Document one of these approaches.

Preferred backend-backed contract:

```http
GET /profile
PUT /profile/preferences
PUT /profile/display-name
```

Acceptable MVP alternative:

```text
Profile page uses /auth/me for identity and local frontend mock data for plan/usage/preferences.
```

Recommendation: use backend-backed DTO if implementation cost is low, because it gives frontend a stable contract.

### 5. Editing rules

Document:

```text
display_name can be edited if supported by current user model
email is displayed but not editable in this phase
plan cannot be changed
tokens cannot be changed
notification settings may be edited as demo/mock preferences
language preference may be edited if i18n is implemented
```

### 6. Non-billing guarantee

Document:

```text
Do not implement real billing.
Do not enforce real token limits.
Do not charge users.
Do not expose payment controls.
```

### 7. i18n readiness

Document:

```text
Profile labels must use the i18n mechanism when available.
The contract must support future locales beyond en/ru.
Backend returns stable codes/values; frontend translates labels.
```

---

## Acceptance criteria

- Profile/account shell contract is documented.
- Fake/demo billing/usage scope is explicit.
- Identity fields are tied to authenticated user data.
- Plan/tokens are marked as demo data.
- Notification preferences are defined.
- Editable vs non-editable fields are defined.
- API approach is selected or explicitly deferred to frontend mock.
- No runtime code is changed.

---

## Non-goals

- Do not implement profile backend.
- Do not implement profile UI.
- Do not implement real billing.
- Do not implement real token accounting.
- Do not integrate payment providers.
- Do not change auth flow.
- Do not add i18n runtime code.
