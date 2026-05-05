# TASK-M206 — Add Audit Target Caps and Run Count Estimate API

## Status

Ready for implementation after TASK-M203. Can be done before or after M204.

## Goal

Add backend caps and a concrete public run-count estimate endpoint for multi-target audits.

This prevents accidental large audits such as:

```text
20 queries × 20 models × 2 levels
```

---

## Dependencies

Requires:

```text
TASK-M201
TASK-M203
```

Recommended before frontend selector work:

```text
TASK-N205
TASK-N206
TASK-N207
```

---

## Scope

Implement:

```text
target count caps
model count caps
query count caps
total run count caps
run-count estimate service
POST /audits/estimate endpoint
safe validation errors
task-scoped backend/API tests
```

---

## Config keys

Add or reuse config keys:

```text
MAX_AUDIT_TARGETS
MAX_MODELS_PER_AUDIT
MAX_QUERIES_PER_AUDIT
MAX_TOTAL_RUNS_PER_AUDIT
```

Use project naming conventions.

Recommended initial defaults for pilot:

```text
MAX_AUDIT_TARGETS=10
MAX_MODELS_PER_AUDIT=5
MAX_QUERIES_PER_AUDIT=20
MAX_TOTAL_RUNS_PER_AUDIT=100
```

Adjust to current provider caps if stricter.

---

## Authenticated estimate endpoint

Implement:

```http
POST /audits/estimate
```

This task must include the endpoint. Do not leave API surface undecided.

Authentication rules:

```text
requires authenticated user session
ownership check is not applicable because the request is draft-only and does not reference a stored audit
unauthenticated requests must be rejected with the project's standard auth error
```

### Request

Accept a draft audit-like payload:

```json
{
  "seed_queries": ["query 1"],
  "seed_query_items": [
    {
      "text": "query 1",
      "type": "brand_direct",
      "source": "user"
    }
  ],
  "model_targets": [
    {
      "ai_family": "chatgpt",
      "execution_provider": "openrouter",
      "model_provider": "openai",
      "model_id": "openai/gpt-4o-mini",
      "display_name": "GPT-4o mini",
      "level": "L1",
      "gateway": true,
      "gateway_l2_experimental": false
    }
  ]
}
```

Use the same canonical field names as audit create.

If both `seed_queries` and `seed_query_items` are present, follow existing project seed-query compatibility rules. If no rule exists, prefer rejecting ambiguous input with 422.

Legacy estimate payload should also be supported:

```json
{
  "seed_queries": ["query 1"],
  "providers": ["mock"],
  "scdl_level": "L1"
}
```

### Response

Return:

```json
{
  "query_count": 1,
  "target_count": 1,
  "model_count": 1,
  "estimated_runs": 1,
  "caps": {
    "max_audit_targets": 10,
    "max_models_per_audit": 5,
    "max_queries_per_audit": 20,
    "max_total_runs_per_audit": 100
  },
  "over_cap": false,
  "violations": [],
  "warnings": []
}
```

For cap violations:

```json
{
  "over_cap": true,
  "violations": [
    {
      "code": "MAX_TOTAL_RUNS_EXCEEDED",
      "message": "Estimated audit runs exceed the configured limit."
    }
  ]
}
```

Use project error/DTO conventions.

---

## Validation

Hard reject audit create/update over caps with 422.

The estimate endpoint itself should return estimate + violations instead of failing, unless the payload is structurally invalid.

Recommended:

```text
structurally invalid payload → 422
valid payload over cap → 200 with over_cap=true and violations
actual audit create/update over cap → 422
```

---

## Model count definition

Define model_count as unique model identity count, not target count.

Recommended key:

```text
execution_provider + model_id
```

Example:

```text
same model L1+L2 = target_count 2, model_count 1
two models L1 = target_count 2, model_count 2
```

---

## Tests

Backend/API tests:

```text
POST /audits/estimate exists
unauthenticated POST /audits/estimate rejected
estimate correct for 1 query × 1 target
estimate correct for multiple queries/targets
same model L1+L2 => model_count 1, target_count 2
exact cap accepted
over target cap reported
over model cap reported
over query cap reported
over total run cap reported
legacy provider/scdl payload estimate works
typed seed_query_items estimate works
structurally invalid payload returns 422
valid over-cap estimate returns safe violations
audit create/update over cap rejected with 422
safe validation messages
no provider calls made
```

---

## Acceptance criteria

- Caps config exists.
- Run estimate service exists.
- `POST /audits/estimate` exists with concrete request/response and requires authentication.
- Estimate endpoint supports canonical and legacy payloads.
- Create/update validation enforces caps.
- Excessive audits rejected safely on create/update.
- Estimate endpoint reports over-cap violations safely.
- Tests pass.
- Touched-file ruff passes.

---

## Escalate if

- The project cannot add an authenticated estimate endpoint without auth/routing refactor.
- Existing seed query compatibility rules conflict with estimate payload shape.
- Caps already exist under different names and changing them would break prior provider pilot behavior.
- Frontend expects estimate to be unauthenticated.

## Commands

Use task-scoped commands. Adjust exact paths to the repository layout.

Suggested backend checks:

```bash
pytest <task-specific tests>
ruff check <touched backend files>
```

Do not run or fix unrelated full-suite legacy failures inside this task.


## Done means

Backend exposes authenticated `POST /audits/estimate`, validates caps consistently, and task tests prove estimate/caps work for canonical and legacy payloads without provider calls.

---

## Non-goals

- Do not implement frontend estimate UI.
- Do not implement cost estimate.
- Do not implement billing.
- Do not redesign provider caps beyond this task.
