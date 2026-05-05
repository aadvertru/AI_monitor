# AFTER-P — Testing Checklist After Profile / Account Shell

## Phase covered

Phase P — Profile / Account Shell.

## Primary goal to verify

Authenticated users can access a profile/account page with real identity fields and demo plan/usage/preferences, without implementing real billing.

---

## Backend tests

Verify:

```text
GET /profile requires auth
authenticated user can fetch own profile
response includes current user id/email/display_name
display_name is read-only in MVP
plan data marked demo
usage/token data marked demo
notification preferences returned
PUT /profile/preferences requires auth
preferences are backend-backed
preferences update notification booleans
preferences update locale
locale is validated against supported locales if locale config exists
invalid locale rejected
email cannot be changed through profile preferences
display_name cannot be changed through profile preferences
plan/token fields cannot be changed by client
```

Safety assertions should check absence of:

```text
password
hashed_password
jwt
secret
api_key
OPENAI_API_KEY
OPENROUTER_API_KEY
ANTHROPIC_API_KEY
```

---

## Frontend tests

Verify:

```text
/profile route is protected
authenticated user can open profile
unauthenticated user redirected/blocked
account email displayed
display name displayed as read-only
demo plan card displayed
demo token usage card displayed
notification settings displayed
demo marker visible
loading state works
API error state works
missing optional fields safe
```

Editable preferences:

```text
notification toggles update form state
locale selector works if i18n exists
save sends preferences-only payload
payload does not include email/display_name/plan/tokens
cancel resets unsaved changes
loading state during save
safe error state on failed save
email is not editable
display_name is not editable
plan is not editable
tokens are not editable
```

---

## Manual QA

Run:

```text
login
open /profile
verify email/name
verify display name is read-only
verify demo plan and token usage
toggle notification preferences
change locale if available
save/cancel
reload page
open profile on mobile viewport
logout and confirm /profile is protected
```

---

## Safety checks

Profile UI/API must not expose:

```text
password hashes
JWT/token values
provider API keys
billing secrets
raw env settings
```

---

## Exit criteria

Phase P is stable when:

```text
profile page works for authenticated users
preferences are backend-backed
display_name is read-only
invalid locale rejected
demo billing/usage clearly marked
no real billing implied
no sensitive data exposed
```
