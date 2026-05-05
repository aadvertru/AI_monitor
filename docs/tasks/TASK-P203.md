# TASK-P203 — Add Protected Profile Page UI

## Goal

Add a protected frontend Profile / Account page that displays user identity, demo plan, token balance, and notification settings.

This task should render profile data only. Editing may be implemented in the next task.

---

## Scope

Implement only:

```text
protected /profile route
profile navigation entry
profile data loading
profile summary cards/sections
safe loading/error/empty states
task-scoped frontend tests
```

Do not implement real billing or payment controls.

---

## UI sections

Add sections/cards for:

```text
Account
- display name
- email

Plan
- current plan name
- demo status

Usage
- remaining tokens
- total tokens
- reset date if available
- demo marker

Notifications
- email notifications
- audit completed notifications
- provider error notifications

Preferences
- language/locale if available
```

Use existing design system components.

---

## Data source

Preferred:

```text
GET /profile
```

Fallback if backend endpoint is intentionally deferred:

```text
/auth/me + frontend mock profile data
```

Do not duplicate profile business logic in multiple components. Use a small API/hook layer.

---

## i18n

If i18n exists:

- use translation keys for labels/buttons/errors
- do not hardcode ru/en-only logic
- raw email/name values are not translated

If i18n is not implemented yet:

- keep labels centralized enough to translate later

---

## UX rules

- Profile route requires login.
- Unauthenticated user redirected to login or handled by existing protected route guard.
- Loading state shown while fetching.
- Safe error state shown on failure.
- Demo plan/usage should be visually clear.

Example copy:

```text
Demo usage data
```

or translated equivalent.

---

## Safety

Do not display:

```text
password hashes
tokens/JWT
API keys
provider secrets
raw env settings
```

---

## Tests

Add task-scoped frontend tests.

### Route/render tests

- `/profile` is protected
- profile page renders for authenticated user
- account email displayed
- plan card displayed
- token usage card displayed
- notification preferences displayed
- demo marker displayed

### State tests

- loading state renders
- API error state renders
- missing optional fields handled safely

### Safety tests

Use mocked API response containing unsafe extra fields and assert they are not rendered:

```text
password
hashed_password
jwt
secret
api_key
OPENAI_API_KEY
OPENROUTER_API_KEY
```

---

## Acceptance criteria

- Protected profile page exists.
- Navigation to profile exists if app shell supports it.
- User identity renders.
- Demo plan and token usage render.
- Notification preferences render.
- Loading/error states work.
- No real billing/payment UI is added.
- Unsafe fields are not rendered.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement editing yet.
- Do not implement billing.
- Do not implement real token accounting.
- Do not change backend profile contract.
- Do not redesign app shell.
- Do not fix unrelated frontend bugs.
