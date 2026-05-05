# AFTER-M — Testing Checklist After Canonical Audit Targets Foundation

## Phase covered

Phase M — Canonical Audit Targets Foundation.

## Primary goal to verify

The system can create, store, schedule, estimate, and execute audits using canonical `model_targets`, while preserving legacy `providers[] + scdl_level` compatibility.

---

## Backend tests

### Data model and migration

Verify:

```text
AuditTarget table/model exists
migration applies cleanly
existing audits without targets still load
audit-owned relationship works
audit delete removes owned targets if current delete policy requires it
invalid level rejected at the chosen model/repository/schema layer
gateway_l2_experimental=true rejected for L1 at the chosen validation layer
```

### DTO validation

Verify:

```text
model_targets accepted in create/update payloads
one target = one model + one level
same model L1+L2 becomes two targets
invalid level rejected
missing required target fields rejected
gateway_l2_experimental=true rejected for L1
duplicate targets rejected or deduplicated according to contract
mixed canonical model_targets + legacy providers/scdl_level rejected with 422
```

### Legacy compatibility

Verify:

```text
legacy providers[] + scdl_level still accepted
legacy payload converts to canonical targets internally
legacy audit detail still renders
legacy audit can still be scheduled/run safely
```

### Scheduling and provider execution

Verify:

```text
jobs/runs = seed_queries × model_targets
target_id stored on jobs/runs/results
legacy audit without targets still schedules safely
duplicate scheduling prevented
OpenRouter target metadata passed through
OpenAI/native target metadata passed through
```

Mandatory provider model payload check:

```text
two same-level targets with different model_id values produce two distinct provider requests
target A model_id appears in provider request model payload
target B model_id appears in provider request model payload
runs are not collapsed by same provider/level
no fallback to global OPENROUTER_L1_MODEL when target.model_id is present
```

Example:

```text
target A: provider=openrouter, level=L1, model_id=openai/gpt-4o-mini
target B: provider=openrouter, level=L1, model_id=anthropic/claude-3-5-sonnet
expected provider request models:
- openai/gpt-4o-mini
- anthropic/claude-3-5-sonnet
```

### Caps and estimates

Verify:

```text
POST /audits/estimate exists
POST /audits/estimate requires auth
estimate = query_count × target_count
same model L1+L2 => model_count 1 and target_count 2
exact cap accepted
over MAX_AUDIT_TARGETS reported/rejected according to endpoint/create semantics
over MAX_MODELS_PER_AUDIT reported/rejected
over MAX_QUERIES_PER_AUDIT reported/rejected
over MAX_TOTAL_RUNS_PER_AUDIT reported/rejected
legacy provider/scdl payload estimate works
typed seed_query_items estimate works
no provider calls made during estimate
```

---

## Frontend/API contract tests

Verify:

```text
AuditTarget internal camelCase type parses backend detail response
backend wire field is model_targets
frontend internal field may be modelTargets
create request body contains model_targets
create request body does not contain modelTargets
update request body contains model_targets
response model_targets maps to internal modelTargets
legacy audit detail still parses
gateway_l2_experimental maps to gatewayL2Experimental
gatewayL2Experimental maps to gateway_l2_experimental
```

---

## Manual QA

Run these checks manually:

```text
create audit with 1 model L1
create audit with same model L1 + L2
create audit with 2 different model targets
create legacy provider/scdl audit if legacy flow still exposed
verify run estimate before start
verify estimate endpoint is unavailable without login
run mock audit
confirm results/runs are tied to target_id
confirm two same-level different model_id targets do not collapse
open audit detail after reload
```

---

## Safety checks

Ensure responses do not expose:

```text
raw provider responses
raw prompts
API keys
headers
stack traces
```

---

## Exit criteria

Phase M is stable when:

```text
canonical model_targets are accepted and persisted
legacy audits remain usable
jobs schedule by query × target
target_id persists into runs/results
target.model_id controls provider request model payload
POST /audits/estimate is authenticated and correct
frontend uses model_targets wire field
caps and estimates work
mock multi-target audit completes
```
