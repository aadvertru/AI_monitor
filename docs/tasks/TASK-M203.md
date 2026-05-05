# TASK-M203 — Update Audit Create/Update/Detail DTOs for Model Targets

## Status

Ready for implementation after TASK-M202.

## Goal

Update audit API contracts so create/update/detail can use canonical `model_targets`.

Preserve temporary backward compatibility for legacy `providers[]` and audit-level `scdl_level`.

---

## Dependencies

Requires:

```text
TASK-M201
TASK-M202
```

---

## Scope

Implement:

```text
model_targets input DTO
model_targets output DTO
create audit support
update audit support if edit exists
detail/list response support where needed
legacy providers[] compatibility
task-scoped backend/API tests
```

Do not update scheduler/pipeline yet.

---

## Canonical input

Accept wire payload:

```json
{
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

### Rules

- Each target is one model + one level.
- Same model L1+L2 appears as two targets.
- Duplicate targets are rejected or deduplicated according to project validation convention.
- Recommended: reject duplicate targets with 422.
- `gateway_l2_experimental=true` only for L2.
- Validate required fields.

---

## Legacy compatibility

Existing input may include:

```json
{
  "providers": ["mock"],
  "scdl_level": "L1"
}
```

Backend should convert this into equivalent canonical target(s) internally.

Required behavior:

```text
if model_targets present, use model_targets
if only legacy providers/scdl_level present, convert to model_targets
if both model_targets and legacy providers/scdl_level are present, return 422
```

Rejecting mixed payloads avoids two sources of truth.

---

## Output

Audit detail should include:

```json
{
  "model_targets": [...]
}
```

Legacy fields may remain:

```json
{
  "providers": ["openrouter"],
  "scdl_level": "L1"
}
```

but should be considered derived/backward-compatible.

---

## Tests

Backend/API tests:

```text
create audit with model_targets succeeds
create audit with same model L1+L2 creates two targets
missing required target fields rejected
invalid level rejected
gateway_l2_experimental true for L1 rejected
duplicate targets rejected with 422
legacy providers/scdl_level still accepted
both model_targets and legacy providers rejected with 422
detail returns model_targets in snake_case wire shape
legacy derived fields still safe if returned
ownership/auth unchanged
```

---

## Acceptance criteria

- Audit create/update can accept `model_targets`.
- Audit detail returns `model_targets`.
- Legacy providers/scdl_level still works.
- Mixed canonical+legacy payload returns 422.
- Required validation implemented.
- Existing audit flows not broken.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

---

## Escalate if

- Current API contract cannot reject mixed payloads without breaking existing frontend.
- Existing tests depend on mixed payload behavior.
- Legacy provider conversion cannot identify model_id safely.
- Update audit behavior differs significantly from create audit behavior.

## Commands

Use task-scoped commands. Adjust exact paths to the repository layout.

Suggested backend checks:

```bash
pytest <task-specific tests>
ruff check <touched backend files>
```

Do not run or fix unrelated full-suite legacy failures inside this task.


## Done means

Backend accepts and returns canonical wire field `model_targets`, preserves legacy compatibility, rejects ambiguous mixed payloads, and passes task-scoped API tests.

---

## Non-goals

- Do not update job scheduling.
- Do not update frontend selector.
- Do not implement model catalog.
- Do not change parser/scoring.
- Do not fix unrelated legacy failures.
