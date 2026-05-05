# TASK-Z206 — Add Source, Concept, and Competitor Change Detection

## Goal

Add backend services for detecting changes in source domains, concepts, and competitor candidates between audits.

---

## Scope

Implement:

```text
source domain diff service
concept diff service
competitor candidate diff service
task-scoped backend tests
```

No frontend UI in this task.

---

## Diff categories

For each data type, return:

```text
added
removed
persisted
increased
decreased
```

### Source domains

Compare by:

```text
domain
```

### Concepts

Compare by normalized concept text.

### Competitor candidates

Compare by normalized name/domain.

---

## Tests

Backend tests:

```text
source domain added/removed/persisted
source count increased/decreased
concept added/removed
competitor added/removed
case/whitespace normalization
missing previous data safe
legacy audits safe
```

---

## Acceptance criteria

- Diff services exist.
- Source domain changes detected.
- Concept changes detected.
- Competitor changes detected.
- Missing data safe.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend UI.
- Do not change extraction logic.
- Do not change scoring.
