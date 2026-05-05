# TASK-P202 — Add Backend Profile DTOs and Demo Profile API

## Status

Ready for implementation.

## Goal

Add authenticated backend DTOs/endpoints for the Profile / Account shell.

This endpoint returns real identity fields and demo/mock plan/usage/preferences.

No real billing, token accounting, or payment behavior is implemented.

## Dependencies

Requires:

```text
TASK-P201
auth /auth/me or equivalent existing user identity
```

## MVP decision

Use backend-backed profile DTO with concrete endpoints:

```http
GET /profile
PUT /profile/preferences
```

Do not implement display-name editing in this task.

Display name is read-only in MVP:

```text
use existing user display_name if present
otherwise derive safe default or return null
```

## Scope

Implement:

```text
profile DTOs
GET /profile
PUT /profile/preferences
demo plan/usage values
preferences persistence or deterministic user-scoped storage
task-scoped backend tests
```

## Response shape

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

## Preferences endpoint

`PUT /profile/preferences` accepts only:

```json
{
  "locale": "ru",
  "email_notifications": true,
  "audit_completed_notifications": true,
  "provider_error_notifications": false
}
```

Rules:

```text
requires auth
updates preferences only
does not update email
does not update display_name
does not update plan
does not update token usage
invalid locale rejected if locale config exists, otherwise accepted as string only if project policy allows
```

Recommendation:

```text
validate locale against configured supported locales if i18n config is available
```

## Storage decision

Use one concrete behavior:

```text
persist preferences in user preferences field/table if available
otherwise add a small user_preferences JSON/columns according to project convention
```

Do not leave persistence as frontend-local for this backend task.

## Safety

Do not return:

```text
password hash
JWT secrets
internal auth tokens
API keys
provider keys
billing secrets
raw settings/env
```

## Tests

Backend tests:

```text
GET /profile unauthenticated rejected
GET /profile authenticated returns current user id/email
GET /profile returns demo plan/usage marked is_demo=true
GET /profile returns preferences
PUT /profile/preferences unauthenticated rejected
PUT /profile/preferences updates notification booleans
PUT /profile/preferences updates locale if valid
PUT /profile/preferences rejects invalid locale if locale validation exists
PUT /profile/preferences cannot change email
PUT /profile/preferences cannot change display_name
PUT /profile/preferences cannot change plan/tokens
sensitive fields absent
```

## Acceptance criteria

- `GET /profile` exists.
- `PUT /profile/preferences` exists.
- Auth required.
- Identity fields returned from current user.
- Plan/usage clearly demo.
- Preferences backend-backed.
- Email/display_name/plan/tokens not editable through preferences.
- No real billing/token accounting.
- Sensitive data not exposed.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- No safe place exists to persist preferences.
- Existing user model cannot be touched without broad auth migration.
- Product requires display_name editing in this phase.

## Commands

```bash
pytest <profile API tests>
ruff check <touched backend files>
```

## Done means

Authenticated profile endpoints work with concrete backend-backed preferences and demo plan/usage, without optional persistence branches.
