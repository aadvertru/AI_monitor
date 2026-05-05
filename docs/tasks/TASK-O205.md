# TASK-O205 — Translate Audit Create/List/Detail UI

## Goal

Translate audit list, audit create/edit, and audit detail/status UI.

---

## Scope

Translate:

```text
audit list labels
create/edit audit form labels
validation messages
seed query editor labels
model target selector labels if implemented
audit detail/status labels
provider diagnostics labels
start audit action labels
```

Do not translate raw provider answers, seed query text, brand descriptions, or source snippets.

---

## Rules

- Keep backend status/error codes stable.
- Frontend maps codes to localized labels.
- L1/L2 labels can be localized as display text but values remain `L1`/`L2`.
- Provider/model ids are not translated.

---

## Tests

Frontend tests:

```text
audit list labels in en/ru
create form labels in en/ru
validation messages translated
status labels translated
provider diagnostic labels translated
raw seed query text unchanged
brand description unchanged
```

---

## Acceptance criteria

- Audit list/create/detail UI translated.
- Validation/status/provider diagnostics translated.
- Raw user/provider content unchanged.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not translate results matrix/summary yet unless already trivial.
- Do not change backend.
- Do not change audit data model.
