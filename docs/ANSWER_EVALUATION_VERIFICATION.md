# Answer Evaluation Verification

Manual/API QA checklist for the answer evaluation and fact-checking foundation.

Allowed statuses: `Not run`, `Pass`, `Fail`, `Blocked`, `Partial`.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| S-S01 | Pass | Covered by `tests/api/test_brand_facts.py`. |  |
| S-S02 | Pass | Covered by `tests/api/test_answer_evaluation_rerun.py`. |  |
| S-S03 | Pass | Covered by `tests/api/test_answer_evaluation_rerun.py`. |  |
| S-S04 | Pass | Covered by `tests/api/test_answer_evaluation_rerun.py` and `tests/api/test_answer_evaluations.py`. |  |
| S-S05 | Pass | Covered by `tests/api/test_answer_evaluation_rerun.py`. |  |
| S-S06 | Pass | Covered by `tests/api/test_answer_evaluation_rerun.py`. |  |
| S-S07 | Pass | Covered by `tests/api/test_results_v2_matrix.py`. |  |
| S-S08 | Pass | Covered by `tests/api/test_results_v2_summary.py`. |  |
| S-S09 | Pass | Covered by summary/matrix null-handling tests. |  |
| S-S10 | Pass | Covered by backend/frontend safety assertions. |  |
| S-S11 | Pass | Covered by `tests/api/test_answer_evaluation_rerun.py`. |  |
| S-S12 | Pass | Covered by `apps/web/src/lib/api/client.test.ts`. |  |

## Scenarios

### S-S01 - Brand facts created from brand fields

Purpose: verify that each audit receives an audit-scoped BrandFact snapshot.

Preconditions: authenticated user; API and DB available.

Steps:
1. Create an audit with brand name, brand domain, and brand description.
2. Inspect `brand_facts` for the created audit.

Expected result: facts exist for brand name, official domain, and description claim; each fact has `audit_id`; source labels match the originating field.

Actual result:

Status: Pass

Issue ID:

### S-S02 - Evaluation records created for successful runs

Purpose: verify rerun evaluation creates AnswerEvaluation rows for successful runs with usable answer text.

Preconditions: audit has successful runs with raw answer text and brand facts.

Steps:
1. Call `POST /audits/{id}/rerun-evaluation`.
2. Inspect `answer_evaluations`.

Expected result: one evaluation exists per eligible successful run; verdict, rationale, confidence, evaluation version, and evaluated timestamp are persisted.

Actual result:

Status: Pass

Issue ID:

### S-S03 - Failed/no-answer runs skipped

Purpose: verify evaluator does not create records for provider failures or empty answers.

Preconditions: audit has failed runs and successful runs with empty or missing raw answers.

Steps:
1. Call `POST /audits/{id}/rerun-evaluation`.
2. Inspect response counters and `answer_evaluations`.

Expected result: failed/no-answer runs increase `skipped_runs`; no evaluation rows are created for them.

Actual result:

Status: Pass

Issue ID:

### S-S04 - Rerun evaluation updates existing evaluations

Purpose: verify rerun is idempotent at the run level.

Preconditions: audit has existing AnswerEvaluation rows.

Steps:
1. Capture existing evaluation IDs.
2. Call `POST /audits/{id}/rerun-evaluation`.
3. Inspect evaluation rows again.

Expected result: existing rows are updated/replaced in place for the same `run_id`; duplicate evaluations are not created.

Actual result:

Status: Pass

Issue ID:

### S-S05 - Raw answers remain unchanged after evaluation

Purpose: verify evaluation does not mutate raw provider outputs.

Preconditions: audit has RawResponse rows.

Steps:
1. Capture `raw_responses.raw_answer`, `request_snapshot`, `citations`, and provider metadata.
2. Call `POST /audits/{id}/rerun-evaluation`.
3. Compare raw response fields.

Expected result: raw response fields are unchanged.

Actual result:

Status: Pass

Issue ID:

### S-S06 - Parser/scoring remain unchanged after evaluation

Purpose: verify evaluation is separate from parser and scoring.

Preconditions: audit has ParsedResult and Score rows.

Steps:
1. Capture parsed result and score fields.
2. Call `POST /audits/{id}/rerun-evaluation`.
3. Compare parsed result and score fields.

Expected result: ParsedResult and Score rows are unchanged; parser/scoring are not rerun.

Actual result:

Status: Pass

Issue ID:

### S-S07 - Matrix cells include verdict/rationale

Purpose: verify answer matrix exposes saved evaluation data.

Preconditions: audit has at least one AnswerEvaluation.

Steps:
1. Call `GET /audits/{id}/answer-matrix`.
2. Inspect the cell for the evaluated run.

Expected result: cell has `evaluation` object with verdict, rationale, confidence, evaluation version, and evaluated timestamp.

Actual result:

Status: Pass

Issue ID:

### S-S08 - Summary accuracy updates after evaluation

Purpose: verify summary v2 strict accuracy is calculated from evaluation records.

Preconditions: audit has evaluations with correct, partial, incorrect, unknown, and not_applicable verdicts.

Steps:
1. Call `GET /audits/{id}/summary-v2`.
2. Inspect accuracy and verdict counts.

Expected result: accuracy is `correct / (correct + partial + incorrect)`; partial counts as evaluated but not correct; unknown and not_applicable are excluded from denominator; verdict counts include all verdicts.

Actual result:

Status: Pass

Issue ID:

### S-S09 - Unknown/missing evaluations handled safely

Purpose: verify missing evaluations do not synthesize fake unknown objects.

Preconditions: audit has runs without evaluation rows.

Steps:
1. Call `GET /audits/{id}/answer-matrix`.
2. Call `GET /audits/{id}/summary-v2`.

Expected result: matrix cell `evaluation` is `null`; summary accuracy is `null` when evaluated denominator is zero.

Actual result:

Status: Pass

Issue ID:

### S-S10 - No raw evaluator/provider data exposed

Purpose: verify API responses do not leak raw answers, prompts, request snapshots, headers, stack traces, API keys, or provider payloads.

Preconditions: audit has raw responses and evaluations.

Steps:
1. Call rerun evaluation, summary v2, and answer matrix endpoints.
2. Search serialized responses for sensitive fields and known secret markers.

Expected result: no raw prompt/response/provider secret fields appear in public responses.

Actual result:

Status: Pass

Issue ID:

### S-S11 - Rerun fact-checking endpoint auth/ownership

Purpose: verify endpoint is protected consistently with other audit endpoints.

Preconditions: owner user, non-owner user, and audit owned by owner.

Steps:
1. Call `POST /audits/{id}/rerun-evaluation` unauthenticated.
2. Call it as a non-owner.
3. Call it as the owner.

Expected result: unauthenticated request is rejected; non-owner is rejected; owner succeeds.

Actual result:

Status: Pass

Issue ID:

### S-S12 - i18n-ready verdict codes

Purpose: verify frontend uses verdict codes that can map to translation keys.

Preconditions: frontend app available.

Steps:
1. Inspect evaluation verdict types and translation-key mapping.
2. Verify no Russian-only hardcoded verdict labels are required by API parsing.

Expected result: verdict codes map to stable translation keys for future en/ru labels.

Actual result:

Status: Pass

Issue ID:

## Captured Issues

No Phase S verification issues were captured. Automated backend and frontend task-scoped checks passed.

Use this template for any failed, blocked, or partial scenario.

```markdown
### ISSUE-S-001 - Short title

Scenario: S-Sxx

Severity: blocker | major | minor

Status: open | fixed | deferred

Observed:

Expected:

Reproduction steps:

Affected files/endpoints:

Resolution / rationale:
```
