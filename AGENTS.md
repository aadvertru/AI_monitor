# AI Brand Visibility Monitor

A B2B SaaS application for auditing how brands and websites appear in AI-generated answers, with SCDL audit as the first core feature.

## Agent role

Implement small, reviewable tasks in this repository without changing product intent or breaking existing audit pipeline contracts.

Codex is the implementation agent. Claude is the review agent.

## Stack

- Backend: Python, FastAPI, Pydantic, async SQLAlchemy
- Database: PostgreSQL for production, SQLite allowed for local/test
- Existing backend app: `apps/api`
- New frontend app: `apps/web`
- Frontend: React, TypeScript, Vite, React Router
- API/cache state: TanStack Query
- Forms/validation: React Hook Form + Zod
- UI: Tailwind CSS, shadcn/ui or Radix-based components
- Charts: Recharts

## Product scope

Current stage:
- Add authentication and authorization
- Add missing audit API endpoints for the UI
- Add frontend app shell
- Add SCDL audit UI

SCDL is a fixed methodology:
- L1 = AI answer without web access
- L2 = AI answer with web access

Out of MVP:
- OAuth/social login
- billing
- teams/workspaces
- complex RBAC
- public customer API
- multi-tenant SaaS complexity

## Commands

Use actual commands from the repository config when available.

Expected backend defaults:
```bash
pytest
ruff check .
mypy .
```

Expected frontend defaults after `apps/web` is created:
```bash
npm run lint
npm run typecheck
npm test
npm run build
```

If commands are missing, add or document them in the task that introduces the relevant module.

## Critical boundaries

- MUST NOT break existing parser, scoring, storage, provider, or aggregation contracts.
- MUST NOT make parser or scoring depend on frontend behavior.
- MUST NOT call real external provider APIs in automated tests.
- MUST NOT silently change public API behavior without updating specs and tests.
- MUST keep tasks small enough for one focused PR.
- MUST add or update tests for every implementation task.
- MUST preserve deterministic parser/scoring behavior.
- MUST keep raw provider responses inspectable and re-runnable.

## Auth rules

- Use email + password for MVP.
- Hash passwords with bcrypt/passlib or the existing backend-approved equivalent.
- Prefer JWT auth via httpOnly cookie.
- Required endpoints:
  - `POST /auth/register`
  - `POST /auth/login`
  - `POST /auth/logout`
  - `GET /auth/me`
- Roles: `user`, `admin`.
- Regular users can access only their own audits.
- Admin may access all audits if this does not require complex RBAC.
- Add `audits.user_id`.

## Frontend rules

- Frontend lives in `apps/web`.
- Use SPA architecture; do not introduce Next.js or another server layer.
- First authenticated screen is the audits dashboard/list.
- Main flow: create audit → monitor status → open results → inspect summary/table/critical queries/competitors/sources.
- Default UI style: clean B2B SaaS dashboard, light theme, compact tables, status badges, summary cards.

## API endpoints for this stage

Add or verify:
- `GET /audits`
- `GET /audits/{id}`
- `GET /audits/{id}/status`
- `GET /audits/{id}/results`
- `GET /audits/{id}/summary`
- `POST /audits/{id}/run` or the existing equivalent pipeline trigger

All audit endpoints must enforce user ownership unless admin access is explicitly implemented.

## Task rules

Tasks are execution contracts. Use the format from `docs/TASK_AUTHORING_GUIDE.md`.

Every implementation task must include:
- clear scope
- explicit out of scope
- observable acceptance criteria
- concrete test requirements
- dependencies
- escalation conditions

If full test suite fails due to pre-existing issues:

- DO NOT fix them unless explicitly required by the task
- MUST:
  - confirm task-related tests pass
  - confirm no new failures introduced
  - explicitly report existing failures

## Escalate if

- A task requires changing parser/scoring/storage contracts.
- Authentication or authorization behavior is ambiguous.
- A database migration is required but not mentioned in the task.
- Existing tests contradict the task.
- API behavior needed by frontend is missing or inconsistent.
- The change exceeds one focused PR.
- Secrets, provider keys, or production credentials are involved.
- Product behavior must be invented rather than implemented from specs.

## Done means

A task is done only when:
- implementation matches the task scope
- out-of-scope items were not changed
- required tests are added or updated
- relevant backend/frontend commands pass
- API behavior is covered by tests where applicable
- PR summary includes what changed and how it was verified
- Claude review issues are either fixed or explicitly escalated
