# TASK-R202 — Add Backend Summary v2 DTO and Endpoint

## Goal

Add a backend summary v2 endpoint that returns data needed for the Web5-style summary screen.

This endpoint should be target-aware and compatible with multi-model/multi-level audits.

---

## Scope

Implement:

```text
summary v2 DTOs
summary v2 aggregation service
GET /audits/{id}/summary-v2 endpoint or equivalent additive endpoint
task-scoped backend tests
```

Do not implement frontend UI in this task.

---

## Endpoint

Preferred:

```http
GET /audits/{id}/summary-v2
```

Use existing auth/ownership guards.

---

## Required DTO sections

Return fields equivalent to:

```text
audit_id
status
totals
overall
model_summaries
provider_diagnostics
```

### Totals

Include:

```text
query_count
target_count
run_count
levels
completed_runs
failed_runs
partial_runs if applicable
```

### Overall metrics

Include:

```text
mentionability_l1
mentionability_l2
accuracy_l1
accuracy_l2
tone
```

`accuracy_*` may be null/unknown until Phase S evaluation exists.

### Model summaries

For each model group, return:

```text
target_group_label
ai_family
execution_provider
model_provider
model_id
mr_l1
mr_l2
delta_mr
accuracy_l1
accuracy_l2
delta_accuracy
tone_l1
tone_l2
```

Use null or `N/A` convention consistently for missing levels.

---

## Metric rules

### Mentionability

Mentionability should use existing backend parser/scoring data.

Example:

```text
percentage = brand_found_count / processed_runs
```

Adapt to existing scoring model.

### Accuracy

Accuracy should be null/unknown until evaluation data exists.

Do not fake accuracy from existing visibility score.

### Tone

Use existing sentiment/tone if available.

If not available, return null/unknown safely.

---

## Backward compatibility

- Existing summary endpoint remains unchanged unless project convention requires extension.
- Legacy audits without audit targets must return safe data.
- Single-provider/single-level audits must work.
- OpenRouter metadata must not break summary.

---

## Safety

Do not expose:

```text
raw provider responses
raw prompts
request headers
API keys
stack traces
```

---

## Tests

Add task-scoped backend/API tests.

Test:

```text
requires auth
enforces ownership
returns safe empty summary for audit with no runs
returns summary for completed mock audit
returns summary for partial audit
groups by model_id and level
calculates mentionability L1/L2
accuracy fields null/unknown before evaluation
handles missing L2 data as N/A/null
legacy audit compatibility
OpenRouter gateway metadata safe
provider diagnostics safe
```

---

## Acceptance criteria

- Summary v2 endpoint exists.
- Endpoint is authenticated and owner-scoped.
- Response includes totals, overall metrics, and model_summaries.
- Mentionability L1/L2 is calculated backend-side.
- Accuracy is not faked before evaluation exists.
- Partial/failed/legacy audits handled safely.
- Existing endpoints remain backward compatible.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend Web5 UI.
- Do not implement evaluation/fact-checking.
- Do not implement source domain aggregation.
- Do not implement exports.
- Do not change parser/scoring methodology.
- Do not fix unrelated legacy failures.
