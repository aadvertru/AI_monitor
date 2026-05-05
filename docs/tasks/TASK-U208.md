# TASK-U208 — Add Concepts/Competitors Fixtures and Contract Tests

## Goal

Add fixtures and contract tests for concepts and competitor candidate data.

---

## Scope

Implement:

```text
concept fixtures
competitor candidate fixtures
legacy competitor fixtures
backend contract tests
frontend parsing/render tests if applicable
```

---

## Required fixture cases

```text
concepts only
competitor candidates only
concepts + competitors
empty concepts/competitors
legacy competitors field
generic phrases not competitors
Russian comparison context if supported
multi-model evidence
```

---

## Tests

Backend contract tests:

```text
concept schema stable
competitor candidate schema stable
evidence summary stable
legacy field compatibility
no raw provider payload exposed
```

Frontend tests if applicable:

```text
concept fixtures render
competitor fixtures render
empty states render
legacy fallback safe
```

---

## Acceptance criteria

- Fixtures exist.
- Contract tests cover concepts/competitors/legacy cases.
- No raw provider payloads/secrets in fixtures.
- Task-scoped tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not implement new extraction logic.
- Do not change parser/scoring.
- Do not run real providers.
