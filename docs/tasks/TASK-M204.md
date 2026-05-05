# TASK-M204 — Update Job Scheduling for Query × AuditTarget Runs

## Status

Ready for implementation after TASK-M203.

## Goal

Update audit job scheduling so jobs/runs are created for every seed query × audit target.

This task owns scheduling and job/run identity.

It must also ensure the provider execution handoff uses the target model metadata, including `target.model_id`.

---

## Dependencies

Requires:

```text
TASK-M201
TASK-M202
TASK-M203
```

---

## Scope

Implement:

```text
scheduler target expansion
target_id on jobs/runs
provider execution input populated from AuditTarget
legacy fallback target generation
task-scoped backend tests
```

Boundary:

```text
M204 owns scheduling + job/run identity + provider execution input handoff.
M205 owns result/status DTO exposure and safe serialization.
```

Do not redesign provider adapters unless the current executor ignores per-target model metadata. If it does, update only the minimal executor/factory handoff needed to pass target model_id into provider calls.

---

## Scheduling rule

For every audit:

```text
runs = seed_queries × audit_targets
```

Example:

```text
3 queries × 4 targets = 12 runs
```

Each scheduled job/run must know:

```text
audit_id
query_id or query text reference
target_id
execution_provider
model_id
model_provider
level
gateway
gateway_l2_experimental
```

---

## Legacy behavior

If audit has no audit_targets but has legacy providers/scdl_level:

```text
derive temporary canonical targets for scheduling
```

This ensures old audits can still run.

---

## Target metadata handoff

Provider execution input must be populated from the target:

```text
execution_provider = target.execution_provider
model_id = target.model_id
model_provider = target.model_provider
level = target.level
gateway = target.gateway
gateway_l2_experimental = target.gateway_l2_experimental
```

Do not infer these from global audit fields if target data exists.

Do not silently use global provider config model when `target.model_id` is present.

Global L1/L2 provider config may be used only for:

```text
legacy fallback targets
explicit default targets
test/mock provider paths where model_id is intentionally irrelevant
```

---

## Required model_id execution tests

Add explicit tests proving target model_id drives provider requests:

```text
two L1 targets with same execution_provider=openrouter but different model_id values create two runs
provider executor receives first model_id for first target
provider executor receives second model_id for second target
mocked OpenRouter client/request payload contains different model values
runs are not collapsed by level/provider
no fallback to OPENROUTER_L1_MODEL when target.model_id is present
```

Example target pair:

```text
target A: level=L1, model_id=openai/gpt-4o-mini
target B: level=L1, model_id=anthropic/claude-3-5-sonnet
```

Expected provider request models:

```text
openai/gpt-4o-mini
anthropic/claude-3-5-sonnet
```

---

## Tests

Backend tests:

```text
1 query × 1 target schedules 1 run
2 queries × 3 targets schedules 6 runs
same model L1+L2 schedules two target runs per query
two same-level targets with different model_id values schedule distinct runs
target_id saved on job/run
legacy audit schedules using converted target
duplicate scheduling prevented if scheduler rerun
OpenRouter target metadata passed to provider factory/executor
OpenRouter provider request payload uses target.model_id
OpenAI target metadata passed correctly
global provider model config is not used when target.model_id exists
```

---

## Acceptance criteria

- Scheduler creates runs by query × target.
- target_id is stored on jobs/runs.
- Legacy audits still schedule.
- Duplicate scheduling avoided.
- Provider execution receives target metadata.
- Provider request model payload uses target.model_id.
- Same-level targets with different model_id values do not collapse.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Escalate if

- Current provider adapter interface cannot accept per-run model_id without broad refactor.
- Current OpenRouter adapter always reads only `OPENROUTER_L1_MODEL`/`OPENROUTER_L2_MODEL` and cannot be overridden per target.
- Scheduling and provider execution are too tightly coupled to change safely in one task.
- The change would require modifying unrelated scoring/parser logic.

## Commands

Use task-scoped commands. Adjust exact paths to the repository layout.

Suggested backend checks:

```bash
pytest <task-specific tests>
ruff check <touched backend files>
```

Do not run or fix unrelated full-suite legacy failures inside this task.


## Done means

Scheduler creates query × target runs, preserves target_id, and mocked provider requests prove target.model_id controls the actual model payload for same-level multi-model audits.

---

## Non-goals

- Do not implement frontend selector.
- Do not redesign pipeline broadly.
- Do not change parser/scoring.
- Do not implement model catalog.
- Do not expose result/status DTO target metadata; that is M205.
- Do not fix unrelated legacy failures.
