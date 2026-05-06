# Profile / Account Contract

## Scope

The Profile / Account shell is an authenticated user area for account identity,
demo plan/usage information, and simple preferences.

This phase does not implement billing, real token accounting, payment controls,
password changes, email changes, or real notification delivery.

## Authentication

Profile endpoints and UI require an authenticated user session.

Identity fields come from the authenticated user record:

- `id`
- `email`
- `display_name` if supported by the user model

Email is read from the authenticated identity and is not editable in this phase.
Display name is read-only in the MVP and may be `null` when the current user
model does not support it.

## Demo Plan And Usage

Profile/account shell displays demo usage and billing data until real cost
accounting and billing are implemented.

The following fields are demo-only:

- current plan
- plan status
- remaining tokens
- token quota
- usage reset date
- billing status

Demo plan and usage fields must be clearly marked with `is_demo: true` in API
responses. The UI must not imply that billing is active or that token limits are
being enforced.

## API

The MVP uses a backend-backed profile contract.

```http
GET /profile
PUT /profile/preferences
```

Both endpoints require authentication.

`GET /profile` returns the authenticated user's identity plus demo plan, demo
usage, and persisted preferences.

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "display_name": null
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
    "locale": "en",
    "email_notifications": true,
    "audit_completed_notifications": true,
    "provider_error_notifications": false
  }
}
```

`PUT /profile/preferences` accepts preferences only:

```json
{
  "locale": "ru",
  "email_notifications": true,
  "audit_completed_notifications": true,
  "provider_error_notifications": false
}
```

The preferences endpoint must not accept or update:

- email
- display name
- plan
- usage
- token counts
- billing status

Unknown fields should be rejected by request validation.

## Preferences

Profile preferences are backend-backed in this phase.

Supported preferences:

- `locale`
- `email_notifications`
- `audit_completed_notifications`
- `provider_error_notifications`

Locale must be validated against the frontend-supported locale set when that
configuration is available to the backend. Backend responses return stable
locale codes. The frontend translates labels.

Notification preferences are stored as user preferences only. They do not send
real email or provider-error notifications yet.

## Editing Rules

Editable in this phase:

- locale preference
- email notification toggle
- audit completed notification toggle
- provider error notification toggle

Read-only in this phase:

- email
- display name
- plan
- token quota
- remaining tokens
- billing status

Display-name editing is deferred.

## i18n

Profile UI labels must use the existing i18n mechanism.

Backend returns stable codes and values. The frontend is responsible for
localized labels. The contract must remain extensible beyond English and
Russian.

Raw user values are not translated:

- email
- display name
- plan code/name returned by backend unless explicitly mapped by frontend

## Safety

Profile API and UI must never expose:

- password hashes
- JWT values
- auth tokens
- API keys
- provider keys
- billing secrets
- raw environment settings
- raw internal configuration dumps

## Non-Billing Guarantee

Do not implement real billing.

Do not enforce real token limits.

Do not charge users.

Do not expose payment controls.
