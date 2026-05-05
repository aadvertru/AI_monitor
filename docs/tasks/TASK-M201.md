# TASK-M201 — Define Canonical AuditTarget Contract

## Status

Ready for implementation.

## Goal

Define the canonical audit target contract for multi-model and multi-level audits.

This task is documentation/contract only. Do not change runtime code.

The goal is to replace the old execution model:

```text
providers[] + audit-level scdl_level
```

with a canonical model where one target represents one model at one SCDL level.

---

## Dependencies

None.

This is the first task in Phase M.

---

## Context

The product now needs audits across multiple AI families, multiple models, and L1/L2 levels.

Future UI screens require:

```text
model-level summary
query × model/level answer matrix
per-model L1/L2 deltas
source aggregation by model/level
cost/run estimates
retry/cancel per target/run later
```

The old `providers[]` and audit-level `scdl_level` model cannot represent this cleanly.

---

## Files to update/create

Preferred new file:

```text
docs/AUDIT_TARGETS_CONTRACT.md
```

Also update if relevant:

```text
docs/ARCHITECTURE.md
docs/PRODUCT_SPEC.md
docs/BACKEND_CONTEXT.md
docs/FRONTEND_CONTEXT.md
docs/TASKS.md
```

---

## Required decisions

### 1. Canonical target shape

Document one target as:

```json
{
  "target_id": "t1",
  "ai_family": "chatgpt",
  "execution_provider": "openrouter",
  "model_provider": "openai",
  "model_id": "openai/gpt-4o-mini",
  "display_name": "GPT-4o mini",
  "level": "L1",
  "gateway": true,
  "gateway_l2_experimental": false
}
```

Rules:

```text
one target = one model + one SCDL level
same model with L1 and L2 = two targets
```

Do not use one target with `levels: ["L1", "L2"]` as the canonical storage/execution model.

### 2. Field definitions

Document:

```text
ai_family = product UI family, e.g. chatgpt/gemini/claude/grok/perplexity
execution_provider = actual API executor, e.g. openai/openrouter/mock
model_provider = model vendor/family derived from model_id, e.g. openai/anthropic/google
model_id = executable model id
display_name = frontend label
level = L1 or L2
gateway = whether execution_provider is a gateway
gateway_l2_experimental = true only for experimental gateway L2
```

### 3. Backward compatibility

Document temporary legacy support:

```text
legacy providers[] and audit-level scdl_level remain accepted temporarily
backend converts legacy inputs into canonical model_targets
existing legacy audits remain readable
frontend can migrate gradually
```

### 4. Scheduling rule

Document:

```text
audit runs = seed_queries × audit_targets
```

Example:

```text
20 queries × 6 targets = 120 provider calls
```

### 5. Caps and estimates

Document required limits:

```text
MAX_AUDIT_TARGETS
MAX_MODELS_PER_AUDIT
MAX_QUERIES_PER_AUDIT
MAX_TOTAL_RUNS_PER_AUDIT
```

Frontend should show a run-count estimate before save/start.

### 6. Matrix mapping

Document:

```text
answer matrix columns = audit_targets
answer matrix rows = seed_queries
answer matrix cells = query × target run/result
```

### 7. Provider execution rule

Document explicitly:

```text
target.model_id is the model that must be sent to the execution provider for that run.
Provider adapters/factories must not ignore target.model_id and silently use only global L1/L2 model config when target.model_id is present.
```

Global provider config may be used as a fallback only for legacy audits or explicitly configured default targets.

---

## Testing plan to document

Document tests needed in later tasks:

```text
legacy providers[] converted to model_targets
new model_targets accepted
one model L1+L2 becomes two targets
jobs scheduled as queries × targets
target_id saved on runs/results
target.model_id drives provider request model payload
two same-level targets with different model_id values produce different provider requests
caps reject excessive audits
run-count estimate correct
legacy audit detail safe
OpenRouter gateway metadata preserved
```

---

## Acceptance criteria

- Audit target contract documented.
- One-target-per-model-level rule documented.
- Field meanings documented.
- Legacy compatibility documented.
- Scheduling rule documented.
- Provider execution model_id rule documented.
- Caps and run estimate documented.
- Matrix mapping documented.
- Testing plan documented.
- No runtime code changed.

---

## Escalate if

- Existing project docs already define a conflicting canonical target model.
- Current provider architecture cannot accept a per-run model id without broad refactor.
- Product owner wants one target with `levels[]` instead of one target per level.

---

## Commands

Documentation-only task.

Optional:

```bash
# only if markdown linting exists
markdownlint docs/AUDIT_TARGETS_CONTRACT.md
```

Do not run backend/frontend test suites for this task.

---

## Done means

`docs/AUDIT_TARGETS_CONTRACT.md` or equivalent project docs clearly define canonical audit targets, legacy compatibility, scheduling, caps, matrix mapping, and the target.model_id execution rule.

---

## Non-goals

- Do not add DB model.
- Do not update API runtime.
- Do not update scheduler.
- Do not update frontend.
- Do not change provider adapters.
- Do not fix unrelated legacy failures.
