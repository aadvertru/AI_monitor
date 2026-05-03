# Phase H — Frontend Pipeline Integration Tasks

This file contains tasks for connecting the completed backend audit pipeline to the user-facing frontend flow.

Important architectural rule:
- Normal user-facing frontend code must use the authenticated owner endpoint.
- Normal user-facing frontend code must not use `/dev/...` pipeline endpoints.
- The dev/admin endpoint, if present, remains internal tooling only.

Current expected owner endpoint:

```text
POST /audits/{id}/run-pipeline
```

---

## TASK-146 — Add authenticated owner pipeline run endpoint

### Status
Ready

### Goal
Add a user-facing authenticated backend endpoint that runs the full audit pipeline for one audit owned by the current user.

### Why
The Start audit button must be available to regular authenticated users, but it should not call the dev/admin-only pipeline endpoint. The product needs a clean user-facing API contract with ownership checks, guardrails, and safe response output.

### Context
A dev/admin pipeline endpoint may already exist for internal verification. That endpoint must remain restricted. This task adds a separate user-facing endpoint for normal authenticated audit owners.

Expected route:

```text
POST /audits/{id}/run-pipeline
```

Expected behavior:

```text
authenticated user
→ ownership guard
→ real-provider/mock guardrails
→ run full audit pipeline
→ return safe pipeline summary
```

This endpoint may run synchronously for MVP/pilot use. If execution time becomes too long, background workers can be introduced later as a separate task.

### Scope
- Add a user-facing pipeline run endpoint:
  - `POST /audits/{id}/run-pipeline`
  - or project-equivalent non-dev route.
- Require authentication.
- Enforce audit ownership for regular users.
- Allow simple admin access only if the existing `user/admin` model already supports it.
- Reuse the full pipeline service from TASK-141.
- Enforce existing real-provider guardrails and pilot caps.
- Reject cross-user access according to the project’s existing `403` or `404` convention.
- Return a safe structured response, such as:
  - audit id
  - scheduling summary
  - execution summary
  - post-processing summary
  - current/final audit status
  - fatal error, if any
- Ensure response does not include:
  - raw provider answers
  - prompts
  - API keys
  - provider secrets
  - auth cookies
  - sensitive provider metadata
- Handle common errors safely:
  - unauthenticated
  - forbidden/cross-user access
  - audit not found
  - already running or invalid state
  - guardrail/cap rejection
  - fatal pipeline error
- Add API tests for endpoint behavior.
- Document this endpoint as the user-facing MVP pipeline execution API.

### Out of scope
- Do not expose or weaken the dev/admin endpoint.
- Do not remove the dev/admin endpoint if it exists.
- Do not add frontend API client in this task.
- Do not wire the Start audit button in this task.
- Do not add polling in this task.
- Do not introduce background worker/queue infrastructure.
- Do not add billing, quotas, teams, workspaces, or production execution policy.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not expose raw answers or prompts in the response.
- Do not call real OpenAI API in automated tests.

### Acceptance criteria
- `POST /audits/{id}/run-pipeline` or project-equivalent user-facing route exists.
- Unauthenticated requests are rejected.
- Authenticated owner can run the pipeline for their audit.
- Regular user cannot run the pipeline for another user’s audit.
- Simple admin access works only if already supported by the existing auth model.
- Endpoint calls the full pipeline service from TASK-141.
- Endpoint enforces real-provider guardrails and pilot caps.
- Endpoint returns safe pipeline summary.
- Endpoint does not expose raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Already-running or invalid-state audits return a controlled error if supported by the backend state model.
- Existing dev/admin endpoint remains restricted if it exists.
- Existing backend tests still pass.
- Automated tests do not call real OpenAI API.

### Test requirements
- Add API test for unauthenticated rejection.
- Add API test for authenticated owner success path with mocked pipeline service.
- Add API test confirming endpoint calls the full pipeline service.
- Add API test for cross-user access rejection.
- Add API test for missing audit behavior.
- Add API test for already-running or invalid-state behavior if supported.
- Add API test for guardrail/cap rejection if pipeline service exposes that error.
- Add test confirming response does not include raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Add regression test confirming dev/admin endpoint remains restricted if it exists.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...pipeline...`
- `apps/api/...dependencies...`
- `apps/api/...schemas...`
- `tests/...api...`
- `tests/...pipeline...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend API tests for audit pipeline endpoint
- backend auth/access-control tests
- backend pipeline tests affected by endpoint integration
- backend lint/typecheck commands if available

### Dependencies
- TASK-141 — Add full audit pipeline service
- TASK-143 — Stabilize audit status transitions
- TASK-145 — Add dev/admin endpoint to run full audit pipeline, if present

### Escalate if
- Existing pipeline service is too slow for synchronous request/response execution.
- Backend has no consistent ownership guard for audit endpoints.
- The project has not chosen `403` versus `404` for cross-user access.
- Product requires this endpoint to behave asynchronously.
- Returning a useful response would require exposing raw provider answers or prompts.
- Real-provider guardrails cannot be enforced from this endpoint.
- Implementing this task requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary explains why this endpoint is separate from the dev/admin endpoint.
- PR summary confirms ownership enforcement.
- PR summary confirms response is safe for regular authenticated users.
- PR summary confirms no real OpenAI API calls are made in automated tests.

---

## TASK-147 — Add frontend API client for owner pipeline run

### Status
Ready

### Goal
Add a typed frontend API client method for starting the full audit pipeline through the authenticated owner endpoint.

### Why
The Start audit button needs a stable frontend API method that calls the user-facing backend route, not the dev/admin-only endpoint.

### Context
TASK-146 added the authenticated owner pipeline endpoint:

```text
POST /audits/{id}/run-pipeline
```

The frontend must call this user-facing endpoint with credentials, handle safe pipeline responses, and normalize common API errors before any UI wiring is added.

### Scope
- Add a typed frontend API method for starting pipeline execution by audit id.
- Use the shared frontend API client.
- Call the user-facing owner endpoint:
  - `POST /audits/{id}/run-pipeline`
  - or the project-equivalent route from TASK-146.
- Ensure request uses credentialed auth through the shared client:
  - `credentials: "include"` or project-equivalent behavior.
- Add or update TypeScript type for pipeline response, for example:
  - `AuditPipelineRunResponse`
- Response type should safely include available fields such as:
  - audit id
  - scheduling summary
  - execution summary
  - post-processing summary
  - current/final audit status
  - fatal error, if any
- Normalize and expose predictable frontend errors for:
  - `401` unauthenticated
  - `403` forbidden / cross-user access / guardrail rejection
  - `404` audit not found
  - `409` already running or invalid state, if backend uses it
  - `500` unexpected server error
- Add tests with mocked responses.
- Do not wire this method into UI yet.

### Out of scope
- Do not call `/dev/audits/{id}/run-pipeline` from normal frontend code.
- Do not wire the Start audit button in this task.
- Do not add polling in this task.
- Do not change backend endpoint behavior in this task.
- Do not call real OpenAI API in frontend tests.
- Do not expose raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Do not add billing, quotas, teams, workspaces, or production execution policy.
- Do not add background worker UI.

### Acceptance criteria
- Frontend has a typed API method for starting the owner audit pipeline.
- API method calls the user-facing owner endpoint, not the dev/admin endpoint.
- API method uses the shared API client.
- API method sends credentialed requests.
- API method returns typed safe pipeline response data.
- API method handles `401`, `403`, `404`, `409`, and `500` using the project’s standard frontend error shape.
- Tests cover success response.
- Tests cover forbidden/guardrail response.
- Tests cover not-found response.
- Tests cover already-running/invalid-state response if supported by backend contract.
- Tests cover server-error response.
- Tests confirm no raw answers, prompts, or secrets are expected in the response type.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add API client test for successful pipeline start response.
- Add test confirming credentialed request behavior.
- Add test confirming the route is the owner endpoint and not a `/dev/...` endpoint.
- Add test for `401` unauthenticated handling.
- Add test for `403` forbidden, cross-user, or guardrail rejection.
- Add test for `404` audit not found.
- Add test for `409` already running or invalid state if supported by backend contract.
- Add test for `500` server error handling.
- Add type-level or runtime assertion that the response does not include raw provider answer fields.
- Add regression assertion that no token/JWT is stored in `localStorage` or `sessionStorage`.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/lib/api...`
- `apps/web/src/types...`
- `apps/web/src/features/audits...`
- `apps/web/src/test...`
- `apps/web/src/test/fixtures...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- frontend tests
- frontend typecheck
- frontend lint
- frontend build

### Dependencies
- TASK-146 — Add authenticated owner pipeline run endpoint

### Escalate if
- Backend endpoint path differs from the expected owner route.
- Backend response shape is undocumented or differs from frontend types.
- Backend only exposes a dev/admin endpoint.
- Backend does not distinguish forbidden, not found, already running, and fatal errors.
- API response contains raw answers, prompts, secrets, or provider metadata that should not be exposed.
- Starting the pipeline from the frontend requires a background worker or long-running request decision not yet made.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary states the exact backend route used by the frontend client.
- PR summary confirms the method is not wired into UI yet.
- PR summary confirms the request is credentialed.
- PR summary confirms no `/dev/...` endpoint is used by normal frontend code.
- PR summary confirms no raw answers or secrets are exposed by the frontend type.

---

## TASK-148 — Wire Start audit button to owner pipeline endpoint

### Status
Ready

### Goal
Connect the user-facing Start audit button to the authenticated owner pipeline endpoint.

### Why
Users should be able to start their own audit from the UI without using CLI commands or dev/admin endpoints.

### Context
TASK-146 added the user-facing backend endpoint:

```text
POST /audits/{id}/run-pipeline
```

TASK-147 added the typed frontend API client method for this endpoint.

This task wires the existing Start audit action in the audit UI to the owner pipeline API method.

### Scope
- Locate the current Start audit button/action in the audit detail, summary, or project-equivalent audit page.
- Replace old/manual/schedule-only start behavior with the owner pipeline API method from TASK-147.
- Ensure normal frontend code does not call `/dev/...` pipeline endpoints.
- Disable the Start audit button while the pipeline request is in flight.
- Show a clear loading/running state while the request is pending.
- On successful response:
  - show success or running/completed state according to returned status
  - invalidate/refetch relevant TanStack Query caches:
    - audit detail
    - audit status
    - audit summary
    - audit results
    - audit sources, if separate
    - audit list/dashboard, if status appears there
- On error:
  - show clear user-facing error message
  - handle unauthenticated state according to existing auth flow
  - handle forbidden/ownership/guardrail rejection
  - handle audit not found
  - handle already-running/invalid-state response if supported
  - handle unexpected server error
- Prevent duplicate rapid submissions.
- Add tests for button behavior and cache invalidation.

### Out of scope
- Do not add polling in this task.
- Do not add progress bar or detailed pipeline progress UI.
- Do not add background worker/queue infrastructure.
- Do not change backend endpoint behavior.
- Do not call dev/admin endpoint from normal frontend code.
- Do not expose raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Do not add billing, teams, workspaces, or production quota UI.
- Do not redesign the audit detail page.

### Acceptance criteria
- Start audit button calls the owner pipeline API method from TASK-147.
- Start audit button does not call any `/dev/...` endpoint.
- Button is disabled while request is pending.
- Duplicate rapid submissions are prevented.
- Successful pipeline response invalidates/refetches relevant audit queries.
- UI reflects returned status safely.
- Forbidden/ownership/guardrail errors are displayed clearly.
- Not-found and server-error states are displayed clearly.
- Existing protected route behavior remains unchanged.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for clicking Start audit calls owner pipeline API method.
- Add test confirming `/dev/...` endpoint is not used by the Start audit action.
- Add test confirming button is disabled while request is pending.
- Add test confirming duplicate click does not trigger duplicate requests.
- Add test confirming success invalidates/refetches audit detail/status/summary/results caches where practical.
- Add test for forbidden/guardrail error display.
- Add test for not-found error display if supported by test setup.
- Add test for server-error display.
- Add test confirming no raw answers or secrets are rendered after response.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/detail...`
- `apps/web/src/features/audits/status...`
- `apps/web/src/features/audits/summary...`
- `apps/web/src/features/audits/results...`
- `apps/web/src/lib/api...`
- `apps/web/src/test...`
- `apps/web/src/test/fixtures...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- frontend tests
- frontend typecheck
- frontend lint
- frontend build

### Dependencies
- TASK-146 — Add authenticated owner pipeline run endpoint
- TASK-147 — Add frontend API client for owner pipeline run

### Escalate if
- There is no single clear Start audit button/action.
- The Start audit UI currently depends on the old schedule-only endpoint in a way that cannot be safely replaced.
- Backend pipeline endpoint is too slow for synchronous request/response and requires a background worker decision.
- Returned status shape differs from frontend types.
- Cache keys for audit detail/status/summary/results are inconsistent or duplicated.
- Product requires detailed progress UI before pipeline integration.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary states which UI action was wired.
- PR summary confirms the owner endpoint is used.
- PR summary confirms `/dev/...` endpoint is not used by normal frontend code.
- PR summary lists which TanStack Query caches are invalidated/refetched.

---

## TASK-149 — Add audit status polling after pipeline start

### Status
Ready

### Goal
Add frontend polling after audit pipeline start so audit status, summary, results, and sources refresh automatically until the audit reaches a terminal state.

### Why
After the user starts an audit, the UI should update without requiring manual refresh. Polling gives the MVP a simple feedback loop before introducing background workers, websockets, or a more advanced progress system.

### Context
TASK-146 added the authenticated owner backend endpoint for running the pipeline. TASK-147 added the frontend API client method. TASK-148 wired the Start audit button to the owner endpoint and invalidated relevant query caches after start.

This task adds polling to keep the UI fresh while audit status is `running`.

Terminal audit statuses:

```text
completed
partial
failed
```

Non-terminal statuses may include:

```text
created
running
```

### Scope
- Add polling/refetch behavior for audit status after pipeline start.
- Use TanStack Query polling/refetch intervals or the project-equivalent pattern.
- Poll while audit status is `running`.
- Stop polling when audit status becomes:
  - `completed`
  - `partial`
  - `failed`
- After terminal status is reached, refetch or invalidate:
  - audit detail
  - audit status
  - audit summary
  - audit results
  - audit sources, if separate
  - audit list/dashboard, if status appears there
- Ensure polling does not continue indefinitely after terminal status.
- Ensure polling does not start on unrelated audits.
- Ensure polling does not require page reload.
- Handle polling API errors safely.
- Add tests for polling lifecycle behavior.

### Out of scope
- Do not add websocket/SSE support.
- Do not add background worker/queue infrastructure.
- Do not add detailed progress bars unless the backend already exposes progress data and UI already supports it.
- Do not change backend pipeline behavior.
- Do not change audit status values.
- Do not call `/dev/...` endpoints from normal frontend code.
- Do not expose raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Do not add billing/quota UI.
- Do not redesign audit pages.

### Acceptance criteria
- Polling starts after pipeline start or when viewing an audit already in `running` state.
- Polling refetches audit status at a reasonable interval.
- Polling stops when status becomes `completed`.
- Polling stops when status becomes `partial`.
- Polling stops when status becomes `failed`.
- Relevant audit queries are refreshed when a terminal status is reached.
- Polling does not trigger duplicate pipeline starts.
- Polling does not call dev/admin endpoints.
- Polling handles API error states without crashing the page.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test confirming polling starts after successful Start audit action.
- Add test confirming polling starts when audit detail loads with `running` status if applicable.
- Add test confirming polling stops on `completed`.
- Add test confirming polling stops on `partial`.
- Add test confirming polling stops on `failed`.
- Add test confirming summary/results/sources are refetched or invalidated after terminal status.
- Add test confirming polling does not call the pipeline start endpoint repeatedly.
- Add test confirming polling does not call `/dev/...` endpoint.
- Add test for polling API error handling if test setup supports it.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/detail...`
- `apps/web/src/features/audits/status...`
- `apps/web/src/features/audits/summary...`
- `apps/web/src/features/audits/results...`
- `apps/web/src/features/audits/sources...`
- `apps/web/src/lib/api...`
- `apps/web/src/test...`
- `apps/web/src/test/fixtures...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- frontend tests
- frontend typecheck
- frontend lint
- frontend build

### Dependencies
- TASK-146 — Add authenticated owner pipeline run endpoint
- TASK-147 — Add frontend API client for owner pipeline run
- TASK-148 — Wire Start audit button to owner pipeline endpoint

### Escalate if
- Audit status values differ from the expected state model.
- Backend pipeline is synchronous and always returns terminal status, making polling unnecessary or only needed for already-running audits.
- Backend does not expose reliable audit status after pipeline start.
- Query keys are too inconsistent to safely invalidate/refetch.
- Product requires precise progress instead of simple polling.
- Polling creates excessive requests or cost risk.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary states the polling interval used.
- PR summary lists terminal statuses that stop polling.
- PR summary lists which query caches are refreshed after terminal status.
- PR summary confirms polling does not re-trigger the pipeline.

---

## Phase I — Pipeline UX Stabilization

Tasks in this phase must be written only after TASK-146 through TASK-149 are complete and manually tested.

Potential areas:
- duplicate start prevention
- stale cache fixes
- better partial/failed error display
- progress display
- background worker / queue migration
- user-facing execution limits
- cost estimate before run