# TASK-N207 — Add Backend Run Estimate Integration to Audit Target Selector

## Status

Ready for implementation.

## Goal

Show a run-count estimate while configuring an audit using the backend `POST /audits/estimate` endpoint.

## Dependencies

Requires:

```text
TASK-M206 — POST /audits/estimate
TASK-N206 — selector integrated with create/edit
```

## Scope

Implement:

```text
frontend estimate API client/hook
selector/form integration
debounced or explicit estimate request
over-cap warning display
task-scoped frontend tests
```

## Decision

Use backend endpoint:

```http
POST /audits/estimate
```

Do not rely solely on local frontend estimate for cap warnings.

Frontend may show a local optimistic estimate, but backend estimate response is authoritative.

## Request

Send draft audit payload using backend wire shape:

```json
{
  "seed_query_items": [],
  "model_targets": []
}
```

Do not send camelCase `modelTargets` in estimate request body.

## Display

Show:

```text
This audit will run 40 checks.
```

If backend returns cap violations:

```text
show warning/error from safe violation messages
block save/start according to backend validation behavior
```

## Tests

Frontend tests:

```text
estimate client calls POST /audits/estimate
request body uses model_targets
request body does not contain modelTargets
estimate updates when queries change
estimate updates when selected targets change
same model L1+L2 counts two targets
over-cap warning shown from backend response
backend estimate error shown safely
save still relies on backend create validation
```

## Acceptance criteria

- Frontend calls `POST /audits/estimate`.
- Estimate request uses wire `model_targets`.
- Estimate updates with queries/targets.
- Over-cap warnings displayed from backend response.
- Backend remains source of truth.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- `POST /audits/estimate` is not implemented.
- Backend estimate payload differs from audit create payload.
- Estimate calls cause unacceptable UI performance and need debouncing/rate limiting.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <audit estimate UI tests>
```

## Done means

The create/edit form uses backend estimate data and cap warnings, with tests proving the wire payload shape.
