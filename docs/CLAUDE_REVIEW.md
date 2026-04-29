# Claude Review Guide

Claude is the review agent for AI Brand Visibility Monitor.

The reviewer must verify that each Codex change follows the task scope, preserves project contracts, includes required tests, and does not introduce unsafe product or architecture decisions.

## Review inputs

For every review, Claude should receive:

- the implemented task ID
- the task text from `docs/TASKS.md`
- the diff or PR
- relevant files:
  - `AGENTS.md`
  - `docs/PROJECT_CONTEXT.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/TEST_STRATEGY.md`
  - `docs/TASK_AUTHORING_GUIDE.md`
- test output
- known limitations or skipped checks, if any

Do not approve a change if the task text or relevant project context is missing.

## Review decision values

Use one of:

```text
approve
request_changes
needs_human_clarification
```

Use severity:

```text
none
minor
important
critical
```

## Required review output

Return structured review output:

```json
{
  "decision": "approve | request_changes | needs_human_clarification",
  "severity": "none | minor | important | critical",
  "summary": "Short review summary",
  "blocking_issues": [],
  "non_blocking_issues": [],
  "tests_reviewed": [],
  "missing_tests": [],
  "contract_risks": [],
  "security_risks": [],
  "recommended_changes": []
}
```

## Global approval rule

Approve only if all are true:

- implementation matches the task scope
- out-of-scope items were not changed
- required tests were added or updated
- relevant project commands passed or failure is justified
- no critical contract was changed silently
- no security-sensitive behavior was guessed
- no unrelated refactoring or formatting noise was introduced
- no frontend behavior depends on invented backend fields
- no backend behavior was changed to satisfy UI assumptions without task scope

## Automatic request_changes

Request changes if any of these are true:

- missing required tests
- task scope was exceeded
- out-of-scope item was changed
- public API response shape changed without task/spec update
- parser/scoring/provider/storage contract changed without explicit task scope
- auth or authorization behavior is insecure or incomplete
- JWT or secrets are hardcoded
- password or password hash appears in API responses
- frontend stores JWT in `localStorage` or `sessionStorage`
- tests call real external provider APIs
- implementation adds OAuth, billing, teams, workspaces, complex RBAC, or multi-tenant behavior
- code introduces a second frontend server layer such as Next.js
- frontend reimplements backend scoring, parsing, competitor extraction, or source classification
- cross-user audit access is possible
- audit endpoints bypass shared ownership/access-control logic without reason

## Automatic needs_human_clarification

Ask for human clarification if any of these are true:

- task contradicts `AGENTS.md`
- task contradicts architecture or product spec
- required API schema is missing or ambiguous
- database migration/backfill decision is unclear
- cookie/CORS/CSRF security decision is unclear
- cross-user access convention is unresolved: `403` vs `404`
- SCDL L1/L2 representation is unclear
- backend lacks data needed by frontend and the task does not authorize schema changes
- implementation requires introducing a new queue/background worker system
- implementation requires a product decision not present in the task

## Critical project contracts

Claude must protect these contracts:

- Parser is deterministic and does not call AI.
- Parser never crashes on malformed or empty provider data.
- Scoring depends on parsed results, not raw provider answers.
- Final score remains bounded to `[0,1]`.
- Raw responses remain stored and inspectable.
- Read endpoints must not call real providers.
- Provider failures must not automatically collapse the whole audit.
- Audit state machine remains controlled.
- SCDL meanings remain:
  - L1 = no web access
  - L2 = web access

## Backend review checklist

For backend tasks, verify:

- FastAPI/Pydantic patterns are consistent with the repo
- async SQLAlchemy usage follows existing project style
- schemas do not expose internal ORM objects directly
- auth responses never expose password/hash fields
- password hashing uses approved secure utility
- JWT secret/config comes from environment/config
- auth cookie settings are explicit
- credentialed CORS does not use wildcard origin
- audit ownership is enforced
- regular users cannot access another user’s audits
- admin behavior does not become complex RBAC
- no real provider APIs are called in tests
- empty/partial/failed audit states are handled safely

## Frontend review checklist

For frontend tasks, verify:

- frontend lives in `apps/web`
- React + TypeScript + Vite SPA is preserved
- Next.js or another server layer is not introduced
- React Router is used for routes
- TanStack Query is used for server state
- React Hook Form + Zod are used for forms
- API calls go through shared API client
- credentialed requests are supported
- JWT is not stored in frontend-accessible storage
- protected routes block unauthenticated users
- loading/error/empty states are present
- UI uses backend-provided fields only
- scoring, parsing, source classification, and competitor extraction are not reimplemented in frontend

## Test review checklist

Verify tests cover the task’s required cases.

Backend tests should cover relevant:

- success path
- failure path
- edge case
- auth/authorization behavior
- ownership behavior
- empty/partial/failed data
- no real provider calls

Frontend tests should cover relevant:

- render success state
- loading state
- error state
- empty state
- form validation
- route protection
- mocked API response
- no token storage in localStorage/sessionStorage

Do not accept “tests pass” as sufficient if task-required cases are missing.

## Diff quality checklist

Reject or request changes if the diff:

- mixes unrelated refactoring with feature work
- changes formatting across unrelated files
- introduces large unreviewable changes
- modifies generated files without explanation
- changes dependency management without task scope
- adds dead code or unused abstractions
- duplicates logic that should be shared
- hides behavior in unclear fallback logic

## Phase review mode

When reviewing a mini-phase containing several tasks, Claude should:

1. list included task IDs
2. verify each task separately
3. verify integration between tasks
4. check for contract drift across the phase
5. identify missing tests across the phase
6. return one overall decision

A mini-phase should usually contain 2–4 related tasks.

Auth/security tasks may require review after each task.

## Review prompts

Use this prompt for task review:

```text
Review the implementation of TASK-XXX.

Follow:
- AGENTS.md
- docs/PROJECT_CONTEXT.md
- docs/ARCHITECTURE.md
- docs/PRODUCT_SPEC.md
- docs/TEST_STRATEGY.md
- docs/TASK_AUTHORING_GUIDE.md
- docs/CLAUDE_REVIEW.md

Check:
- scope compliance
- out-of-scope violations
- required tests
- contract safety
- auth/security risks
- frontend/backend schema consistency
- unnecessary refactoring

Return the structured JSON review decision.
```

Use this prompt for phase review:

```text
Review the completed mini-phase containing TASK-XXX through TASK-YYY.

For each task:
- verify task scope
- verify acceptance criteria
- verify tests
- identify missing or weak coverage

Then review integration across the phase:
- contract drift
- auth/security risks
- ownership/access-control consistency
- frontend/backend schema mismatch
- test gaps

Return the structured JSON review decision.
```

## Reviewer principle

Prefer `request_changes` over approval when behavior is unsafe, untested, or outside task scope.

Prefer `needs_human_clarification` when the implementation requires a product, security, migration, or architecture decision not explicitly defined.
