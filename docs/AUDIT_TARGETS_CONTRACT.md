# Audit Targets Contract

## Purpose

This document defines the canonical audit target contract for multi-model and
multi-level audits.

The canonical model replaces the legacy execution shape:

```text
providers[] + audit-level scdl_level
```

with a target-based shape:

```text
one audit target = one model at one SCDL level
```

This contract is the source of truth for later storage, API, scheduler,
frontend, fixture, and verification tasks.

## Canonical Target Shape

A single target is represented as:

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

Do not store or execute one target with `levels: ["L1", "L2"]`.

## Field Definitions

`target_id`
: Stable target identity within an audit. Database-backed targets may use a
  numeric id; draft/UI targets may use a temporary string id.

`ai_family`
: Product UI family such as `chatgpt`, `gemini`, `claude`, `grok`, or
  `perplexity`. This is for grouping and display, not necessarily the executor.

`execution_provider`
: Actual API executor used by the worker, such as `openai`, `openrouter`, or
  `mock`.

`model_provider`
: Model vendor or family derived from `model_id`, such as `openai`,
  `anthropic`, or `google`.

`model_id`
: Executable model id sent to the execution provider for this target.

`display_name`
: Frontend label shown to users.

`level`
: SCDL level. Allowed values are `L1` and `L2`.

`gateway`
: Whether `execution_provider` is a gateway that routes to another model
  provider.

`gateway_l2_experimental`
: `true` only when an L2 target is executed through an experimental gateway web
  search path. It must be `false` for L1.

## SCDL Levels

SCDL remains fixed:

```text
L1 = AI answer without web access
L2 = AI answer with web access
```

Do not introduce additional levels without a product contract update.

## Backward Compatibility

Legacy audit input remains temporarily supported:

```json
{
  "providers": ["mock"],
  "scdl_level": "L1"
}
```

Compatibility rules:

```text
legacy providers[] and audit-level scdl_level remain accepted temporarily
backend converts legacy inputs into canonical model_targets
existing legacy audits remain readable
frontend can migrate gradually
```

When canonical `model_targets` are present, they are the source of truth. A
request that mixes canonical `model_targets` with legacy `providers` or
audit-level `scdl_level` should be rejected by create/update APIs once those APIs
support canonical targets, because mixed payloads create two sources of truth.

## Scheduling Rule

Audit scheduling expands seed queries across audit targets:

```text
audit runs = seed_queries x audit_targets
```

Example:

```text
20 queries x 6 targets = 120 provider calls
```

The scheduler must not collapse targets that share the same level or execution
provider. Two same-level targets with different `model_id` values represent two
distinct provider calls per query.

## Provider Execution Rule

`target.model_id` is the model that must be sent to the execution provider for
that run.

Provider adapters, factories, and workers must not ignore `target.model_id` and
silently use only global L1/L2 model config when `target.model_id` is present.

Global provider config may be used only for:

```text
legacy audits without persisted targets
explicitly configured default targets
test/mock provider paths where model_id is intentionally irrelevant
```

For gateway providers such as OpenRouter, `execution_provider` identifies the
gateway, while `model_id` identifies the routed model. The provider request
payload must contain the target model id.

## Caps and Estimates

The backend must define and enforce caps before audits can create accidental
large run sets:

```text
MAX_AUDIT_TARGETS
MAX_MODELS_PER_AUDIT
MAX_QUERIES_PER_AUDIT
MAX_TOTAL_RUNS_PER_AUDIT
```

Frontend should show a run-count estimate before save/start.

The canonical estimate is:

```text
estimated_runs = effective_query_count x target_count
```

Model count is distinct from target count. The recommended unique model key is:

```text
execution_provider + model_id
```

Example:

```text
same model L1+L2 = target_count 2, model_count 1
two models L1 = target_count 2, model_count 2
```

## Matrix Mapping

The future answer matrix maps queries to targets:

```text
answer matrix rows = seed_queries
answer matrix columns = audit_targets
answer matrix cells = query x target run/result
```

Each cell represents the run/result for one query against one target.

## Result Metadata

Result/status APIs should expose safe target metadata additively:

```text
target_id
ai_family
execution_provider
model_provider
model_id
display_name
level
gateway
gateway_l2_experimental
```

Do not expose raw provider responses, prompts, headers, API keys, or raw request
payloads through frontend-facing DTOs.

## Testing Plan

Later implementation tasks must cover:

```text
legacy providers[] converted to model_targets
new model_targets accepted
one model L1+L2 becomes two targets
jobs scheduled as queries x targets
target_id saved on jobs/runs/results
target.model_id drives provider request model payload
two same-level targets with different model_id values produce different provider requests
caps reject excessive audits
run-count estimate correct
legacy audit detail safe
OpenRouter gateway metadata preserved
```

## Non-Goals

This document does not implement runtime behavior. It does not add a database
model, API endpoint, scheduler change, frontend selector, provider adapter
change, or verification fixture.
