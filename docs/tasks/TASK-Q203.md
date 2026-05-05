# TASK-Q203 — Add Domain Availability UI and Generation Soft Block

## Goal

Show brand domain availability status in the audit create/edit UI and use it as a soft gate for domain-based query generation.

Manual audit creation and manual seed query input must remain available.

---

## Scope

Implement:

```text
frontend API client for POST /brand-domain/check
domain status badge
loading/error states
soft block/warning for domain-based generation
task-scoped frontend tests
```

Do not implement backend domain check in this task.

---

## UI behavior

When user enters/changes Brand domain:

```text
show unchecked/idle state
allow user to trigger check manually or auto-check with debounce
show loading state
show status badge after check
```

Statuses:

```text
reachable
dns_failed
http_failed
timeout
invalid_domain
blocked_private_network
unknown
```

User-facing copy should be translatable if i18n exists.

---

## Soft block behavior

If domain check says `query_generation_allowed=false`:

```text
disable or warn for "Use domain" in Generate Queries
domain-based generation should not run silently
manual seed query input remains enabled
brand description generation remains enabled
audit creation remains enabled
```

Do not block entire audit creation.

---

## UX details

- If domain empty, do not call check.
- If invalid domain, show inline validation.
- If check fails due to backend/network error, show safe warning.
- User can still save audit manually.
- Do not show raw backend stack traces.

---

## Tests

Frontend tests:

```text
check button/debounce calls domain check endpoint
reachable badge renders
invalid domain state renders
unreachable state renders
timeout state renders
Use domain generation option disabled/warned when not allowed
manual seed query input remains available
audit save remains available
safe error state renders
```

Safety tests:

```text
unsafe fields in mocked response are not rendered
raw HTTP details not shown
```

---

## Acceptance criteria

- Domain check API client exists.
- Domain status badge renders.
- Domain generation is soft-blocked/warned when unavailable.
- Manual audit creation remains possible.
- Manual seed query input remains possible.
- Brand description generation remains possible when domain unavailable.
- Loading/error states work.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement backend domain checking.
- Do not implement PAA.
- Do not block entire audit creation.
- Do not redesign audit create page broadly.
