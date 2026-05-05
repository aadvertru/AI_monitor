# TASK-W205 — Implement Matrix Cell Expand Details with Safe Answer Source

## Status

Ready for implementation.

## Goal

Implement expand details for answer matrix cells using safe normalized answer data only.

Expanded view must never display raw provider payloads.

## Dependencies

Requires:

```text
TASK-W204
answer matrix DTO with safe answer/excerpt fields
or safe result detail endpoint
```

## Safe full answer requirement

The expanded view may show full answer only if it comes from a safe normalized field:

```text
cell.safe_answer_text
cell.answer_text
or GET /audits/{id}/results/{run_id} returning normalized answer_text
```

The source endpoint/field must be proven not to expose:

```text
raw_response
raw_prompt
raw_tool_result
raw_annotations
headers
API keys
```

If no safe full-answer field/endpoint exists, show only `answer_excerpt` and escalate for backend safe-answer endpoint/task.

## Scope

Implement:

```text
cell expand button
details panel/modal/drawer
safe answer/excerpt display
evaluation details
provider/model/level metadata
sources summary
concepts/competitors summary if present
task-scoped frontend tests
```

## Detail content

Show:

```text
query text
model/target label
level
status
safe answer text or excerpt
evaluation verdict
evaluation rationale
confidence
provider diagnostic if failed
source count / safe source links if available
concepts/competitors if present
```

## Safety tests

Use mocked detail/cell data containing unsafe fields and assert they are not rendered:

```text
raw_response
raw_prompt
raw_tool_result
raw_annotations
headers
authorization
api_key
OPENAI_API_KEY
OPENROUTER_API_KEY
stack_trace
traceback
```

## Tests

Frontend tests:

```text
expand opens details
details show query/model/level
details show safe answer/evaluation
if safe full answer missing, excerpt-only behavior works or task escalates
failed cell details show provider diagnostic
close works
keyboard accessible if component supports it
unsafe fields not rendered
```

## Acceptance criteria

- Cell expand details implemented.
- Full answer shown only from safe normalized source.
- If no safe source exists, task escalates rather than using raw provider payload.
- Evaluation details displayed.
- Provider diagnostics displayed safely.
- No raw provider data exposed.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- No safe normalized full-answer field or endpoint exists.
- Existing result detail endpoint exposes raw provider payloads.
- Product requires full answer display before backend safe endpoint exists.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <matrix cell expand tests>
```

## Done means

Expanded cells show safe normalized details only, with tests proving raw provider fields are ignored.
