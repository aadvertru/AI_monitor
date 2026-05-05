# TASK-S207 — Add Frontend API Types for Evaluation Data

## Goal

Add frontend TypeScript types and API parsing support for answer evaluation data in summary v2 and answer matrix responses.

This task does not implement the Web5/Web6/Web7 UI yet.

---

## Scope

Implement:

```text
Evaluation types
verdict enum types
summary accuracy types
matrix cell evaluation types
safe null handling
task-scoped frontend tests
```

---

## Types

Add types equivalent to:

```ts
type EvaluationVerdict =
  | "correct"
  | "partial"
  | "incorrect"
  | "unknown"
  | "not_applicable"

type AnswerEvaluation = {
  verdict: EvaluationVerdict
  rationale?: string | null
  confidence?: number | null
  evaluationVersion?: string | null
  evaluatedAt?: string | null
}
```

Use project naming conventions.

---

## i18n readiness

Frontend should translate verdict labels from codes.

Do not hardcode Russian-only labels like:

```text
Верно
Частично
Ошибка
```

Translation keys should support future languages beyond en/ru.

---

## Tests

Frontend/API tests:

```text
parses evaluation object
handles evaluation=null
handles unknown verdict
summary accuracy fields parsed
matrix cell evaluation parsed
verdict codes can map to translation keys
missing optional fields do not crash
```

---

## Acceptance criteria

- Frontend evaluation types exist.
- Summary/matrix types include evaluation data.
- Null/unknown evaluation handled safely.
- Verdict codes are translation-ready.
- Existing results UI not broken.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement matrix UI.
- Do not implement summary accuracy UI.
- Do not implement rerun button UI.
- Do not change backend.
