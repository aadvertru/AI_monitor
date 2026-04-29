# Backend Context

Backend for AI Brand Visibility Monitor lives in `apps/api`.

The backend is a FastAPI application responsible for authentication, audit API, orchestration entry points, storage access, parser/scoring execution, aggregation, and frontend-facing API contracts.

## Stack

- Python
- FastAPI
- Pydantic
- async SQLAlchemy
- PostgreSQL for production
- SQLite allowed for local/test if already supported
- pytest or the project-approved backend test runner
- ruff/mypy or the project-approved lint/typecheck tools

## Product role

The backend supports the SCDL audit lifecycle:

1. Accept audit input.
2. Normalize and validate settings.
3. Prepare queries.
4. Schedule or run provider jobs.
5. Store raw responses.
6. Parse stored responses.
7. Score parsed results.
8. Aggregate audit summary.
9. Expose frontend-safe results.

The backend must remain the source of truth for validation, scoring, aggregation, ownership, and access control.

## Existing audit model

Core audit-related entities include:

- Brand
- Audit
- Query
- Run
- RawResponse
- ParsedResult
- Score
- Summary or project-equivalent aggregation output

Do not expose internal ORM objects directly through frontend endpoints.

## SCDL methodology

SCDL is fixed product methodology.

- L1 = AI answer without web access
- L2 = AI answer with web access

Backend must define the persisted API contract for SCDL level before frontend create-audit UI depends on it.

Do not invent additional SCDL levels without product approval.

## Architecture boundaries

The backend must preserve the audit pipeline boundaries:

- API validates input and exposes endpoints.
- Orchestrator coordinates pipeline execution.
- Scheduler creates jobs.
- Worker executes provider calls and stores raw responses.
- Provider adapter normalizes external provider responses.
- Parser extracts deterministic signals.
- Scoring calculates bounded component metrics and final score.
- Aggregation produces query/provider/audit summaries.
- Storage persists raw, parsed, and score data separately.

Do not mix these responsibilities in route handlers.

## Critical invariants

MUST preserve:

- Provider adapters return normalized provider responses and do not leak unhandled provider exceptions.
- Raw responses are stored for executed runs.
- Raw responses remain inspectable and re-runnable.
- Parser never crashes on malformed or empty provider data.
- Parser returns a complete parsed result shape.
- Scoring depends on parsed results, not raw provider answers.
- Final score stays bounded to `[0,1]`.
- Audit reaches a final controlled state: `completed`, `partial`, or `failed`.
- Partial provider failure must not automatically collapse the whole audit.

## Authentication scope

MVP authentication uses:

- email + password
- persistent users table
- password hashing with bcrypt/passlib or approved equivalent
- JWT via httpOnly cookie preferred
- roles: `user`, `admin`

Required auth endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Out of scope:

- OAuth/social login
- password reset
- email verification
- refresh-token rotation unless explicitly adopted
- complex RBAC
- teams/workspaces
- billing
- multi-tenant SaaS abstractions

## Password and token rules

Backend MUST:

- never store plain passwords
- never return password or password hash fields from API responses
- read JWT secret/config from environment or approved config
- avoid hardcoded secrets
- verify tokens safely
- reject invalid or expired tokens
- clear auth cookies on logout

Backend SHOULD:

- centralize password/JWT utilities
- centralize auth cookie settings
- keep token claim shape small and stable

## Cookie, CORS, and CSRF rules

Because auth uses httpOnly cookies:

- cookie settings must be explicit
- `HttpOnly` must be enabled
- `Secure` must be configurable for local versus production
- `SameSite` must be explicit
- credentialed CORS must not use wildcard origin
- allowed frontend origins must come from config/environment
- CSRF stance must be documented or implemented according to the project decision

Do not weaken production cookie/security settings silently to make local development work.

## Ownership and authorization

Audits must be owned by users.

Rules:

- `audits.user_id` or project-equivalent owner field is required.
- `POST /audits` must assign owner from current authenticated user.
- Regular users can access only their own audits.
- Admin access to all audits is allowed only through simple role check if it does not introduce complex RBAC.
- Cross-user access must use one consistent convention: `403` or `404`.
- Audit list must filter by current user ownership.

Use a shared access guard/dependency for audit read/run endpoints where possible.

## Frontend-facing audit endpoints

Frontend needs stable endpoints:

- `POST /audits`
- `GET /audits`
- `GET /audits/{id}`
- `GET /audits/{id}/status`
- `GET /audits/{id}/results`
- `GET /audits/{id}/summary`
- `POST /audits/{id}/run` or documented equivalent

All protected audit endpoints must enforce ownership.

Do not expose internal jobs, ORM objects, provider secrets, or unsafe raw provider payloads directly.

## Frontend-facing schema rules

Use Pydantic schemas or project-equivalent response models.

Schemas should cover:

- audit list item
- audit detail
- audit status
- audit result row
- audit results response
- audit summary response
- competitor summary item
- source summary item
- critical query item
- auth user response

Schemas must be frontend-safe and stable.

If a field is not available yet, mark it optional or omit it. Do not invent fake backend behavior to satisfy UI assumptions.

## Results endpoint rules

`GET /audits/{id}/results` should expose per-run result rows based on:

`query × provider × run`

Rows may include:

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
- safe raw answer reference if supported

Read endpoints should not call real providers.

## Summary endpoint rules

`GET /audits/{id}/summary` should expose aggregate values where available:

- total queries
- total runs
- completion ratio
- visibility ratio
- average score
- critical query count
- provider summary
- critical queries
- top competitors
- top sources

Summary must remain safe for empty, running, partial, and failed audits.

## Testing expectations

Backend implementation tasks must include tests.

Required test areas:

- user persistence
- duplicate email handling
- password hashing and verification
- JWT creation/verification
- invalid and expired token handling
- auth cookie behavior
- registration/login/logout/me endpoints
- authenticated audit creation
- audit ownership filtering
- cross-user access rejection
- audit list/detail/status/results/summary endpoints
- empty, partial, failed audit response shapes
- no real provider calls in automated tests

Parser/scoring tests must remain deterministic and fixture-based.

## Do not change without explicit task scope

- parser contract
- scoring formulas
- provider adapter contract
- raw response storage contract
- audit state machine
- aggregation definitions
- SCDL L1/L2 meanings
- public API response behavior

## Escalate if

- a task requires changing parser/scoring/storage/provider contracts
- database migration pattern is unclear
- auth security behavior is ambiguous
- cookie/CORS/CSRF policy conflicts with browser requirements
- cross-user access convention is undefined
- frontend requires a field not available in backend schemas
- run trigger requires a new queue/background worker system
- tests would need real external provider APIs
- implementation requires OAuth, billing, teams, workspaces, complex RBAC, or multi-tenant design