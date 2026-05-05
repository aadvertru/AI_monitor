# TASK-X208 — Add Export Fixtures and Regression Tests

## Goal

Add fixtures and regression tests for DOCX/Excel exports.

---

## Scope

Implement:

```text
export fixtures
backend export regression tests
frontend download tests if not already covered
safety tests
```

---

## Required fixture cases

```text
completed audit with evaluation
partial audit
audit without evaluation
audit without sources
multi-model audit
OpenRouter L2 experimental audit
concepts/competitors data
provider diagnostics
legacy audit
```

---

## Tests

Backend:

```text
Excel sheets stable
DOCX sections stable
files valid
partial/no-evaluation cases safe
no raw provider payloads
no secrets
```

Frontend:

```text
download buttons use correct endpoints
error state safe
```

---

## Acceptance criteria

- Export fixtures exist.
- Regression tests cover main export cases.
- Files contain expected sections/sheets.
- No raw provider payloads/secrets in exported text.
- Task-scoped tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not implement new export formats.
- Do not change export endpoints.
- Do not run real providers.
