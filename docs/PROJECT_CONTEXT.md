# AI Brand Visibility Monitor

AI Brand Visibility Monitor is a B2B SaaS product for auditing how brands and websites appear in AI-generated answers.

## Working mode

- Primary coding agent: Codex
- Review agent: Claude
- File language: English
- Discussion language: Russian is allowed
- Work format: code, product specs, task planning, review-driven development

## Product focus

The first core feature is SCDL audit.

SCDL is a fixed audit methodology:
- L1 = AI answer without web access
- L2 = AI answer with web access

The product measures:
- whether a brand appears in AI answers
- how visible/prominent it is
- which competitors appear near or instead of it
- which sources are cited or used
- how results aggregate by query, provider, run, and audit

This is not a classic SEO SERP monitoring tool.

## Current stage

The backend for SCDL audit already exists and has been tested with mock data.

Next development stage:
1. Add authentication and authorization.
2. Add missing API endpoints needed by the UI.
3. Add a new frontend SPA in `apps/web`.
4. Implement the SCDL audit frontend.

## Existing backend

- Backend app: `apps/api`
- Stack: Python, FastAPI, Pydantic, async SQLAlchemy
- Production database: PostgreSQL
- Local/test database: SQLite is allowed
- Existing endpoint: `POST /audits`
- Existing domain/storage models include:
  - Brand
  - Audit
  - Query
  - Run
  - RawResponse
  - ParsedResult
  - Score

Existing audit pipeline includes parts of:
- query preparation
- provider execution
- mock provider
- raw response storage
- parser
- scoring
- aggregation

## New frontend

Frontend must be added as `apps/web`.

Chosen stack:
- React
- TypeScript
- Vite
- React Router
- TanStack Query
- React Hook Form
- Zod
- Tailwind CSS
- shadcn/ui or Radix-based components
- Recharts

Do not use Next.js at this stage.

The frontend must be a regular SPA calling the FastAPI REST API.

## Authentication scope

MVP authentication:
- email + password
- users table in the existing database
- password hashing with bcrypt/passlib or an approved backend equivalent
- JWT auth, preferably via httpOnly cookie
- roles: `user`, `admin`

Required auth endpoints:
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Authorization rules:
- regular users see only their own audits
- admin may see all audits if this does not introduce complex RBAC
- add `audits.user_id`

Out of scope:
- OAuth/social login
- billing
- teams/workspaces
- complex RBAC
- multi-tenant SaaS complexity
- public customer API

## UI direction

Style:
- clean B2B SaaS dashboard
- light theme by default
- compact tables
- filters
- status badges
- summary cards
- charts where useful
- no marketing landing page

Main authenticated flow:
1. Audits dashboard/list
2. Create audit
3. Monitor audit status
4. Open audit detail
5. Inspect results table
6. Inspect summary, critical queries, competitors, and sources

Core pages:
- Login
- Register
- Audits list
- Create audit
- Audit detail
- Audit results table
- Audit summary
- Minimal profile/settings page only if needed for auth

## Critical rules

- MUST NOT break parser, scoring, storage, provider, or aggregation contracts.
- MUST preserve deterministic parser and scoring behavior.
- MUST keep raw provider responses available for re-running parser/scoring.
- MUST keep API behavior compatible with FastAPI/Pydantic patterns.
- MUST add tests for implementation tasks.
- MUST keep tasks small and reviewable.
- MUST update specs if public contracts change.

## Task authoring

Tasks must follow `docs/TASK_AUTHORING_GUIDE.md`.

Each task must include:
- Goal
- Why
- Scope
- Out of scope
- Acceptance criteria
- Test requirements
- Dependencies
- Escalate if
- Done means

Do not use vague task wording such as “improve”, “clean up”, or “make production-ready” unless concrete measurable criteria are included.

## Where to look

- `AGENTS.md` — primary execution rules for Codex
- `docs/TASKS.md` — current implementation tasks
- `docs/ARCHITECTURE.md` — audit pipeline architecture and invariants
- `docs/PRODUCT_SPEC.md` — product scope and audit lifecycle
- `docs/PARSER_SPEC.md` — parser contract
- `docs/SCORING.md` — scoring contract
- `docs/TEST_STRATEGY.md` — required test strategy
- `docs/TASK_AUTHORING_GUIDE.md` — task writing format

## Decision status

DECIDED:
- Backend remains FastAPI.
- Frontend will be React + TypeScript + Vite SPA.
- Authentication is email/password with JWT.
- SCDL L1/L2 definitions are fixed.
- OAuth, billing, teams, and complex RBAC are out of MVP.

ASSUMED:
- Existing backend structure can accept auth and user ownership without major architecture changes.
- Existing audit endpoints can be extended without breaking current tests.
- shadcn/ui or Radix-based UI will be sufficient for MVP.

UNKNOWN:
- Exact repository commands for backend and frontend.
- Whether database migrations are already configured.
- Exact current API response schemas for frontend consumption.
- Whether admin access to all audits is required immediately or can be deferred.
