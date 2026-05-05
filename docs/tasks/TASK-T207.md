# TASK-T207 — Add Source Intelligence v2 Fixtures and Contract Tests

## Goal

Add fixtures and contract tests for Source Intelligence v2.

These fixtures should stabilize future UI and export work.

---

## Scope

Implement:

```text
source-domain fixtures
backend contract tests
frontend parsing/render fixtures if applicable
legacy/no-source fixtures
OpenRouter L2 no-source fixture
```

---

## Required fixture cases

Create fixtures for:

```text
no sources
single domain with one URL
single domain with multiple URLs
same registrable domain across subdomains
multiple domains
duplicate URLs
invalid URL skipped/safe
OpenRouter L2 with citations
OpenRouter L2 without citations
legacy source records
partial audit with some source groups
```

---

## Contract tests

Backend:

```text
source domain endpoint schema stable
same domain grouped
counts stable
URL evidence stable
invalid/unsafe fields excluded
legacy source records safe
```

Frontend, if applicable:

```text
types parse fixtures
domain UI renders fixtures
empty/no-source fixture safe
```

---

## Acceptance criteria

- Source Intelligence v2 fixtures exist.
- Contract tests cover key source grouping cases.
- Fixtures contain no raw provider payloads/secrets.
- Task-scoped tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not implement new UI behavior beyond tests.
- Do not change provider adapters.
- Do not run real providers.
- Do not fix unrelated legacy failures.
