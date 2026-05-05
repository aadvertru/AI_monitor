# TASK-M205 — Expose Target Metadata on Results and Status DTOs

## Status

Ready for implementation after TASK-M204.

## Goal

Ensure audit results/status APIs can expose safe target metadata needed for matrix results, summaries, source aggregation, and diagnostics.

This task owns result/status DTO exposure and safe serialization.

---

## Dependencies

Requires:

```text
TASK-M201
TASK-M202
TASK-M203
TASK-M204
```

---

## Scope

Implement:

```text
result/status DTO target metadata exposure
safe target metadata serialization
legacy result/status compatibility
task-scoped backend/API tests
```

Boundary:

```text
M204 owns scheduling + job/run identity.
M205 owns result/status DTO exposure and safe serialization.
```

Do not change scheduling in this task unless a small bug prevents DTO exposure tests from passing.

---

## Required metadata

Results/status APIs should be able to expose or join:

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

Prefer joining to AuditTarget rather than duplicating all fields, unless snapshots are already project convention.

---

## Rules

- Existing provider diagnostics remain safe.
- Existing results endpoint remains backward compatible.
- Legacy runs without target_id must not crash.
- OpenRouter gateway metadata must be preserved.
- Parser/scoring should not parse raw provider payloads.
- Do not expose raw provider responses or prompts.
- Do not expose provider API keys or headers.

---

## Tests

Backend/API tests:

```text
run/result with target_id can resolve target metadata
result DTO includes target_id and safe target metadata where required
status/result endpoints remain backward compatible
legacy run without target_id safe
OpenRouter L1 metadata present
OpenRouter L2 metadata includes gateway_l2_experimental=true
OpenAI native metadata gateway=false
mock provider metadata safe
failed run includes safe provider_error and target metadata
no raw provider response exposed
no raw prompt exposed
```

---

## Acceptance criteria

- Results/status APIs can expose target identity safely.
- Legacy runs safe.
- Existing API behavior not broken.
- OpenRouter gateway metadata available for future matrix/summary UI.
- No raw provider response/prompt/secrets exposed.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

---

## Escalate if

- Existing result DTOs cannot be extended additively without breaking current frontend.
- Legacy runs have no reliable way to derive safe fallback target metadata.
- Adding metadata requires changing parser/scoring outputs.

## Commands

Use task-scoped commands. Adjust exact paths to the repository layout.

Suggested backend checks:

```bash
pytest <task-specific tests>
ruff check <touched backend files>
```

Do not run or fix unrelated full-suite legacy failures inside this task.


## Done means

Target metadata is safely serializable from result/status APIs, legacy runs do not crash, and existing endpoints remain backward compatible.

---

## Non-goals

- Do not implement matrix endpoint.
- Do not change scheduling except tiny bug fix if required.
- Do not change scoring.
- Do not implement frontend.
- Do not fix unrelated legacy failures.
