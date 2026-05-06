# Answer Evaluation Contract

Phase S adds an answer evaluation layer for accuracy and fact-checking UI.

Evaluation is separate from provider execution, parsing, scoring, and aggregation.

## Separation Rules

Evaluation must not:

- mutate raw provider answers
- mutate `ParsedResult`
- mutate `Score`
- replace visibility, mentionability, or existing SCDL scoring
- rerun provider calls
- expose evaluator prompts or raw evaluator responses in frontend DTOs

Evaluation may:

- read normalized provider answer text
- read audit-scoped brand facts
- create or update `AnswerEvaluation` records
- feed accuracy metrics and verdict UI

Visibility answers the question: "Was the brand mentioned and how prominently?"

Evaluation answers the question: "Was the answer factually correct enough against known brand facts?"

## Verdict Enum

Backend returns stable verdict codes:

```text
correct
partial
incorrect
unknown
not_applicable
```

Suggested meanings:

- `correct`: answer aligns with known brand facts
- `partial`: answer contains useful factual content but is incomplete or partly unsupported
- `incorrect`: answer contradicts known brand facts
- `unknown`: evaluator cannot decide from available answer/facts
- `not_applicable`: evaluation should not apply to this run/cell

Labels are frontend/i18n responsibility. Backend must not return language-specific labels as the source of truth.

## Evaluation DTO

Canonical frontend-safe evaluation object:

```json
{
  "verdict": "partial",
  "rationale": "The answer contains useful information but misses exact program details.",
  "confidence": 0.72,
  "evaluation_version": "eval-v1",
  "evaluated_at": "2026-01-01T00:00:00Z"
}
```

Rules:

- `verdict` is required.
- `evaluation_version` is required.
- `evaluated_at` is required once an evaluation record exists.
- `rationale` must be concise safe text or `null`.
- `confidence` is nullable and, when present, must be between `0` and `1`.
- Raw evaluator prompt/response fields are not part of this DTO.

Missing evaluation is represented as:

```json
"evaluation": null
```

Do not synthesize an `unknown` evaluation object when no evaluation record exists.

## Brand Facts Dependency

Evaluation compares answers against known brand facts where available.

Brand facts may come from:

- brand name
- brand domain
- brand description
- user-provided facts
- future domain analysis

For Phase S, brand facts are conservative audit-scoped snapshots. Evaluation must use facts from the same audit snapshot so old audits are not reinterpreted using future brand profile edits.

## Accuracy Formula

Accuracy is strict:

```text
accuracy = correct_count / evaluated_count
```

Where:

```text
evaluated_count = correct + partial + incorrect
```

Rules:

- `partial` is evaluated but not counted as correct.
- `unknown` is excluded from evaluated count.
- `not_applicable` is excluded from evaluated count.
- accuracy is `null` when evaluated count is `0`.

APIs should also expose verdict counts so UI can explain the denominator.

## Evaluator Strategy

Initial strategy:

- deterministic mock evaluator for tests and local development
- optional real evaluator later
- no real evaluator calls in CI

Mock evaluator may use stable markers such as `[CORRECT]`, `[PARTIAL]`, and `[INCORRECT]` for deterministic behavior.

Real LLM-as-judge behavior is not required for MVP tests and must be added behind explicit configuration.

## Rerun Evaluation

Endpoint:

```http
POST /audits/{id}/rerun-evaluation
```

Rules:

- requires authentication
- enforces audit ownership
- does not rerun provider calls
- does not mutate raw answers
- does not rerun parser or scoring
- updates evaluation records only
- skips failed runs or runs without usable answer text

Expected response shape:

```json
{
  "audit_id": 1,
  "evaluated_runs": 20,
  "skipped_runs": 2,
  "status": "completed",
  "warnings": []
}
```

## Testing Strategy

Automated tests must cover:

- verdict enum validation
- deterministic mock evaluator behavior
- evaluation record creation/update
- rerun endpoint auth and ownership
- raw answers unchanged after evaluation
- parsed results unchanged after evaluation
- scores unchanged after evaluation
- failed/no-answer runs skipped
- summary/matrix evaluation exposure
- no raw evaluator or provider data exposed

Automated tests must not call real evaluator/provider APIs.
