# TASK-P204 — Add Editable Profile Preferences Flow

## Status

Ready for implementation.

## Goal

Allow the user to edit profile preferences in the Profile / Account shell.

This remains a demo/simple preferences flow. It does not implement real billing, real notification delivery, email changes, or display-name editing.

## Dependencies

Requires:

```text
TASK-P202 — GET /profile and PUT /profile/preferences
TASK-P203 — Profile page UI
```

## Scope

Implement:

```text
notification preference toggles
locale preference if i18n exists
save/cancel behavior
safe success/error states
task-scoped frontend tests
```

## Editable fields

Allowed:

```text
email_notifications
audit_completed_notifications
provider_error_notifications
locale if i18n exists
```

Not editable:

```text
email
display_name
plan
tokens_remaining
tokens_total
billing status
```

Display name editing is explicitly deferred.

## Backend behavior

Use:

```http
PUT /profile/preferences
```

Payload must contain preferences only.

## Tests

Frontend tests:

```text
notification toggles change form state
save sends preferences-only payload
payload does not include email/display_name/plan/tokens
cancel resets form
loading state during save
safe error state on failed save
locale selector updates preference if i18n exists
email/display_name/plan/tokens not editable
```

## Acceptance criteria

- Preferences are editable.
- Save/cancel UX works.
- Payload contains preferences only.
- Email/display_name/plan/tokens are not editable.
- Language preference integrates with i18n if available.
- No real billing/notification delivery.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- Product requires display_name editing now.
- Backend preferences endpoint is unavailable.
- Locale preference is not part of the profile contract.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <profile preferences tests>
```

## Done means

Profile preferences can be edited through the concrete backend endpoint without changing identity/billing fields.
