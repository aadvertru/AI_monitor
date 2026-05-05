# TASK-S201 — Define Answer Evaluation / Fact-Check Contract

## Goal

Define the answer evaluation / fact-check contract needed for Web5/Web6/Web7-style accuracy and cell verdicts.

This task is documentation/contract only. Do not change runtime code.

---

## Context

The target UI requires:

```text
accuracy L1/L2
verdict badges: correct / partial / incorrect / unknown
cell-level rationale
rerun fact-checking action
```

This must be implemented as a separate layer from parser/scoring.

---

## File to create

```text
docs/ANSWER_EVALUATION_CONTRACT.md
```

---

## Required decisions

### 1. Evaluation is separate from parser/scoring

Document:

```text
Evaluation must not mutate raw provider answers.
Evaluation must not mutate ParsedResult.
Evaluation must not replace visibility/mentionability scoring.
Evaluation is an additional layer used for accuracy/verdict UI.
```

### 2. Verdict enum

Define:

```text
correct
partial
incorrect
unknown
not_applicable
```

### 3. Evaluation DTO

Suggested:

```json
{
  "verdict": "partial",
  "label": "Partial",
  "rationale": "The answer contains useful information but misses exact program details.",
  "confidence": 0.72,
  "evaluation_version": "eval-v1",
  "evaluated_at": "2026-01-01T00:00:00Z"
}
```

Labels are translated by frontend. Backend returns stable codes.

### 4. Brand facts dependency

Document that evaluation should compare answers against known brand facts where available.

Brand facts may come from:

```text
brand name
brand domain
brand description
user-provided facts
domain analysis, future
```

### 5. Evaluator strategy

Define initial strategy:

```text
mock/deterministic evaluator for tests
optional real evaluator later
no real evaluator calls in CI
```

Do not make LLM-as-judge required for MVP tests.

### 6. Rerun evaluation

Define endpoint:

```http
POST /audits/{id}/rerun-evaluation
```

or equivalent.

Rules:

```text
requires auth and ownership
does not rerun provider calls
does not mutate raw answers
does not rerun parser/scoring unless explicitly requested later
updates evaluation records only
```

---

## Acceptance criteria

- Evaluation contract documented.
- Verdict enum defined.
- Evaluation DTO defined.
- Parser/scoring separation documented.
- Brand facts dependency documented.
- Rerun evaluation behavior documented.
- Testing strategy documented.
- No runtime code changed.

---

## Non-goals

- Do not implement evaluation model.
- Do not implement evaluator.
- Do not implement rerun endpoint.
- Do not change parser/scoring.
