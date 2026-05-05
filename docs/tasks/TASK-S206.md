# TASK-S206 — Add Evaluation Fields to Summary v2 and Answer Matrix

## Status

Ready for implementation.

## Goal

Expose answer evaluation data through summary v2 and answer matrix APIs.

This enables Web5 accuracy cards and Web6/Web7 cell verdicts.

## Dependencies

Requires:

```text
TASK-S203 — AnswerEvaluation model
TASK-R202 — Summary v2
TASK-R203 — Answer matrix
```

## Decisions

### Missing evaluation

Use:

```json
"evaluation": null
```

when no evaluation exists.

Do not synthesize `unknown` records for missing evaluations.

### Accuracy formula

Use strict formula:

```text
accuracy = correct_count / evaluated_count
```

Where:

```text
evaluated_count = correct + partial + incorrect
unknown and not_applicable are excluded
partial is not counted as correct
```

Return verdict counts so UI can show partial separately:

```json
{
  "verdict_counts": {
    "correct": 10,
    "partial": 4,
    "incorrect": 3,
    "unknown": 0,
    "not_applicable": 0
  }
}
```

If `evaluated_count=0`, accuracy is `null`.

## Scope

Implement:

```text
evaluation fields in answer matrix cells
accuracy_l1/accuracy_l2 in summary v2
accuracy by model/level
verdict_counts
task-scoped backend tests
```

## Matrix cell evaluation

```json
{
  "evaluation": {
    "verdict": "partial",
    "rationale": "Answer includes useful information but misses exact details.",
    "confidence": 0.72,
    "evaluation_version": "eval-v1",
    "evaluated_at": "2026-01-01T00:00:00Z"
  }
}
```

If absent:

```json
"evaluation": null
```

## Tests

Backend tests:

```text
matrix cell includes evaluation when present
matrix cell evaluation=null when missing
summary accuracy L1 strict correct/evaluated
summary accuracy L2 strict correct/evaluated
partial included in evaluated_count but not correct_count
unknown excluded from evaluated_count
not_applicable excluded from evaluated_count
accuracy null when evaluated_count=0
verdict_counts returned
model accuracy calculated
legacy audits without evaluation safe
rerun evaluation updates summary/matrix
```

## Acceptance criteria

- Summary v2 exposes strict accuracy fields from evaluation records.
- Answer matrix cells expose evaluation or null.
- Verdict counts returned.
- Formula documented in code/tests.
- Existing visibility/mentionability metrics unchanged.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Product wants weighted accuracy with partial=0.5.
- Existing UI already expects `unknown` object instead of null.
- Summary DTO cannot add verdict_counts without frontend impact.

## Commands

```bash
pytest <summary/matrix evaluation tests>
ruff check <touched backend files>
```

## Done means

Evaluation data feeds summary/matrix with deterministic null handling and strict accuracy formula.
