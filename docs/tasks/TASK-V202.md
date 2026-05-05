# TASK-V202 — Add Web5 Summary Data Hook and Page Shell

## Goal

Add the frontend data hook and page shell for the Web5-style audit summary.

This task should wire the page to `summary-v2` data but should not implement all visual sections yet.

---

## Scope

Implement:

```text
summary v2 query hook
summary page shell/container
loading/error/empty states
basic route integration if needed
task-scoped frontend tests
```

Do not implement final cards/table/actions yet.

---

## Data source

Use existing API client from Results v2:

```text
GET /audits/{id}/summary-v2
```

Use TanStack Query conventions if project uses them.

---

## Page shell

The shell should support:

```text
audit title/header area placeholder
summary content area
model summary area placeholder
actions area placeholder
provider diagnostics area
```

---

## State handling

Handle:

```text
loading
API error
audit not found / forbidden according to existing route behavior
empty summary
partial audit
failed audit
```

Do not show raw API error bodies.

---

## i18n

Use translation keys for all static labels.

Do not translate raw audit title or user content.

---

## Tests

Frontend tests:

```text
summary hook calls summary-v2 endpoint
loading state renders
error state renders safely
empty summary state renders
page shell renders with mock summary data
provider diagnostics placeholder renders if diagnostics exist
i18n labels render
```

---

## Acceptance criteria

- Summary v2 hook/client integration works.
- Web5 summary page shell exists.
- Loading/error/empty states work.
- No raw API/provider payloads displayed.
- Static labels use i18n if available.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement final cards/table.
- Do not implement exports.
- Do not implement rerun evaluation action.
- Do not change backend.
- Do not calculate metrics in frontend.
