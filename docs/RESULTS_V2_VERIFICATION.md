# Results v2 Verification Checklist

Manual/API QA checklist for Phase R Results Data Contracts v2.

Allowed statuses: `Not run`, `Pass`, `Fail`, `Blocked`, `Partial`.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| R-S01 | Pass | API checked on created audit `#43`: run_count=0, evaluation=null, placeholders empty. |  |
| R-S02 | Pass | API checked on completed mock legacy audit `#42`: 10 queries, 10 completed runs. |  |
| R-S03 | Pass | API checked on partial OpenRouter audit `#45`: 7 completed, 1 failed, safe diagnostics. |  |
| R-S04 | Pass | API checked on single-column L1 legacy matrix `#42`. |  |
| R-S05 | Pass | API checked on audit `#43`: separate L1/L2 target columns with `not_run` cells. |  |
| R-S06 | Pass | API checked on multi-model audit `#45`: two OpenRouter target columns. |  |
| R-S07 | Pass | API checked on audit `#45`: failed cell exposes safe `RATE_LIMIT` provider_error. |  |
| R-S08 | Pass | API checked on audit `#43`: OpenRouter gateway and L2 experimental metadata present. |  |
| R-S09 | Pass | API checked on L1/L2/legacy audits: `domains=[]`, `warnings=[]`. |  |
| R-S10 | Pass | API checked on summary/matrix/detail payloads: placeholder arrays empty. |  |
| R-S11 | Pass | API checked on legacy audits `#42`, `#41`, `#40`: stable legacy columns and no crashes. |  |
| R-S12 | Pass | API checked across 15 serialized v2 payloads: no raw/sensitive keys found. |  |

## Scenarios

## R-S01 - Summary v2 Empty Audit

### Purpose
Verify `GET /audits/{id}/summary-v2` returns a safe empty state before runs exist.

### Preconditions
Authenticated user owns a created audit with at least one query and no runs.

### Steps
1. Call `GET /audits/{id}/summary-v2`.
2. Inspect `totals`, `overall`, `model_summaries`, `concepts`, `competitor_candidates`, and `provider_diagnostics`.

### Expected Result
Response is `200`; counts are zero where no run data exists; accuracy fields are `null`; placeholder arrays are empty; no raw provider payload is present.

### Actual Result

### Status
Not run

### Issue ID

## R-S02 - Summary v2 Completed Mock Audit

### Purpose
Verify completed mock audit summary-v2 aggregation is backend-owned and stable.

### Preconditions
Authenticated user owns a completed mock audit with parsed/scored successful runs.

### Steps
1. Call `GET /audits/{id}/summary-v2`.
2. Compare totals, mentionability, tone, and model summaries with the underlying runs.

### Expected Result
Response is `200`; completed/failed counts and mentionability are correct; `model_summaries` are grouped by model/target identity; accuracy remains `null`.

### Actual Result

### Status
Not run

### Issue ID

## R-S03 - Summary v2 Partial Audit

### Purpose
Verify partial audits expose safe completed and failed run information.

### Preconditions
Authenticated user owns a partial audit with at least one successful run and one failed/provider-error run.

### Steps
1. Call `GET /audits/{id}/summary-v2`.
2. Inspect totals and `provider_diagnostics`.

### Expected Result
Response is `200`; completed and failed counts are correct; diagnostics contain safe provider/code/message/model/level data only.

### Actual Result

### Status
Not run

### Issue ID

## R-S04 - Matrix for Single Model L1

### Purpose
Verify `GET /audits/{id}/answer-matrix` returns one L1 column and query rows.

### Preconditions
Authenticated user owns an audit with one L1 audit target and at least one query.

### Steps
1. Call `GET /audits/{id}/answer-matrix`.
2. Inspect `columns`, `rows`, and `cells`.

### Expected Result
Response is `200`; one column matches the L1 target; rows match seed queries; completed cells include `answer_excerpt`; `evaluation` is `null`.

### Actual Result

### Status
Not run

### Issue ID

## R-S05 - Matrix for Same Model L1+L2

### Purpose
Verify matrix supports the same model represented as separate L1 and L2 columns.

### Preconditions
Authenticated user owns an audit with the same model configured for L1 and L2.

### Steps
1. Call `GET /audits/{id}/answer-matrix`.
2. Inspect column levels and cell mapping.

### Expected Result
Response includes separate L1 and L2 columns; cells map by query and target; L2 gateway metadata remains safe.

### Actual Result

### Status
Not run

### Issue ID

## R-S06 - Matrix for Multi-Model Audit

### Purpose
Verify matrix columns match multiple selected models.

### Preconditions
Authenticated user owns an audit with two or more model targets.

### Steps
1. Call `GET /audits/{id}/answer-matrix`.
2. Compare columns to audit target setup.

### Expected Result
Columns preserve target labels, model IDs, model providers, execution providers, levels, and gateway flags.

### Actual Result

### Status
Not run

### Issue ID

## R-S07 - Failed Cell Provider Diagnostics

### Purpose
Verify failed matrix cells expose safe provider diagnostics.

### Preconditions
Authenticated user owns an audit with at least one failed, timed out, or rate-limited run.

### Steps
1. Call `GET /audits/{id}/answer-matrix`.
2. Inspect failed cell `provider_error`.

### Expected Result
Failed cell status is `failed`; provider error has safe code/message/provider/model/level/retryable fields; no stack trace, token, request headers, or API key appears.

### Actual Result

### Status
Not run

### Issue ID

## R-S08 - OpenRouter Gateway Metadata in Matrix

### Purpose
Verify OpenRouter gateway metadata is represented safely.

### Preconditions
Authenticated user owns an OpenRouter-backed audit with L1 and optionally L2 targets.

### Steps
1. Call `GET /audits/{id}/answer-matrix`.
2. Inspect column `gateway` and `gateway_l2_experimental` fields.

### Expected Result
Gateway flags are present and boolean; no OpenRouter API key, headers, raw prompt, or request payload is exposed.

### Actual Result

### Status
Not run

### Issue ID

## R-S09 - Source-Domain Placeholder Endpoint

### Purpose
Verify `GET /audits/{id}/source-domains` is a strict empty placeholder until Phase T.

### Preconditions
Authenticated user owns any audit, including an L2 audit with source citations.

### Steps
1. Call `GET /audits/{id}/source-domains`.
2. Inspect `domains` and `warnings`.

### Expected Result
Response is `200`; `domains=[]`; `warnings=[]`; no grouping or raw source/provider payload is returned.

### Actual Result

### Status
Not run

### Issue ID

## R-S10 - Concepts/Competitors Placeholder Fields

### Purpose
Verify placeholder concept and competitor-candidate fields are present and empty.

### Preconditions
Authenticated user owns any audit with summary-v2 and matrix responses available.

### Steps
1. Call `GET /audits/{id}/summary-v2`.
2. Call `GET /audits/{id}/answer-matrix`.
3. Inspect `concepts` and `competitor_candidates`.

### Expected Result
Placeholder arrays exist and are empty; generic descriptive phrases are not reclassified as competitors in Phase R.

### Actual Result

### Status
Not run

### Issue ID

## R-S11 - Legacy Audit Compatibility

### Purpose
Verify Results v2 remains safe for audits created before `audit_targets`.

### Preconditions
Authenticated user owns a legacy audit without `audit_targets`.

### Steps
1. Call `GET /audits/{id}/summary-v2`.
2. Call `GET /audits/{id}/answer-matrix`.
3. Call `GET /audits/{id}/source-domains`.

### Expected Result
Responses are `200`; matrix uses stable legacy columns; source domains remain empty; no crash due to missing target metadata.

### Actual Result

### Status
Not run

### Issue ID

## R-S12 - Raw Provider Data Is Not Exposed

### Purpose
Verify Results v2 contracts do not expose raw provider responses or sensitive request data.

### Preconditions
Authenticated user owns an audit with raw responses, provider metadata, and at least one provider error.

### Steps
1. Call all Results v2 endpoints.
2. Search serialized responses for raw/sensitive keys.

### Expected Result
Responses do not contain `raw_answer`, `request_snapshot`, `raw_prompt`, `headers`, `authorization`, `api_key`, cookies, tokens, stack traces, or full raw provider payloads.

### Actual Result

### Status
Not run

### Issue ID

# Captured Issues

## ISSUE-R-001 - Short title

### Scenario
R-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Actual result
...

### Expected result
...

### Evidence
...

### Suggested next step
...
