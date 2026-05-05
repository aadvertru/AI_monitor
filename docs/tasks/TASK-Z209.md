# TASK-Z209 — Add Longitudinal Analytics Fixtures and Contract Tests

## Goal

Add fixtures and tests for audit comparison and trend analytics.

---

## Scope

Implement:

```text
comparison fixtures
trend fixtures
source/concept/competitor diff fixtures
backend contract tests
frontend parsing/render tests if applicable
```

---

## Fixture cases

```text
two completed audits same brand
multiple audits trend
missing accuracy
changed model set
added/removed source domains
added/removed concepts
added/removed competitors
legacy audit comparison
no previous audits
```

---

## Tests

Backend:

```text
comparison schema stable
trend schema stable
diff schema stable
missing data safe
legacy safe
no raw provider data exposed
```

Frontend:

```text
types parse fixtures
UI renders fixtures if implemented
empty state safe
```

---

## Acceptance criteria

- Longitudinal analytics fixtures exist.
- Contract tests cover main comparison/trend cases.
- No raw provider payloads/secrets in fixtures.
- Task-scoped tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not implement new analytics logic beyond tests.
- Do not run real providers.
- Do not change scoring methodology.
