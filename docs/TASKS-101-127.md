## TASK-101 — Add user model and audit ownership schema

### Status
Ready

### Goal
Add persistent users and connect audits to their owning user.

### Why
Audit data must be associated with a user before authentication and authorization rules can safely restrict access to personal audit results.

### Context
The backend already has SCDL audit storage models and a tested mock-data audit pipeline. This task introduces the minimum user ownership layer required for later auth work. It must not change parser, scoring, provider, raw response, or aggregation contracts.

### Scope
- Add a persistent `User` model.
- Include at least:
  - `id`
  - `email`
  - `hashed_password`
  - `role`
  - `created_at`
  - `updated_at`
- Enforce unique user email at the database/model level according to the existing project pattern.
- Add a relationship from `Audit` to `User`.
- Add `audits.user_id` or the project-equivalent ownership field.
- Add the required migration or schema update using the repository’s existing migration/schema-management approach.
- Ensure existing audit creation/storage behavior remains compatible with current tests.
- Add tests for user persistence and audit ownership.

### Out of scope
- Do not implement registration, login, logout, or `/auth/me`.
- Do not implement JWT handling.
- Do not implement password hashing utilities beyond storing the `hashed_password` field.
- Do not enforce authorization rules yet.
- Do not change parser, scoring, provider, raw response, or aggregation contracts.
- Do not introduce teams, workspaces, organizations, billing, or multi-tenant abstractions.
- Do not add OAuth/social login.

### Acceptance criteria
- A `User` record can be created and persisted.
- User email uniqueness is enforced or validated according to the existing project pattern.
- A user can own multiple audits.
- An audit can be linked to exactly one owning user once ownership is assigned.
- Audits can be queried by `user_id` or the project-equivalent ownership field.
- Existing audit pipeline/storage tests still pass.
- Local/test database setup works after the schema change.

### Test requirements
- Add a test for creating a user with a valid email and hashed password value.
- Add a test for duplicate email behavior.
- Add a test for linking an audit to a user.
- Add a test for querying audits by owner.
- Add a regression test or update an existing audit storage test to confirm existing audit behavior is not broken by the new ownership field.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...models...`
- `apps/api/...schemas...`
- `apps/api/...migrations...`
- `tests/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run the backend test command after implementation.

### Dependencies
- None

### Escalate if
- The repository has no clear database migration or schema update pattern.
- Existing audit tests assume audits cannot have owners.
- Adding `audits.user_id` requires changing parser, scoring, provider, raw response, or aggregation contracts.
- Existing audit creation cannot remain backward-compatible without a product decision.
- The implementation requires introducing teams, workspaces, organizations, or broader multi-tenant design.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-102 — Add password hashing and JWT utilities

### Status
Ready

### Goal
Add backend utilities for password hashing, password verification, JWT creation, JWT verification, and auth cookie configuration.

### Why
Authentication endpoints need one tested security boundary so password and token behavior is consistent across register, login, logout, and current-user flows.

### Context
MVP authentication uses email and password. Passwords must be hashed with bcrypt/passlib or the existing backend-approved equivalent. JWT authentication should preferably use an httpOnly cookie. This task prepares reusable utilities only; it does not expose auth endpoints.

### Scope
- Add password hashing utility.
- Add password verification utility.
- Add JWT creation utility.
- Add JWT verification/decoding utility.
- Add typed token claims structure or project-equivalent schema.
- Add auth cookie configuration helper or constants.
- Add configuration handling for:
  - JWT secret
  - JWT algorithm
  - access token lifetime
  - cookie name
  - cookie `httponly`
  - cookie `secure`
  - cookie `samesite`
- Ensure secrets are read from environment/config and are not hardcoded.
- Add tests for password and JWT utility behavior.

### Out of scope
- Do not implement registration, login, logout, or `/auth/me`.
- Do not implement route dependencies for current user.
- Do not add frontend code.
- Do not store JWT in localStorage.
- Do not implement OAuth/social login.
- Do not implement refresh tokens unless the existing backend already requires them.
- Do not implement CSRF mitigation in this task beyond exposing cookie settings needed for the later policy task.
- Do not change audit models or ownership behavior.

### Acceptance criteria
- Password hashing returns a value different from the plain password.
- Valid password verification succeeds.
- Invalid password verification fails.
- JWT creation includes at least user identifier and role claims, or a documented project-equivalent claim shape.
- Valid JWT verification returns expected claims.
- Invalid JWT verification fails safely.
- Expired JWT verification fails safely.
- Cookie configuration exposes httpOnly behavior.
- JWT secret/config values are not hardcoded in source code.
- Existing backend tests still pass.

### Test requirements
- Add a unit test for hashing and verifying a valid password.
- Add a unit test confirming the plain password is not returned as the hash.
- Add a unit test for rejecting an invalid password.
- Add a unit test for JWT creation and verification roundtrip.
- Add a unit test for invalid token handling.
- Add a unit test for expired token handling if the JWT library/test setup supports deterministic expiry.
- Add a test or assertion for httpOnly cookie configuration.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...auth...`
- `apps/api/...security...`
- `apps/api/...config...`
- `tests/...auth...`
- `tests/...security...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run the backend unit test command after implementation.

### Dependencies
- TASK-101 — Add user model and audit ownership schema

### Escalate if
- The repository has no clear config/environment pattern.
- Required JWT secret handling is undefined.
- Existing dependencies conflict with bcrypt/passlib or the selected password hashing library.
- Cookie-based JWT conflicts with existing CORS/API setup.
- Token claim shape requires a product or security decision.
- The implementation would require adding refresh-token rotation or session storage.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-103 — Define auth cookie, CORS, and CSRF policy

### Status
Ready

### Goal
Define and implement the backend policy for cookie-based JWT auth, credentialed CORS, and CSRF handling for the MVP.

### Why
The frontend will authenticate through httpOnly cookies, so the backend must have explicit rules for browser credentials, allowed origins, cookie security flags, and CSRF risk before auth endpoints are exposed.

### Context
The MVP uses FastAPI as the only backend server and `apps/web` as a Vite SPA. JWT should preferably be stored in an httpOnly cookie. The frontend must be able to call the FastAPI REST API with credentials. This task creates the security and configuration boundary for later auth endpoints.

### Scope
- Define auth cookie policy for:
  - cookie name
  - `HttpOnly`
  - `Secure`
  - `SameSite`
  - path
  - expiration/max-age behavior
- Define CORS policy for credentialed frontend requests.
- Add environment/config support for allowed frontend origins.
- Ensure credentialed requests can be supported without wildcard `Access-Control-Allow-Origin`.
- Define the MVP CSRF position:
  - either document why `SameSite` is sufficient for MVP/local setup
  - or add a minimal CSRF token strategy if the project already has a suitable pattern
- Add tests or configuration tests for CORS/cookie policy where the project test stack supports it.
- Document local development expectations for frontend/backend origin configuration.

### Out of scope
- Do not implement register, login, logout, or `/auth/me`.
- Do not implement user lookup dependencies.
- Do not implement frontend API client code.
- Do not add OAuth/social login.
- Do not add refresh tokens.
- Do not introduce session storage unless explicitly required by existing backend architecture.
- Do not weaken cookie security to make local development work silently.
- Do not use wildcard CORS origin with credentials.

### Acceptance criteria
- Auth cookie settings are defined in one clear backend location.
- Cookie policy includes `HttpOnly`.
- Cookie `Secure` behavior is configurable for local development versus production.
- Cookie `SameSite` behavior is explicitly configured or documented.
- CORS allowed origins are loaded from config/environment.
- Credentialed CORS does not use wildcard origin.
- The frontend origin can be configured for local development.
- CSRF stance is explicitly documented in code comments, config docs, or project docs.
- Existing backend tests still pass.

### Test requirements
- Add a test or assertion confirming auth cookie config includes `HttpOnly`.
- Add a test or assertion confirming wildcard CORS origin is not used with credentials.
- Add a test or assertion confirming allowed origins can be loaded from config/environment.
- Add a test for local-development cookie/CORS config if the project has environment-specific config tests.
- Add a regression test or reviewer-verifiable check that no JWT storage in response body/localStorage is introduced by this task.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...config...`
- `apps/api/...main...`
- `apps/api/...security...`
- `apps/api/...auth...`
- `tests/...config...`
- `tests/...security...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend config/security tests and the backend test command after implementation.

### Dependencies
- TASK-102 — Add password hashing and JWT utilities

### Escalate if
- The frontend origin or deployment origin is unknown and cannot be represented as environment configuration.
- Existing CORS setup conflicts with credentialed cookie auth.
- CSRF requirements are unclear or stricter than SameSite-based MVP protection.
- The implementation requires changing the auth transport away from httpOnly cookies.
- Production cookie settings require a security decision not present in the specs.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-104 — Implement registration endpoint

### Status
Ready

### Goal
Implement `POST /auth/register` for creating a new user account with email and password.

### Why
Users need a backend entry point to create accounts before they can authenticate and own audit data.

### Context
The user model, audit ownership schema, password hashing utilities, JWT utilities, cookie/CORS policy, and CSRF position should already be defined by earlier tasks. This task only adds registration behavior and must not implement the full login/session flow.

### Scope
- Add request schema for registration input.
- Add response schema for safe user output.
- Implement `POST /auth/register`.
- Normalize email according to the existing project pattern.
- Validate required registration fields.
- Hash the submitted password before storing it.
- Store only `hashed_password`, never the plain password.
- Assign default role `user` unless the project already has another safe default.
- Reject duplicate email registration.
- Return safe user data only.
- Add API tests for registration behavior.

### Out of scope
- Do not implement `POST /auth/login`.
- Do not implement `POST /auth/logout`.
- Do not implement `GET /auth/me`.
- Do not create an authenticated session after registration unless existing project requirements explicitly require auto-login.
- Do not set JWT cookies in this task.
- Do not implement password reset.
- Do not implement email verification.
- Do not implement OAuth/social login.
- Do not implement admin user management.
- Do not change audit creation or audit ownership enforcement.

### Acceptance criteria
- `POST /auth/register` creates a new user with valid email and password.
- The stored password value is hashed and is not equal to the plain password.
- Duplicate email registration returns a clear error response.
- Invalid email input is rejected.
- Missing password input is rejected.
- The response does not include `hashed_password` or plain password.
- New users receive the default `user` role.
- Existing backend tests still pass.

### Test requirements
- Add API test for successful registration.
- Add API test confirming plain password is not returned in the response.
- Add database or service-level assertion confirming stored password is hashed.
- Add API test for duplicate email registration.
- Add API test for invalid email input.
- Add API test for missing password input.
- Add API test confirming default role is assigned.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/auth...`
- `apps/api/...schemas/auth...`
- `apps/api/...models/user...`
- `apps/api/...security...`
- `tests/...auth...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend API/auth tests and the backend test command after implementation.

### Dependencies
- TASK-101 — Add user model and audit ownership schema
- TASK-102 — Add password hashing and JWT utilities
- TASK-103 — Define auth cookie, CORS, and CSRF policy

### Escalate if
- Product requirements expect registration to automatically log the user in.
- Existing user schema requires additional mandatory fields not described in the task.
- Email normalization rules are unclear or conflict with existing tests.
- Password policy requirements are stricter than basic required-field validation.
- Duplicate email behavior cannot be implemented without changing the user model or migration.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-105 — Implement login, logout, and current-user endpoints

### Status
Ready

### Goal
Implement `POST /auth/login`, `POST /auth/logout`, and `GET /auth/me` using the existing user model and JWT cookie utilities.

### Why
The frontend needs a complete session flow to authenticate users, end sessions, and identify the current user before rendering protected dashboard pages.

### Context
Registration is handled separately. This task creates the browser session behavior based on email/password credentials and httpOnly JWT cookies. It must use the cookie, CORS, and CSRF policy defined earlier.

### Scope
- Add request schema for login input.
- Add safe response schema for current user output if not already present.
- Implement `POST /auth/login`.
- Verify submitted password against the stored password hash.
- Set JWT auth cookie on successful login.
- Return safe user data only.
- Implement `POST /auth/logout`.
- Clear the JWT auth cookie using the configured cookie settings.
- Implement `GET /auth/me`.
- Decode and validate the JWT from the auth cookie.
- Return the current user when authenticated.
- Return unauthorized response when no valid auth cookie exists.
- Add API tests for login, logout, and current-user behavior.

### Out of scope
- Do not implement registration.
- Do not implement password reset.
- Do not implement email verification.
- Do not implement OAuth/social login.
- Do not implement refresh-token rotation.
- Do not implement complex RBAC.
- Do not implement audit ownership enforcement in this task.
- Do not expose `hashed_password` or password-like fields in any response.

### Acceptance criteria
- `POST /auth/login` accepts valid credentials.
- Successful login sets the configured httpOnly auth cookie.
- Successful login returns safe user data only.
- Login rejects unknown email.
- Login rejects invalid password.
- `GET /auth/me` returns the authenticated user when the JWT cookie is valid.
- `GET /auth/me` returns unauthorized when the cookie is missing, invalid, or expired.
- `POST /auth/logout` clears the auth cookie.
- Existing backend tests still pass.

### Test requirements
- Add API test for successful login.
- Add assertion that successful login sets the auth cookie.
- Add assertion that the auth cookie is httpOnly if the test client exposes cookie attributes.
- Add API test for unknown email login.
- Add API test for invalid password login.
- Add API test for `/auth/me` with a valid cookie.
- Add API test for `/auth/me` without a cookie.
- Add API test for `/auth/me` with invalid or expired token.
- Add API test for logout clearing the cookie.
- Add regression test confirming password/hash fields are never returned.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/auth...`
- `apps/api/...schemas/auth...`
- `apps/api/...dependencies...`
- `apps/api/...security...`
- `tests/...auth...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend API/auth tests and the backend test command after implementation.

### Dependencies
- TASK-102 — Add password hashing and JWT utilities
- TASK-103 — Define auth cookie, CORS, and CSRF policy
- TASK-104 — Implement registration endpoint

### Escalate if
- Cookie-based auth cannot be tested with the existing test client.
- Cookie clearing requires settings that differ from the configured cookie policy.
- Current-user lookup needs a dependency pattern that conflicts with existing FastAPI structure.
- The frontend requires token delivery in response body instead of httpOnly cookie.
- Login should support identifiers other than email.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-106 — Enforce authenticated audit creation ownership

### Status
Ready

### Goal
Require authentication for audit creation and assign each newly created audit to the current user.

### Why
Audit data must have a reliable owner before the service can safely show personal audit lists, details, results, and summaries.

### Context
The backend already has `POST /audits`. Earlier tasks added users, audit ownership schema, and auth endpoints. This task changes audit creation from anonymous creation to authenticated user-owned creation, without changing parser, scoring, provider, raw response, or aggregation contracts.

### Scope
- Add or reuse a current-user dependency for protected routes.
- Protect `POST /audits` so unauthenticated requests are rejected.
- Assign the created audit’s ownership field from the authenticated user.
- Preserve existing audit input validation and normalization behavior.
- Preserve existing audit pipeline behavior after the audit is created.
- Update tests that previously created audits anonymously to authenticate where appropriate.
- Add API tests for authenticated and unauthenticated audit creation.

### Out of scope
- Do not implement audit list/read/status/results/summary endpoints.
- Do not implement admin audit access.
- Do not implement teams, workspaces, organizations, billing, or multi-tenant behavior.
- Do not change parser, scoring, provider, raw response, or aggregation contracts.
- Do not change scoring formulas or audit state transitions.
- Do not add frontend code.

### Acceptance criteria
- Unauthenticated `POST /audits` requests return an unauthorized response.
- Authenticated `POST /audits` requests can create audits.
- Created audits are assigned to the authenticated user.
- Existing audit validation behavior remains unchanged for authenticated requests.
- Existing audit pipeline/storage tests pass after being updated for auth where needed.
- No parser, scoring, provider, raw response, or aggregation contract changes are introduced.

### Test requirements
- Add API test for unauthenticated audit creation rejection.
- Add API test for authenticated audit creation success.
- Add assertion that the created audit has the authenticated user’s ownership field.
- Add regression test or update an existing audit creation test to verify current audit validation behavior still works.
- Add test confirming another user is not assigned as owner accidentally.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...dependencies...`
- `apps/api/...schemas/audits...`
- `tests/...audits...`
- `tests/...auth...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend auth/audit API tests and the backend test command after implementation.

### Dependencies
- TASK-101 — Add user model and audit ownership schema
- TASK-105 — Implement login, logout, and current-user endpoints

### Escalate if
- Existing product requirements still require anonymous audit creation.
- Existing tests or fixtures cannot be updated without changing audit contracts.
- Audit creation currently triggers pipeline execution in a way that cannot safely run under authenticated context.
- Ownership assignment requires a migration/backfill decision not covered by TASK-101.
- The implementation would require changing parser, scoring, provider, raw response, or aggregation behavior.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-107 — Define frontend-facing audit API schemas

### Status
Ready

### Goal
Define stable frontend-facing request and response schemas for audit list, audit detail, audit status, audit results, and audit summary API usage.

### Why
The frontend must consume predictable API contracts instead of depending on internal database models, pipeline objects, or aggregation implementation details.

### Context
The existing backend already has SCDL audit models and pipeline components. The frontend will need stable JSON shapes for dashboard/list pages, detail pages, results tables, summary cards, competitors, critical queries, and source intelligence views. This task defines the contract boundary before adding or adjusting the read endpoints.

### Scope
- Define or verify Pydantic response schemas for:
  - audit list item
  - audit detail
  - audit status
  - audit result row
  - audit results response
  - audit summary response
  - competitor summary item
  - source summary item
  - critical query item
- Define or verify request/response schema for triggering an audit run if the backend supports a run trigger endpoint.
- Ensure schemas expose only frontend-safe fields.
- Ensure schemas do not expose raw internal database objects directly.
- Ensure audit result rows support the `query × provider × run` output shape.
- Include fields needed by the UI where available:
  - audit id
  - brand name
  - brand domain
  - status
  - created/updated timestamps
  - provider
  - run number
  - run status
  - brand visibility
  - brand position/rank
  - final score
  - component scores
  - competitors
  - sources
  - raw answer reference, if already supported
- Add schema-level tests or serialization tests using representative audit data.
- Document any intentionally missing fields as not yet available rather than inventing them.

### Out of scope
- Do not implement new audit read endpoints in this task.
- Do not implement frontend code.
- Do not change parser, scoring, provider, raw response, or aggregation contracts.
- Do not add export endpoints.
- Do not add recommendations generation.
- Do not implement SCDL L1/L2 mode if no backend contract exists yet.
- Do not expose sensitive user data, password data, internal provider secrets, or raw credentials.
- Do not expose full raw provider answers unless an existing safe raw-answer endpoint already exists.

### Acceptance criteria
- Frontend-facing audit schemas exist in the backend schema layer or the project-equivalent contract layer.
- Audit list schema contains enough data for the dashboard list.
- Audit detail schema contains enough data for the audit detail header and metadata area.
- Audit status schema represents the current audit state without requiring the frontend to inspect internal jobs.
- Audit results schema can represent per-run rows.
- Audit summary schema can represent completion ratio, visibility ratio, average score, critical query count, competitors, and sources where available.
- Schemas serialize representative audit data without exposing internal ORM objects directly.
- Missing or unavailable optional fields serialize safely.
- Existing backend tests still pass.

### Test requirements
- Add schema serialization test for audit list item.
- Add schema serialization test for audit detail.
- Add schema serialization test for audit status.
- Add schema serialization test for audit result row.
- Add schema serialization test for audit summary.
- Add test for empty results response.
- Add test for partial/failed audit summary shape if representative data is available.
- Add regression test confirming sensitive auth/user fields are not included in audit responses.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...schemas/audits...`
- `apps/api/...schemas/results...`
- `apps/api/...schemas/summary...`
- `tests/...schemas...`
- `tests/...audits...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend schema/API tests and the backend test command after implementation.

### Dependencies
- TASK-106 — Enforce authenticated audit creation ownership

### Escalate if
- Existing aggregation output shape is inconsistent or unavailable.
- Required frontend fields cannot be derived from existing backend data.
- Raw answer references require a new access-control decision.
- SCDL L1/L2 mode needs a schema field but no backend contract exists yet.
- Existing schemas expose ORM models directly and replacing that behavior would exceed this task scope.
- Defining the schema requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-108 — Add audit list and detail endpoints

### Status
Ready

### Goal
Add authenticated `GET /audits` and `GET /audits/{id}` endpoints using the frontend-facing audit schemas.

### Why
The frontend dashboard needs a stable way to list the current user’s audits and open a single audit detail page without reading internal storage structures.

### Context
Audit creation is already authenticated by earlier tasks. Frontend-facing schemas are defined in TASK-107. This task adds only basic read endpoints for audit list and audit detail. Status, results, summary, and run trigger endpoints are separate tasks.

### Scope
- Implement or update `GET /audits`.
- Implement or update `GET /audits/{id}`.
- Use the frontend-facing schemas from TASK-107.
- Enforce authenticated access.
- Return only audits owned by the current user.
- Return admin-visible audits only if simple admin access already exists without complex RBAC.
- Add deterministic ordering for the audit list, such as newest first, unless the project already has a different convention.
- Return a clear not-found or forbidden response when a user requests another user’s audit.
- Add API tests for list and detail behavior.

### Out of scope
- Do not implement `GET /audits/{id}/status`.
- Do not implement `GET /audits/{id}/results`.
- Do not implement `GET /audits/{id}/summary`.
- Do not implement `POST /audits/{id}/run`.
- Do not change audit creation behavior.
- Do not change parser, scoring, provider, raw response, or aggregation contracts.
- Do not add frontend code.
- Do not add complex RBAC, teams, workspaces, or billing.

### Acceptance criteria
- Authenticated user can list their own audits.
- Audit list does not include audits owned by other users.
- Audit list response uses the schema defined in TASK-107.
- Authenticated user can fetch one owned audit by ID.
- Fetching an audit owned by another user is rejected or hidden according to the project’s existing not-found/forbidden convention.
- Unauthenticated requests are rejected.
- Existing backend tests still pass.

### Test requirements
- Add API test for authenticated `GET /audits`.
- Add API test confirming `GET /audits` returns only owned audits.
- Add API test confirming audit list ordering.
- Add API test for authenticated `GET /audits/{id}` on an owned audit.
- Add API test for unauthenticated list/detail rejection.
- Add API test for cross-user audit detail access rejection.
- Add admin visibility test if simple admin access is implemented.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...schemas/audits...`
- `apps/api/...dependencies...`
- `tests/...audits...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend audit API tests and the backend test command after implementation.

### Dependencies
- TASK-106 — Enforce authenticated audit creation ownership
- TASK-107 — Define frontend-facing audit API schemas

### Escalate if
- The project has no convention for cross-user access response: 403 versus 404.
- Existing audit queries cannot filter by owner without a schema or repository change.
- Admin access would require complex RBAC.
- List response pagination is required but not specified.
- Existing route structure conflicts with these endpoint paths.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-109 — Add audit status and run trigger endpoints

### Status
Ready

### Goal
Add authenticated audit status retrieval and audit execution trigger endpoints for owned audits.

### Why
The frontend must let users see whether an audit is created, running, partial, completed, or failed, and must provide a safe way to start the audit pipeline when execution is not automatically triggered.

### Context
The architecture defines audit states as `created`, `running`, `partial`, `completed`, and `failed`. The backend already has parts of the audit pipeline and mock provider execution. This task exposes only the status and trigger boundary; results and summary endpoints are separate tasks.

### Scope
- Implement or update `GET /audits/{id}/status`.
- Implement or update `POST /audits/{id}/run`, or document and test the existing equivalent endpoint if it already exists.
- Use frontend-facing schemas from TASK-107.
- Enforce authenticated access.
- Enforce audit ownership for regular users.
- Return status without exposing internal worker/job implementation details.
- Ensure run trigger uses the existing orchestrator/pipeline entry point where available.
- Prevent unsafe duplicate execution if the audit is already running.
- Add API tests for status and run trigger behavior.

### Out of scope
- Do not implement `GET /audits/{id}/results`.
- Do not implement `GET /audits/{id}/summary`.
- Do not implement frontend polling or UI.
- Do not add a new background job system unless the repository already has one.
- Do not change parser, scoring, provider, raw response, or aggregation contracts.
- Do not call real provider APIs in tests.
- Do not redesign audit state transitions.

### Acceptance criteria
- Authenticated user can retrieve status for an owned audit.
- Unauthenticated status requests are rejected.
- Cross-user status access is rejected or hidden according to the project convention.
- Run trigger starts or requests execution for an owned audit using the existing pipeline path.
- Run trigger rejects or safely no-ops when the audit is already running.
- Run trigger does not call real external providers in automated tests.
- Status response contains a stable frontend-safe state value.
- Existing backend tests still pass.

### Test requirements
- Add API test for `GET /audits/{id}/status` on an owned audit.
- Add API test for unauthenticated status rejection.
- Add API test for cross-user status rejection.
- Add API test for successful run trigger using mock provider or existing mock pipeline.
- Add API test for duplicate run trigger behavior when audit is already running.
- Add API test confirming real provider APIs are not called in the test path.
- Add regression test confirming state values remain within the documented audit states.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...schemas/audits...`
- `apps/api/...orchestrator...`
- `apps/api/...pipeline...`
- `tests/...audits...`
- `tests/...pipeline...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend audit API/pipeline tests and the backend test command after implementation.

### Dependencies
- TASK-107 — Define frontend-facing audit API schemas
- TASK-108 — Add audit list and detail endpoints

### Escalate if
- The audit pipeline has no existing safe entry point.
- Triggering execution requires introducing a new queue/background worker system.
- Duplicate run behavior is undefined.
- Existing state values differ from the architecture document.
- Running an audit from the API would require real external provider calls in tests.
- Cross-user access behavior is still unresolved.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-110 — Add audit results endpoint

### Status
Ready

### Goal
Add an authenticated `GET /audits/{id}/results` endpoint that returns frontend-safe per-run audit results for an owned audit.

### Why
The SCDL results table needs a stable API response for inspecting what was tested, whether the brand appeared, score components, competitors, sources, and run-level status.

### Context
The product output is based on `query × provider × run`. The frontend-facing schemas were defined in TASK-107. This task exposes stored/aggregated results only; it must not change parser, scoring, provider, raw response, or aggregation behavior.

### Scope
- Implement or update `GET /audits/{id}/results`.
- Use the frontend-facing results schemas from TASK-107.
- Enforce authenticated access.
- Enforce audit ownership for regular users.
- Return per-run rows where available.
- Include frontend-safe fields where available:
  - query
  - provider
  - run number
  - run status
  - brand visibility
  - brand position/rank
  - prominence score
  - sentiment
  - recommendation score
  - source quality score
  - final score
  - competitors
  - sources
  - raw answer reference, if already supported safely
- Handle empty results safely.
- Handle partial or failed audits safely.
- Add API tests for results behavior.

### Out of scope
- Do not implement `GET /audits/{id}/summary`.
- Do not implement export endpoints.
- Do not add frontend results table.
- Do not expose full raw provider answers unless an existing safe endpoint and access-control rule already exist.
- Do not change parser/scoring formulas.
- Do not change provider execution.
- Do not call real provider APIs in tests.
- Do not add recommendations generation.

### Acceptance criteria
- Authenticated user can retrieve results for an owned audit.
- Unauthenticated results requests are rejected.
- Cross-user results access is rejected or hidden according to the project convention.
- Results response uses the schema defined in TASK-107.
- Successful run rows include score and parser-derived fields where available.
- Failed/error/timeout/rate-limited runs are represented without crashing serialization.
- Empty results return a stable empty response shape.
- Existing backend tests still pass.

### Test requirements
- Add API test for retrieving results for an owned completed audit.
- Add API test for empty results response.
- Add API test for partial audit results including at least one failed or error run if fixtures allow.
- Add API test for unauthenticated results rejection.
- Add API test for cross-user results rejection.
- Add serialization test confirming result rows do not expose sensitive internal fields.
- Add regression test confirming parser/scoring are not re-run by this read endpoint unless the existing architecture explicitly requires it.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...schemas/results...`
- `apps/api/...repositories...`
- `tests/...audits...`
- `tests/...results...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend audit/results API tests and the backend test command after implementation.

### Dependencies
- TASK-107 — Define frontend-facing audit API schemas
- TASK-108 — Add audit list and detail endpoints

### Escalate if
- Stored result data cannot produce the required `query × provider × run` rows.
- Result row schema requires fields not available from current parser/scoring/storage outputs.
- Raw answer references require a new access-control or data-exposure decision.
- The endpoint would need to execute provider calls to produce results.
- Existing aggregation or storage structure is inconsistent with the frontend-facing schema.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-111 — Add audit summary endpoint

### Status
Ready

### Goal
Add an authenticated `GET /audits/{id}/summary` endpoint that returns frontend-safe aggregate metrics for an owned audit.

### Why
The audit detail and dashboard UI need compact summary data without requiring the frontend to calculate aggregate metrics from raw per-run rows.

### Context
The product requires audit-level summary, provider summary, critical queries, top competitors, and top sources where available. Aggregation must remain deterministic and must not change parser, scoring, provider, raw response, or storage contracts.

### Scope
- Implement or update `GET /audits/{id}/summary`.
- Use the frontend-facing summary schemas from TASK-107.
- Enforce authenticated access.
- Enforce audit ownership for regular users.
- Return audit-level summary fields where available:
  - total queries
  - total runs
  - completion ratio
  - visibility ratio
  - average score
  - critical query count
- Return provider-level summary where available.
- Return critical queries where available.
- Return top competitors where available.
- Return top sources/citation summary where available.
- Handle empty, running, partial, and failed audits safely.
- Add API tests for summary behavior.

### Out of scope
- Do not implement `GET /audits/{id}/results`.
- Do not implement frontend summary cards or charts.
- Do not add export endpoints.
- Do not change scoring formulas.
- Do not change parser behavior.
- Do not call provider APIs from this endpoint.
- Do not generate AI recommendations.
- Do not expose sensitive user/provider/internal fields.

### Acceptance criteria
- Authenticated user can retrieve summary for an owned audit.
- Unauthenticated summary requests are rejected.
- Cross-user summary access is rejected or hidden according to the project convention.
- Summary response uses the schema defined in TASK-107.
- Completed audit summary includes aggregate metrics where data exists.
- Running, partial, failed, or empty audits return a stable safe response shape.
- Summary endpoint does not require frontend-side aggregation to render basic summary cards.
- Existing backend tests still pass.

### Test requirements
- Add API test for summary of a completed audit with representative data.
- Add API test for summary of an empty or newly created audit.
- Add API test for summary of a partial or failed audit if fixtures allow.
- Add API test for unauthenticated summary rejection.
- Add API test for cross-user summary rejection.
- Add serialization test confirming summary response does not expose sensitive internal fields.
- Add regression test confirming this endpoint does not call external providers.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...schemas/summary...`
- `apps/api/...aggregation...`
- `apps/api/...repositories...`
- `tests/...audits...`
- `tests/...summary...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend audit/summary API tests and the backend test command after implementation.

### Dependencies
- TASK-107 — Define frontend-facing audit API schemas
- TASK-108 — Add audit list and detail endpoints
- TASK-110 — Add audit results endpoint

### Escalate if
- Existing aggregation output cannot produce the required summary fields.
- Critical query, competitor, or source summary definitions conflict with existing scoring/aggregation logic.
- Summary calculation would require changing parser, scoring, provider, raw response, or storage contracts.
- The endpoint would need to call external provider APIs.
- The response shape requires a product decision not covered by existing specs.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-112 — Add shared audit access guard for read and run endpoints

### Status
Ready

### Goal
Add a shared backend access guard that consistently enforces authenticated ownership checks for audit read and run endpoints.

### Why
Audit access control must be consistent across list, detail, status, results, summary, and run-trigger endpoints so one user cannot inspect or execute another user’s audit.

### Context
Earlier endpoint tasks require ownership checks individually. This task creates or verifies one shared access-control boundary to reduce endpoint-specific mistakes. Regular users may access only their own audits. Admin access is allowed only if it already fits the simple `user/admin` role model without introducing complex RBAC.

### Scope
- Add or verify a shared helper/dependency/service for loading an audit accessible to the current user.
- Apply the shared access guard to:
  - `GET /audits/{id}`
  - `GET /audits/{id}/status`
  - `GET /audits/{id}/results`
  - `GET /audits/{id}/summary`
  - `POST /audits/{id}/run`
- Ensure `GET /audits` still filters by current user ownership.
- Preserve the project’s chosen cross-user response convention: `403` or `404`.
- Add or consolidate regression tests proving cross-user access is rejected across all audit read/run endpoints.
- Add admin access tests only if simple admin behavior is already implemented.

### Out of scope
- Do not implement complex RBAC.
- Do not add teams, workspaces, organizations, or multi-tenant abstractions.
- Do not change audit result, summary, parser, scoring, provider, raw response, or aggregation contracts.
- Do not change audit creation behavior except where required to keep ownership consistent.
- Do not add frontend code.
- Do not change endpoint response schemas except for access-control error behavior if required by the existing convention.

### Acceptance criteria
- All audit read/run endpoints use one shared ownership/access-control path or a clearly equivalent project pattern.
- Regular users cannot access another user’s audit detail.
- Regular users cannot access another user’s audit status.
- Regular users cannot access another user’s audit results.
- Regular users cannot access another user’s audit summary.
- Regular users cannot trigger another user’s audit run.
- Audit list returns only audits owned by the current user.
- Existing backend tests still pass.

### Test requirements
- Add regression test for cross-user rejection on `GET /audits/{id}`.
- Add regression test for cross-user rejection on `GET /audits/{id}/status`.
- Add regression test for cross-user rejection on `GET /audits/{id}/results`.
- Add regression test for cross-user rejection on `GET /audits/{id}/summary`.
- Add regression test for cross-user rejection on `POST /audits/{id}/run`.
- Add regression test confirming `GET /audits` does not include another user’s audits.
- Add admin access tests only if simple admin access is implemented.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/audits...`
- `apps/api/...dependencies...`
- `apps/api/...repositories...`
- `tests/...audits...`
- `tests/...auth...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend auth/audit API tests and the backend test command after implementation.

### Dependencies
- TASK-108 — Add audit list and detail endpoints
- TASK-109 — Add audit status and run trigger endpoints
- TASK-110 — Add audit results endpoint
- TASK-111 — Add audit summary endpoint

### Escalate if
- The project has not chosen whether cross-user access returns `403` or `404`.
- Existing endpoints intentionally use different authorization behavior.
- Admin access requires more than a simple role check.
- Applying a shared guard would require changing parser, scoring, provider, raw response, or aggregation behavior.
- Existing tests contradict the ownership model.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-113 — Define SCDL level field in audit creation contract

### Status
Ready

### Goal
Define the backend contract for selecting SCDL audit level during audit creation.

### Why
The frontend must not invent how L1 and L2 are represented when creating an audit, because SCDL level affects provider execution mode and audit interpretation.

### Context
SCDL is a fixed methodology. L1 means AI answer without web access. L2 means AI answer with web access. The create-audit UI needs a stable field for this choice before the frontend form is implemented.

### Scope
- Define the audit creation field for SCDL level.
- Use one explicit representation, such as:
  - `scdl_level: "L1" | "L2"`
  - or a project-approved equivalent naming scheme
- Add the field to the audit creation request schema.
- Add the field to the audit detail/list/status schemas if the frontend needs to display it.
- Persist the selected SCDL level on the audit or project-equivalent settings object.
- Define default behavior for existing or omitted values if backward compatibility is required.
- Validate unsupported SCDL level values.
- Document the mapping:
  - `L1` = no web access
  - `L2` = web access
- Add tests for schema validation and persistence.

### Out of scope
- Do not implement actual provider web/no-web behavior unless it already exists and only needs wiring.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change aggregation logic.
- Do not add frontend create-audit UI.
- Do not add provider integrations.
- Do not rename the SCDL methodology.
- Do not introduce additional levels beyond L1 and L2.

### Acceptance criteria
- Audit creation accepts a valid SCDL level.
- Audit creation rejects unsupported SCDL level values.
- The selected SCDL level is persisted with the audit or audit settings.
- Audit read schemas expose SCDL level where needed by the frontend.
- Existing audit creation remains backward-compatible if required by current tests or fixtures.
- L1/L2 meanings are documented in the backend contract or schema comments.
- Existing backend tests still pass.

### Test requirements
- Add API/schema test for creating an audit with `L1`.
- Add API/schema test for creating an audit with `L2`.
- Add API/schema test for rejecting an unsupported SCDL level.
- Add persistence test confirming the selected level is stored.
- Add response serialization test confirming the selected level is returned where expected.
- Add regression test for omitted SCDL level if backward compatibility/default behavior is required.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...schemas/audits...`
- `apps/api/...models/audit...`
- `apps/api/...routes/audits...`
- `apps/api/...migrations...`
- `tests/...audits...`
- `tests/...schemas...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run backend audit schema/API tests and the backend test command after implementation.

### Dependencies
- TASK-107 — Define frontend-facing audit API schemas
- TASK-108 — Add audit list and detail endpoints

### Escalate if
- Existing audit execution already has a different field for web/no-web mode.
- Adding the field requires a migration/backfill decision not covered by this task.
- L1/L2 must affect provider execution immediately but provider capability support is undefined.
- Backward-compatible default behavior is unclear.
- Product requirements imply levels beyond L1 and L2.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-114 — Bootstrap React frontend app in apps/web

### Status
Ready

### Goal
Create the `apps/web` React TypeScript Vite SPA foundation for the service frontend.

### Why
The project needs a dedicated frontend module for authentication screens, protected dashboard layout, SCDL audit creation, audit status, results, summary, and source intelligence views.

### Context
The frontend is not implemented yet. It must be a regular SPA that calls the existing FastAPI REST API. Next.js is intentionally out of scope to avoid adding a second server-side application layer.

### Scope
- Create `apps/web`.
- Configure React + TypeScript + Vite.
- Add React Router.
- Add TanStack Query and wire its provider at the app root.
- Add Tailwind CSS.
- Add shadcn/ui or Radix-compatible UI foundation.
- Add a minimal route structure with placeholder routes.
- Add basic app shell placeholder only if needed to prove routing works.
- Add frontend scripts for:
  - lint
  - typecheck
  - test
  - build
- Add a minimal frontend test setup.
- Add one smoke test proving the app root renders.
- Document frontend local development command if the repository has a place for command docs.

### Out of scope
- Do not build login/register pages.
- Do not build protected routing logic.
- Do not build audit list, create, detail, results, summary, or source intelligence pages.
- Do not implement frontend API client.
- Do not modify backend API behavior.
- Do not add Next.js or another server-rendered framework.
- Do not add marketing landing pages.
- Do not add production deployment configuration unless required for the app to build in CI.

### Acceptance criteria
- `apps/web` exists and contains a React TypeScript Vite app.
- The frontend app can render at least one placeholder route.
- TanStack Query provider is configured at the app root.
- React Router is configured.
- Tailwind CSS is available to components.
- The selected UI component foundation is installed or minimally prepared.
- Frontend lint, typecheck, test, and build scripts exist.
- The smoke test passes.
- Existing backend tests are not affected.

### Test requirements
- Add a smoke test for rendering the frontend app root.
- Add a routing smoke test if the chosen test setup supports it without excessive setup.
- Run frontend typecheck.
- Run frontend build.
- Run frontend test command.
- Run backend tests only if root workspace or shared config was changed.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/...`
- root package/workspace config if required
- root CI/config files only if required to support frontend scripts

### Commands
Use project commands from `/AGENTS.md`.

If frontend commands do not exist yet, this task must introduce and document the frontend commands.

### Dependencies
- None

### Escalate if
- The repository package manager is unclear.
- Root workspace configuration conflicts with adding `apps/web`.
- CI cannot support frontend commands without a broader pipeline decision.
- The selected UI foundation requires project-level decisions not covered by this task.
- Adding frontend dependencies would modify unrelated backend dependency management.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-115 — Add frontend API client and shared response types

### Status
Ready

### Goal
Add a typed frontend API client and shared TypeScript response types for auth and audit API calls.

### Why
Frontend pages need one stable API boundary for backend communication instead of duplicating fetch logic, credentials behavior, error parsing, and response typing in every feature.

### Context
The frontend app has been bootstrapped in `apps/web`. Backend auth is expected to use httpOnly cookie-based JWT, so frontend requests must support credentials. Frontend-facing backend schemas for audits should already be defined before audit-specific API functions are added.

### Scope
- Add a shared API client module in `apps/web`.
- Configure API base URL through environment/config.
- Ensure requests can include credentials for cookie-based auth.
- Add predictable API error parsing.
- Add TypeScript types for safe frontend use of:
  - current user
  - auth responses
  - audit list item
  - audit detail
  - audit status
  - audit result row
  - audit results response
  - audit summary response
  - competitor summary item
  - source summary item
  - critical query item
- Add typed API functions for:
  - `GET /auth/me`
  - `POST /auth/login`
  - `POST /auth/register`
  - `POST /auth/logout`
  - `GET /audits`
  - `GET /audits/{id}`
  - `GET /audits/{id}/status`
  - `GET /audits/{id}/results`
  - `GET /audits/{id}/summary`
  - `POST /audits/{id}/run` or the documented equivalent if available
- Add tests for API client success and error behavior with mocked responses.

### Out of scope
- Do not build login/register pages.
- Do not build auth session hooks or route guards.
- Do not build audit UI pages.
- Do not store JWT or session tokens in localStorage.
- Do not invent backend response fields that are not present in the frontend-facing API schemas.
- Do not change backend API behavior in this task.
- Do not add generated OpenAPI tooling unless the repository already uses it or it is explicitly approved.

### Acceptance criteria
- API base URL is configurable without code changes.
- API client supports credentialed requests.
- Auth API functions are typed and callable from frontend code.
- Audit API functions are typed and callable from frontend code.
- API errors are returned or thrown in a predictable frontend-safe shape.
- TypeScript types match the documented backend response schemas as closely as possible.
- No JWT/token is stored in localStorage, sessionStorage, or frontend-accessible persistent storage.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for successful `GET /auth/me` API client call with mocked response.
- Add test for failed login or generic API error parsing.
- Add test or assertion confirming credentialed request configuration.
- Add test for one audit list API call with mocked response.
- Add test for one audit detail or summary API call with mocked response.
- Add regression test or static assertion that the client does not use localStorage/sessionStorage for auth tokens.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/lib/api...`
- `apps/web/src/types...`
- `apps/web/src/features/auth...`
- `apps/web/src/features/audits...`
- `apps/web/src/test...`
- `apps/web/.env.example` if the project uses env examples

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-107 — Define frontend-facing audit API schemas
- TASK-114 — Bootstrap React frontend app in apps/web

### Escalate if
- Backend response schemas are missing or inconsistent.
- Backend auth does not support credentialed cookie requests.
- CORS prevents credentialed frontend calls.
- API base URL configuration pattern is unclear.
- The task appears to require OpenAPI generation or shared package setup not already approved.
- Frontend needs token storage outside httpOnly cookies.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-116 — Add auth session state and protected route primitives

### Status
Ready

### Goal
Add frontend auth session state, current-user loading, and protected route primitives for authenticated pages.

### Why
The dashboard and SCDL audit pages must be inaccessible to unauthenticated users and must consistently know whether a user session exists.

### Context
The frontend API client exists and supports credentialed cookie-based auth. This task should create reusable auth/session primitives only. It should not build the final login/register page UI or audit dashboard.

### Scope
- Add a current-user query hook using `GET /auth/me`.
- Add login mutation hook using `POST /auth/login`.
- Add register mutation hook using `POST /auth/register`.
- Add logout mutation hook using `POST /auth/logout`.
- Add a session provider or project-equivalent auth state boundary if needed.
- Add protected route component or route guard primitive.
- Add unauthenticated redirect behavior for protected routes.
- Add authenticated redirect behavior for guest-only routes if routing structure supports it.
- Ensure auth state refreshes after login, register, and logout.
- Add tests for session loading and route guard behavior with mocked API responses.

### Out of scope
- Do not build final login/register pages.
- Do not build audit list or dashboard UI.
- Do not implement backend auth endpoints.
- Do not store JWT or session tokens in localStorage/sessionStorage.
- Do not add OAuth/social login.
- Do not add password reset or email verification.
- Do not add role-based UI beyond exposing the current user role if returned by the API.

### Acceptance criteria
- Frontend can load the current user session through a reusable hook.
- Loading, authenticated, and unauthenticated states are distinguishable.
- Login mutation updates or invalidates the current-user session state.
- Register mutation updates or invalidates the current-user session state according to backend behavior.
- Logout mutation clears or invalidates the current-user session state.
- Protected route primitive blocks unauthenticated access.
- Guest-only route behavior is available if needed for login/register pages.
- No JWT/token is stored in frontend-accessible persistent storage.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for current-user hook success state with mocked API response.
- Add test for current-user unauthenticated/error state.
- Add test for login mutation invalidating or refreshing current-user state.
- Add test for logout mutation clearing or invalidating current-user state.
- Add test for protected route redirect when unauthenticated.
- Add test for protected route rendering when authenticated.
- Add regression test or static assertion that auth primitives do not use localStorage/sessionStorage for tokens.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/auth...`
- `apps/web/src/routes...`
- `apps/web/src/app...`
- `apps/web/src/lib/api...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-115 — Add frontend API client and shared response types

### Escalate if
- Backend registration does not create a session but the frontend flow expects auto-login.
- Route guard behavior conflicts with the chosen router structure.
- API error shape does not distinguish unauthenticated from other errors.
- Cookie-based auth is not available from the browser due to CORS/config issues.
- Implementing role-based route protection becomes necessary.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-117 — Build login and register pages

### Status
Ready

### Goal
Add login and register pages connected to the frontend auth session flow.

### Why
Users need a browser UI to create an account, log in, and enter the protected audit dashboard.

### Context
Frontend auth API client, session hooks, and protected route primitives already exist. Registration may or may not automatically create an authenticated session depending on the backend behavior from earlier auth tasks. The UI must follow the clean B2B SaaS dashboard direction and avoid marketing landing page work.

### Scope
- Add `/login` route/page.
- Add `/register` route/page.
- Use React Hook Form for form state.
- Use Zod for client-side validation.
- Add email and password fields.
- Add password confirmation on register if the frontend validation pattern requires it.
- Connect login form to the login mutation from TASK-116.
- Connect register form to the register mutation from TASK-116.
- Redirect authenticated users away from login/register pages.
- Redirect successful login to the audits list/dashboard.
- Define successful register behavior according to backend behavior:
  - if registration creates a session, redirect to audits list/dashboard
  - if registration does not create a session, redirect to login with a success message
- Show loading and API error states.
- Add basic accessible labels and form error messages.
- Add tests for login/register behavior.

### Out of scope
- Do not implement password reset.
- Do not implement email verification.
- Do not implement OAuth/social login.
- Do not build audit list or dashboard content.
- Do not implement backend auth endpoints.
- Do not store JWT or session tokens in localStorage/sessionStorage.
- Do not add role-based UI.
- Do not add marketing landing page sections.

### Acceptance criteria
- `/login` renders a usable login form.
- `/register` renders a usable registration form.
- Invalid email is blocked by client-side validation.
- Missing password is blocked by client-side validation.
- Login API errors are displayed to the user.
- Register API errors are displayed to the user.
- Successful login redirects to the audits list/dashboard.
- Successful register follows the backend-compatible behavior documented in this task.
- Authenticated users do not remain on login/register pages.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for login page rendering.
- Add test for register page rendering.
- Add test for login form validation with invalid email.
- Add test for register form validation with missing required fields.
- Add test for successful login flow with mocked API/session behavior.
- Add test for login API error display.
- Add test for successful register behavior according to backend session behavior.
- Add test for authenticated redirect away from login/register if the route test setup supports it.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/routes...`
- `apps/web/src/features/auth...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-116 — Add auth session state and protected route primitives

### Escalate if
- Backend registration behavior is unclear: auto-login versus manual login after registration.
- Password policy requirements are stricter than the current validation contract.
- The selected UI component foundation is not installed or has conflicting patterns.
- Redirect paths for authenticated users are not defined.
- The task requires adding password reset, email verification, or OAuth.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-118 — Build protected app shell

### Status
Ready

### Goal
Add the authenticated application shell with shared layout, navigation, user session display, and logout behavior.

### Why
Protected product pages need a consistent dashboard frame before audit list, create, detail, results, summary, and source intelligence screens are implemented.

### Context
Login/register pages and protected route primitives already exist. The first authenticated destination is the audits dashboard/list. The target UI style is a clean light-theme B2B SaaS dashboard with compact navigation and no marketing landing page.

### Scope
- Add a protected app shell layout.
- Add sidebar or top navigation using the chosen UI foundation.
- Add primary navigation links for:
  - audits list/dashboard
  - create audit
  - profile/settings placeholder only if needed
- Add current user display using the auth session state.
- Add logout action connected to the logout mutation.
- Add route nesting so protected audit pages can render inside the shell.
- Add loading state for session initialization.
- Add unauthenticated redirect through the existing protected route primitive.
- Add basic responsive behavior for desktop and smaller screens.
- Add tests for shell rendering and logout behavior.

### Out of scope
- Do not build the audits list page content.
- Do not build create audit, detail, results, summary, or source intelligence pages.
- Do not implement admin dashboard UI.
- Do not implement billing, teams, workspaces, or organization switching.
- Do not add marketing landing sections.
- Do not change backend auth behavior.
- Do not add role-based navigation beyond showing simple admin/user role if already returned by `/auth/me`.

### Acceptance criteria
- Authenticated users see the protected app shell.
- The shell renders stable navigation links.
- The shell displays safe current-user information.
- Logout action calls the logout flow and returns the user to the unauthenticated flow.
- Protected child routes can render inside the shell.
- Session loading state does not flash protected content to unauthenticated users.
- Basic responsive layout works without breaking navigation.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for app shell rendering with authenticated session.
- Add test for navigation links rendering.
- Add test for child route rendering inside the shell.
- Add test for logout action invoking logout mutation and redirect behavior.
- Add test for unauthenticated redirect or reuse existing protected route test if already covered.
- Add test for session loading state if the test setup supports it.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/app...`
- `apps/web/src/routes...`
- `apps/web/src/layouts...`
- `apps/web/src/features/auth...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-116 — Add auth session state and protected route primitives
- TASK-117 — Build login and register pages

### Escalate if
- The routing structure cannot support protected nested layouts without redesign.
- Logout behavior conflicts with backend cookie-clearing behavior.
- Current-user response does not include enough safe display data.
- The UI foundation chosen in earlier tasks is missing or incompatible.
- The shell requires admin-specific navigation not defined in MVP scope.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-119 — Build audits list page

### Status
Ready

### Goal
Add the authenticated audits list page that shows the current user’s audits and links to audit creation and audit detail views.

### Why
The first screen after login must let users see existing SCDL audits, understand their status, and start a new audit.

### Context
The protected app shell already exists. Backend audit list/detail endpoints and frontend API client types should already exist. This task builds only the list/dashboard page content inside the protected shell.

### Scope
- Add audits list/dashboard route inside the protected app shell.
- Fetch audits through the typed frontend API client.
- Render audit rows or cards with available fields:
  - audit id or short id
  - brand name
  - brand domain
  - SCDL level if available
  - audit status
  - created/updated timestamp
  - summary preview if already included in list schema
- Add status badges for documented audit states.
- Add loading state.
- Add error state.
- Add empty state with call to action.
- Add navigation to create audit page.
- Add navigation from an audit row/card to audit detail page.
- Add basic filtering or search only if it can be implemented without changing backend API contracts.
- Add tests with mocked API data.

### Out of scope
- Do not build create audit form.
- Do not build audit detail/status/results/summary pages.
- Do not implement backend audit list endpoint.
- Do not add pagination unless backend contract already supports it.
- Do not add admin-wide audit management UI.
- Do not add billing, teams, workspaces, or organization UI.
- Do not change audit API response schemas.
- Do not add export functionality.

### Acceptance criteria
- Authenticated user can open the audits list/dashboard route.
- The page renders audits returned by the API.
- Audit status is displayed with a clear visual badge.
- Empty audit list shows a useful empty state and create-audit call to action.
- Loading state is visible while data is loading.
- Error state is visible when the API request fails.
- Clicking an audit navigates to that audit’s detail route.
- Clicking create-audit call to action navigates to the create audit route.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for rendering audits list with mocked audit data.
- Add test for empty state rendering.
- Add test for loading state if the test setup supports it.
- Add test for API error state.
- Add test for navigation to audit detail from an audit row/card.
- Add test for navigation to create audit page.
- Add test for rendering documented status values as badges.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits...`
- `apps/web/src/routes...`
- `apps/web/src/components/ui...`
- `apps/web/src/lib/api...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-108 — Add audit list and detail endpoints
- TASK-115 — Add frontend API client and shared response types
- TASK-118 — Build protected app shell

### Escalate if
- Audit list API response shape differs from the frontend types.
- The UI needs pagination but the backend does not expose pagination.
- The UI requires admin-wide audit visibility not defined in MVP.
- SCDL level display is required but the backend does not expose it.
- Existing route structure conflicts with the intended audits dashboard path.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-120 — Build manual create audit page

### Status
Ready

### Goal
Add an authenticated manual create audit page that submits a new SCDL audit through the backend audit creation API.

### Why
Users need a UI flow to create an audit before they can monitor status, inspect results, and analyze AI visibility.

### Context
The screenshots include both website-derived input and manual input. For MVP, manual audit creation is the priority unless website extraction already exists in the backend. The SCDL level contract should already be defined before this task.

### Scope
- Add create audit route inside the protected app shell.
- Build a manual audit creation form.
- Use React Hook Form for form state.
- Use Zod for client-side validation.
- Include fields supported by the backend contract:
  - brand name
  - brand domain
  - brand description
  - seed queries
  - providers
  - runs per query
  - language/locale/country if supported
  - SCDL level `L1` / `L2` if exposed by backend
- Convert seed queries into the backend-expected format.
- Submit form data to `POST /audits`.
- Show loading state during submission.
- Show API validation errors.
- Redirect to the created audit detail page after successful creation.
- Add tests for form validation and submission behavior.

### Out of scope
- Do not implement website crawling, website extraction, or auto-fill from URL unless it already exists and is explicitly exposed by the backend.
- Do not implement audit run trigger unless audit creation already triggers execution by backend contract.
- Do not implement audit status polling.
- Do not implement results, summary, or source intelligence UI.
- Do not change backend validation rules.
- Do not add provider integrations.
- Do not add export functionality.

### Acceptance criteria
- Authenticated user can open the create audit page.
- User can submit valid manual audit input.
- Required brand name validation works on the client.
- Invalid runs-per-query input is blocked before API submission.
- Seed queries are submitted in a predictable backend-compatible format.
- Selected SCDL level is submitted if the backend contract exposes it.
- API validation errors are displayed to the user.
- Successful creation redirects to the created audit detail page.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for create audit page rendering.
- Add test for required brand name validation.
- Add test for invalid runs-per-query validation.
- Add test for seed query parsing/submission format.
- Add test for SCDL level submission if the field exists in the backend contract.
- Add test for successful form submission with mocked API response.
- Add test for API error display.
- Add test for redirect to audit detail after successful creation.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/create...`
- `apps/web/src/routes...`
- `apps/web/src/lib/api...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-106 — Enforce authenticated audit creation ownership
- TASK-113 — Define SCDL level field in audit creation contract
- TASK-115 — Add frontend API client and shared response types
- TASK-118 — Build protected app shell

### Escalate if
- Backend `POST /audits` schema is incompatible with the required form fields.
- Supported providers are not known or not exposed to the frontend.
- SCDL level is required by product but not exposed by the backend contract.
- Website-derived audit creation becomes required for MVP.
- Audit creation must also trigger execution but the backend behavior is unclear.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-121 — Build audit detail and status view

### Status
Ready

### Goal
Add an authenticated audit detail page that shows audit metadata, current status, and run-trigger controls for an owned audit.

### Why
Users need to open a created audit, understand its current lifecycle state, and start or re-run execution through the UI when the backend contract supports it.

### Context
The backend exposes audit detail and status endpoints. It may also expose `POST /audits/{id}/run` or an equivalent run trigger. Audit states are `created`, `running`, `partial`, `completed`, and `failed`. Summary, results table, competitors, and source intelligence are separate UI tasks.

### Scope
- Add audit detail route inside the protected app shell.
- Fetch audit detail by ID through the typed API client.
- Fetch audit status by ID through the typed API client.
- Render audit metadata:
  - brand name
  - brand domain if available
  - SCDL level if available
  - providers if available
  - runs per query if available
  - created/updated timestamps
- Render current audit status with a clear visual state.
- Add manual refresh behavior.
- Add run/start button if the backend run trigger endpoint exists.
- Disable or protect run/start action when audit is already running.
- Show loading state.
- Show API error state.
- Show not-found/forbidden state using the project’s existing frontend pattern.
- Add navigation links to summary and results views if routes are already defined, or placeholders if not.
- Add tests with mocked API data.

### Out of scope
- Do not build audit summary cards or charts.
- Do not build full results table.
- Do not build critical queries, competitors, or source intelligence sections.
- Do not implement backend status or run trigger endpoints.
- Do not add polling, websockets, or real-time updates unless already defined by the project.
- Do not change audit state machine values.
- Do not change parser, scoring, provider, raw response, or aggregation behavior.
- Do not add export functionality.

### Acceptance criteria
- Authenticated user can open audit detail page for an owned audit.
- Audit metadata is rendered from the API response.
- Audit status is rendered using documented status values.
- Running audits show a running/in-progress state.
- Partial and failed audits remain inspectable.
- Manual refresh re-fetches audit detail/status data.
- Run/start action is available only when supported by the backend API contract.
- Run/start action is blocked or disabled while the audit is already running.
- Loading, error, and not-found/forbidden states are handled.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for rendering audit detail metadata with mocked API data.
- Add test for rendering each documented audit status value or a representative subset covering created/running/completed/failed.
- Add test for partial or failed audit remaining visible.
- Add test for loading state.
- Add test for API error state.
- Add test for manual refresh behavior if the test setup supports it.
- Add test for run/start button behavior when the endpoint is supported.
- Add test confirming run/start is disabled or blocked while audit status is `running`.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/detail...`
- `apps/web/src/features/audits/status...`
- `apps/web/src/routes...`
- `apps/web/src/lib/api...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-108 — Add audit list and detail endpoints
- TASK-109 — Add audit status and run trigger endpoints
- TASK-115 — Add frontend API client and shared response types
- TASK-118 — Build protected app shell
- TASK-120 — Build manual create audit page

### Escalate if
- Audit status values differ from the documented state model.
- The backend does not expose enough audit metadata for the detail view.
- Run trigger behavior is unclear or duplicate execution rules are not defined.
- Product requires automatic polling or real-time updates.
- Not-found versus forbidden frontend behavior is not defined.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-122 — Build audit summary cards and charts

### Status
Ready

### Goal
Add an authenticated audit summary view that renders aggregate SCDL metrics, provider summaries, critical query count, top competitors, and top sources for an owned audit.

### Why
Users need a compact overview of audit performance before drilling into the full per-run results table.

### Context
The backend exposes `GET /audits/{id}/summary`. The summary view should use frontend-safe aggregate data and must not calculate core scoring logic in the browser. Charts should be lightweight and use Recharts where useful.

### Scope
- Add audit summary route or summary section inside the audit detail area.
- Fetch audit summary by ID through the typed API client.
- Render summary cards for available metrics:
  - total queries
  - total runs
  - completion ratio
  - visibility ratio
  - average score
  - critical query count
- Render provider-level summary where available.
- Render top competitors where available.
- Render top sources/citation summary where available.
- Add one or more simple charts using Recharts where the data shape supports it.
- Handle running, partial, failed, and empty audits safely.
- Show loading state.
- Show API error state.
- Add tests with mocked summary data.

### Out of scope
- Do not implement backend summary endpoint.
- Do not calculate backend scoring formulas in the frontend.
- Do not build full audit results table.
- Do not build source intelligence detail view.
- Do not build export to DOCX/Excel.
- Do not add AI-generated recommendations.
- Do not change parser, scoring, provider, raw response, or aggregation behavior.
- Do not add complex competitor graph.

### Acceptance criteria
- Authenticated user can view summary for an owned audit.
- Summary cards render available aggregate metrics.
- Missing optional summary fields do not crash the page.
- Running, partial, failed, and empty audit summaries render safe states.
- Provider summary renders when data exists.
- Top competitors render when data exists.
- Top sources/citation summary renders when data exists.
- At least one chart renders when the required data exists.
- Frontend does not reimplement scoring formulas.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for rendering summary cards with completed audit summary data.
- Add test for empty or newly created audit summary state.
- Add test for partial or failed audit summary state.
- Add test for missing optional fields.
- Add test for provider summary rendering when data exists.
- Add test for top competitors rendering when data exists.
- Add test for top sources rendering when data exists.
- Add test for API error state.
- Add test or reviewer-verifiable assertion that scoring formulas are not implemented in the frontend.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/summary...`
- `apps/web/src/features/audits/detail...`
- `apps/web/src/routes...`
- `apps/web/src/lib/api...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-111 — Add audit summary endpoint
- TASK-115 — Add frontend API client and shared response types
- TASK-118 — Build protected app shell
- TASK-121 — Build audit detail and status view

### Escalate if
- Summary API response shape differs from frontend types.
- Required metrics are not available from the backend summary endpoint.
- Product requires frontend-side score calculation.
- Chart requirements need data not exposed by the backend.
- Source or competitor summaries require new backend aggregation behavior.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-123 — Build audit results table

### Status
Ready

### Goal
Add an authenticated audit results table that renders per-run SCDL audit results for an owned audit.

### Why
Users need to inspect the actual `query × provider × run` outputs behind the aggregate summary, including visibility, rank, score components, competitors, sources, and run status.

### Context
The backend exposes `GET /audits/{id}/results`. The product output is based on per-run rows. This task builds the main results table only; critical queries, competitor analysis, and source intelligence detail sections are separate tasks.

### Scope
- Add audit results route or results section inside the audit detail area.
- Fetch audit results by ID through the typed API client.
- Render a compact table of per-run result rows.
- Include available columns:
  - query
  - provider
  - run number
  - run status
  - SCDL level if available
  - brand visibility
  - brand position/rank
  - final score
  - prominence score
  - sentiment
  - recommendation score
  - source quality score
- Render competitors and sources in compact form if included directly in each row.
- Add status badges for run states.
- Add basic filters where feasible without backend changes:
  - provider
  - run status
  - brand visible / not visible
- Add expandable row or detail panel for longer query/result metadata if feasible.
- Handle empty results safely.
- Handle failed/error/timeout/rate-limited rows safely.
- Show loading state.
- Show API error state.
- Add tests with mocked results data.

### Out of scope
- Do not implement backend results endpoint.
- Do not build separate critical queries section.
- Do not build separate competitor analysis section.
- Do not build source intelligence/RAG citations detail view.
- Do not implement export to DOCX/Excel.
- Do not expose full raw provider answers unless a safe backend endpoint already exists.
- Do not calculate scoring formulas in the frontend.
- Do not change parser, scoring, provider, raw response, or aggregation behavior.
- Do not add server-side filtering unless already supported by the backend contract.

### Acceptance criteria
- Authenticated user can view results for an owned audit.
- Results table renders successful per-run rows.
- Results table renders failed/error/timeout/rate-limited rows without crashing.
- Brand visibility is clearly distinguishable.
- Final score and component scores are displayed when available.
- Empty results render a stable empty state.
- Loading and API error states are handled.
- Basic frontend-only filters work if implemented.
- Long query/result metadata does not break table layout.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for rendering successful result rows with mocked API data.
- Add test for rendering failed or error result rows.
- Add test for empty results state.
- Add test for API error state.
- Add test for brand visible and not-visible display.
- Add test for score/component score rendering.
- Add test for provider or status filtering if filters are implemented.
- Add test for expandable row/detail panel if implemented.
- Add test or reviewer-verifiable assertion that scoring formulas are not implemented in the frontend.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/results...`
- `apps/web/src/features/audits/detail...`
- `apps/web/src/routes...`
- `apps/web/src/lib/api...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-110 — Add audit results endpoint
- TASK-115 — Add frontend API client and shared response types
- TASK-118 — Build protected app shell
- TASK-121 — Build audit detail and status view

### Escalate if
- Results API response shape differs from frontend types.
- Required table fields are missing from the backend response.
- Product requires raw answer display but no safe raw-answer endpoint exists.
- Product requires server-side filtering or pagination.
- Displaying SCDL level requires a backend contract not yet implemented.
- The UI requirement implies frontend-side score calculation.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-124 — Build critical queries and competitors sections

### Status
Ready

### Goal
Add audit result sections for critical queries and competitor visibility using existing audit summary/results data.

### Why
Users need to quickly identify where their brand is absent, weakly represented, or displaced by competitors without manually scanning every per-run result row.

### Context
Critical queries are defined by the backend/product rules as queries where the brand is absent or the score is below the configured threshold. Competitor data should come from backend parser/aggregation outputs, not from frontend inference.

### Scope
- Add critical queries section to the audit results or summary area.
- Render critical query items from the summary/results API where available.
- Show why each query is critical when the API provides the reason or supporting fields.
- Add competitors section to the audit results or summary area.
- Render competitor names and frequency/visibility metrics where available.
- Link or cross-reference competitor/critical query items to related result rows if feasible without backend changes.
- Handle empty critical queries safely.
- Handle empty competitors safely.
- Show loading and error states if these sections fetch data independently.
- Add tests with mocked summary/results data.

### Out of scope
- Do not implement backend aggregation for critical queries or competitors.
- Do not infer competitors with new frontend parsing logic.
- Do not calculate scoring formulas in the frontend.
- Do not build source intelligence/RAG citations detail view.
- Do not build export functionality.
- Do not add AI-generated recommendations.
- Do not add complex competitor graph.
- Do not change parser, scoring, provider, raw response, or aggregation behavior.

### Acceptance criteria
- Critical queries section renders when critical query data exists.
- Empty critical queries state renders when no critical queries exist.
- Competitors section renders when competitor summary data exists.
- Empty competitors state renders when no competitors exist.
- Sections rely on backend-provided summary/results data, not frontend parser logic.
- User can understand whether a query is critical because of brand absence or low score when data is available.
- Loading and error states are handled if applicable.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for rendering critical queries with mocked data.
- Add test for empty critical queries state.
- Add test for rendering competitors with mocked data.
- Add test for empty competitors state.
- Add test for displaying critical reason when provided by the API.
- Add test for API error state if the section performs its own request.
- Add test or reviewer-verifiable assertion that no frontend competitor extraction/parser logic is introduced.
- Add test or reviewer-verifiable assertion that scoring formulas are not implemented in the frontend.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/summary...`
- `apps/web/src/features/audits/results...`
- `apps/web/src/features/audits/competitors...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-111 — Add audit summary endpoint
- TASK-122 — Build audit summary cards and charts
- TASK-123 — Build audit results table

### Escalate if
- Critical query data is not exposed by the backend.
- Competitor summary data is not exposed by the backend.
- Product requires frontend-side competitor extraction.
- Product requires a graph or recommendation engine rather than a simple summary section.
- Critical query definition differs from the backend/product spec.
- Required fields would need parser, scoring, or aggregation contract changes.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-125 — Build source intelligence and RAG citations view

### Status
Ready

### Goal
Add an authenticated source intelligence view that shows cited sources, citation counts, and source usage patterns for an owned SCDL audit.

### Why
Users need to understand which external sources influence AI answers and how often those sources appear across audit runs.

### Context
The screenshots include an interface for RAG/source audit: where citations come from and how often they are used. Source data must come from backend parser/aggregation outputs. The frontend must not crawl sources, classify them with new AI logic, or infer source quality outside the backend contract.

### Scope
- Add source intelligence section or route inside the audit detail/results area.
- Render source summary data from the audit summary/results API where available.
- Show available source fields such as:
  - source title or domain
  - URL or normalized domain if available
  - citation count
  - provider
  - related query count
  - source type if provided by the backend
  - source quality score if provided by the backend
- Add simple sorting or grouping where feasible without backend changes:
  - by citation count
  - by provider
  - by source type if available
- Add empty state for audits with no sources.
- Add safe rendering for malformed or partially missing source fields.
- Add loading and error states if the section fetches data independently.
- Add tests with mocked source data.

### Out of scope
- Do not implement backend source aggregation.
- Do not implement source crawling.
- Do not classify sources in the frontend.
- Do not calculate source quality in the frontend.
- Do not call external APIs from the frontend.
- Do not expose full raw provider answers unless a safe backend endpoint already exists.
- Do not add export functionality.
- Do not add AI-generated source recommendations.
- Do not change parser, scoring, provider, raw response, or aggregation behavior.

### Acceptance criteria
- Source intelligence view renders when source summary data exists.
- Empty source state renders when no sources are available.
- Citation counts are visible when provided by the backend.
- Source domain or URL is visible when provided by the backend.
- Provider/source grouping or sorting works if implemented.
- Malformed or partial source entries do not crash the page.
- The frontend does not perform source crawling or source classification.
- Loading and API error states are handled if applicable.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add test for rendering source summary data with citation counts.
- Add test for empty sources state.
- Add test for malformed or partially missing source fields.
- Add test for sorting or grouping if implemented.
- Add test for API error state if the section performs its own request.
- Add test or reviewer-verifiable assertion that no source crawling is introduced.
- Add test or reviewer-verifiable assertion that source quality is not calculated in the frontend.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/features/audits/sources...`
- `apps/web/src/features/audits/results...`
- `apps/web/src/features/audits/summary...`
- `apps/web/src/components/ui...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-111 — Add audit summary endpoint
- TASK-122 — Build audit summary cards and charts
- TASK-123 — Build audit results table
- TASK-124 — Build critical queries and competitors sections

### Escalate if
- Source data is not exposed by the backend summary or results API.
- Product requires frontend-side source classification.
- Product requires crawling or verifying source URLs.
- Source quality score definition is missing or conflicts with backend scoring.
- Required fields would need parser, scoring, provider, raw response, or aggregation contract changes.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-126 — Add frontend-backend mocked contract fixtures

### Status
Ready

### Goal
Add shared mocked contract fixtures that represent the frontend-facing auth and audit API responses used by frontend tests.

### Why
Frontend tests need stable representative API data so UI implementation can be verified against backend-facing contracts without depending on a running backend or real provider executions.

### Context
The frontend consumes backend responses for auth, audit list, audit detail, audit status, audit results, audit summary, competitors, and sources. These fixtures should mirror the schemas defined for the frontend-facing API and help detect drift between frontend assumptions and backend contracts.

### Scope
- Add mocked frontend test fixtures for:
  - current user
  - unauthenticated auth response/error
  - audit list response
  - audit detail response
  - audit status response
  - audit results response
  - empty audit results response
  - audit summary response
  - empty/new audit summary response
  - partial or failed audit summary response if supported by current schemas
  - competitors summary data
  - sources/citations summary data
- Use documented audit states and run states only.
- Include both successful and failed/error run examples.
- Include at least one fixture with empty sources.
- Include at least one fixture with competitors.
- Include at least one fixture with critical queries.
- Use fixtures in frontend API/client or UI tests where practical.
- Keep fixtures small and readable.

### Out of scope
- Do not start or require a real backend server.
- Do not call real provider APIs.
- Do not add new backend endpoints.
- Do not change backend schemas in this task.
- Do not generate fixtures from production data.
- Do not include secrets, credentials, real customer data, or provider keys.
- Do not implement frontend pages in this task.

### Acceptance criteria
- Fixtures exist for the core auth and audit API response shapes.
- Fixtures are small, readable, and safe to commit.
- Fixtures use only documented status values.
- Fixtures include representative success, empty, partial, and failed/error states where supported.
- Frontend tests can import and reuse fixtures.
- Fixture data does not contain secrets or real customer data.
- Frontend lint/typecheck/test commands pass.

### Test requirements
- Add or update at least one API client test to use the auth fixture.
- Add or update at least one audits list/detail test to use audit fixtures.
- Add or update at least one results or summary test to use results/summary fixtures.
- Add a type-level or runtime validation check if the project test setup supports validating fixture shapes.
- Add regression coverage for empty sources or empty results using fixtures.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/src/test/fixtures...`
- `apps/web/src/features/auth...`
- `apps/web/src/features/audits...`
- `apps/web/src/lib/api...`
- `apps/web/src/test...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run frontend lint, typecheck, tests, and build after implementation.

### Dependencies
- TASK-115 — Add frontend API client and shared response types
- TASK-119 — Build audits list page
- TASK-123 — Build audit results table
- TASK-125 — Build source intelligence and RAG citations view

### Escalate if
- Backend response schemas and frontend TypeScript types do not match.
- Required fixture fields are unknown or still product-dependent.
- Fixture creation would require changing backend API contracts.
- Tests require a live backend rather than mocked responses.
- Representative source/competitor/critical query shapes are not defined.

### Done means
Inherits project defaults from `/AGENTS.md`.

## TASK-127 — Add authenticated happy-path E2E smoke flow

### Status
Ready

### Goal
Add a minimal authenticated end-to-end smoke test that covers login, audit creation, audit execution trigger, status inspection, summary inspection, and results inspection using mocked backend/provider behavior.

### Why
The MVP needs one high-level verification path proving that auth, protected frontend routes, audit API contracts, and SCDL UI screens work together without requiring real provider calls.

### Context
Backend tests already cover core contracts individually, and frontend tests cover pages/components with mocked responses. This task adds one thin integration/E2E smoke flow for the main user journey. The flow must remain lightweight and deterministic.

### Scope
- Add one authenticated happy-path smoke flow.
- Use mock provider or mocked backend responses only.
- Cover the user journey:
  - register or login
  - reach protected audits dashboard
  - create a manual SCDL audit
  - open audit detail
  - trigger audit run if the backend contract supports manual run trigger
  - inspect audit status
  - inspect audit summary
  - inspect audit results
- Ensure no real external provider APIs are called.
- Ensure test data is deterministic.
- Add setup/teardown or isolated test data handling according to project conventions.
- Document how to run the smoke flow.

### Out of scope
- Do not add broad E2E test coverage for every edge case.
- Do not test real provider integrations.
- Do not test billing, teams, workspaces, OAuth, or admin UI.
- Do not introduce a heavy E2E matrix across multiple browsers unless the project already requires it.
- Do not replace unit, API, contract, or fixture tests.
- Do not change parser, scoring, provider, raw response, or aggregation behavior.
- Do not add production deployment configuration.

### Acceptance criteria
- The smoke flow can authenticate a test user or use a deterministic authenticated test session.
- The smoke flow reaches the protected audits dashboard.
- The smoke flow creates a manual SCDL audit or uses a deterministic pre-created audit fixture if full creation is not practical.
- The smoke flow opens audit detail.
- The smoke flow verifies a visible audit status.
- The smoke flow verifies summary data appears when mocked summary data is available.
- The smoke flow verifies results table data appears when mocked results data is available.
- The smoke flow does not call real external provider APIs.
- The smoke flow is documented and can be run through a project command.
- Existing backend and frontend tests still pass.

### Test requirements
- Add one E2E or integration smoke test for the authenticated audit journey.
- Add assertion that protected routes are reachable only after authentication.
- Add assertion that audit creation or audit fixture loading succeeds.
- Add assertion that audit detail/status is visible.
- Add assertion that summary view renders expected mocked data.
- Add assertion that results view renders expected mocked data.
- Add guard, mock, or assertion confirming real provider APIs are not called.
- Add failure diagnostics that make it clear whether auth, API contract, or UI rendering failed.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/web/...e2e...`
- `apps/web/...tests...`
- `apps/web/src/test/fixtures...`
- `apps/api/...test fixtures...`
- root test or CI config if required

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- frontend lint
- frontend typecheck
- frontend tests
- frontend build
- backend tests if backend fixtures or test setup are changed
- the new E2E/smoke command

### Dependencies
- TASK-103 — Define auth cookie, CORS, and CSRF policy
- TASK-105 — Implement login, logout, and current-user endpoints
- TASK-109 — Add audit status and run trigger endpoints
- TASK-111 — Add audit summary endpoint
- TASK-119 — Build audits list page
- TASK-120 — Build manual create audit page
- TASK-121 — Build audit detail and status view
- TASK-122 — Build audit summary cards and charts
- TASK-123 — Build audit results table
- TASK-126 — Add frontend-backend mocked contract fixtures

### Escalate if
- The project has no agreed E2E test runner or smoke-test strategy.
- Running the flow requires real external provider APIs.
- Auth cookies cannot be handled reliably in the selected test environment.
- Frontend and backend contracts disagree on required response fields.
- Audit execution cannot be made deterministic with mock provider behavior.
- The smoke flow becomes a broad test suite rather than one minimal happy-path check.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- The smoke-test command is documented.
- The PR description explains which parts are mocked and which parts are real.