# Frontend Context

Frontend for AI Brand Visibility Monitor lives in `apps/web`.

The frontend is a React TypeScript Vite SPA that calls the FastAPI REST API. It must not introduce Next.js or any second server-side application layer.

## Stack

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- React Hook Form
- Zod
- Tailwind CSS
- shadcn/ui or Radix-based UI components
- Recharts
- Frontend tests according to the repository setup

## Product role

The frontend provides the authenticated SaaS dashboard for SCDL audit workflows:

1. Login or register.
2. View audits dashboard/list.
3. Create a manual SCDL audit.
4. Open audit detail.
5. Monitor status.
6. Inspect summary.
7. Inspect per-run results.
8. Inspect critical queries, competitors, and sources.

## SCDL concepts

SCDL is fixed product methodology.

- L1 = AI answer without web access
- L2 = AI answer with web access

The frontend may display and submit the selected SCDL level only through the backend-defined contract. Do not invent new names, levels, or execution modes in frontend code.

## UI direction

Use a clean B2B SaaS dashboard style.

Default UI expectations:

- light theme by default
- compact tables
- status badges
- summary cards
- simple filters
- clear loading/error/empty states
- readable forms
- practical navigation
- no marketing landing page

The UI may use screenshots as visual direction, but must not copy them literally.

## Routing

Expected route groups:

- public / guest:
  - `/login`
  - `/register`

- protected:
  - `/audits`
  - `/audits/new`
  - `/audits/:id`
  - `/audits/:id/summary`
  - `/audits/:id/results`
  - `/audits/:id/sources`

Exact paths may follow the project’s router conventions, but the user journey must stay the same.

## Auth behavior

Backend auth uses email/password and JWT via httpOnly cookie.

Frontend rules:

- MUST use credentialed API requests.
- MUST NOT store JWT in `localStorage`.
- MUST NOT store JWT in `sessionStorage`.
- MUST NOT read or manually manage the JWT token in browser code.
- MUST load session state through `GET /auth/me`.
- MUST invalidate or refresh session state after login/logout/register.
- MUST protect authenticated routes.
- MUST redirect unauthenticated users away from protected routes.

## API client rules

All backend calls should go through a shared API client layer.

The API client must:

- use configurable API base URL
- support credentialed requests
- normalize API errors into a predictable frontend-safe shape
- expose typed functions for auth and audit endpoints
- avoid duplicating fetch logic inside components

Do not make components depend directly on raw `fetch` unless the project explicitly chooses that pattern.

## TanStack Query rules

Use TanStack Query for server state:

- current user session
- audit list
- audit detail
- audit status
- audit results
- audit summary
- source intelligence data if fetched separately

Do not store server state in local component state unless it is purely temporary UI state.

## Forms

Use React Hook Form + Zod for:

- login
- register
- create audit

Validation rules must mirror backend contracts where possible.

Frontend validation is for UX only. Backend remains the source of truth.

## Audit list page

The audits dashboard/list should show:

- brand name
- brand domain if available
- SCDL level if available
- audit status
- created/updated timestamp
- summary preview if available

Required states:

- loading
- error
- empty
- populated

## Create audit page

Manual audit creation is the MVP priority.

Supported fields depend on backend contract, but may include:

- brand name
- brand domain
- brand description
- seed queries
- providers
- runs per query
- language / locale / country
- SCDL level

Do not implement website crawling or website-derived auto-fill unless the backend already exposes it.

## Audit detail page

Audit detail should show:

- audit metadata
- current status
- SCDL level if available
- providers if available
- runs per query if available
- created/updated timestamps
- run/start action if backend exposes it
- links to summary, results, and sources views

Do not implement polling, websockets, or real-time behavior unless explicitly specified.

## Summary view

Summary data must come from backend aggregation.

Frontend may render:

- total queries
- total runs
- completion ratio
- visibility ratio
- average score
- critical query count
- provider summary
- top competitors
- top sources
- simple charts with Recharts

Frontend MUST NOT reimplement backend scoring formulas.

## Results table

Results are based on:

`query × provider × run`

Rows may display:

- query
- provider
- run number
- run status
- brand visibility
- brand position/rank
- final score
- component scores
- competitors
- sources

Frontend MUST NOT re-run parser or scoring logic.

## Critical queries and competitors

Critical queries and competitor summaries must come from backend summary/results data.

Frontend MUST NOT:

- extract competitors with new parser logic
- calculate critical-query rules independently if backend already provides them
- generate AI recommendations

## Source intelligence

Source intelligence must use backend-provided source/citation data.

Frontend may display:

- source title/domain
- URL or normalized domain
- citation count
- provider
- related query count
- source type if provided
- source quality score if provided

Frontend MUST NOT:

- crawl sources
- classify sources
- calculate source quality
- call external source APIs

## Testing expectations

Frontend tasks should include tests for:

- rendering success states
- loading states
- error states
- empty states
- form validation
- route protection
- mocked API responses
- no token usage in localStorage/sessionStorage where relevant

Use shared mocked fixtures for auth and audit responses once available.

## Escalate if

- Backend response schema differs from frontend types.
- Cookie auth cannot work because of CORS/config.
- A UI requirement needs a backend field that does not exist.
- Product behavior requires frontend-side scoring, parsing, source classification, or competitor extraction.
- A task requires Next.js or another server layer.
- A task requires billing, teams, OAuth, complex RBAC, or multi-tenant behavior.