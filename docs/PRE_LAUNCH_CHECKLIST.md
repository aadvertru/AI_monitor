# Pre-Launch Checklist

Issues and technical debt identified during code review that should be addressed before production launch.
Items are grouped by area and sorted roughly by priority within each group.

---

## 🔴 Critical (must fix before launch)

### Backend

**B-1 · No database migration system**
File: `apps/api/database.py`, `lifespan` in `apps/api/main.py`
`AUTO_CREATE_SCHEMA=1` calls `Base.metadata.create_all`, which is a no-op on existing tables.
Any schema change (adding a column, adding an index) silently goes unapplied in an existing DB.
Set up Alembic before the first real deployment, or any schema evolution will require a manual
`DROP TABLE` and data loss.

**B-2 · No rate limiting on auth endpoints**
File: `apps/api/main.py` — `/auth/login`, `/auth/register`
Both endpoints accept unlimited unauthenticated requests. With no account lockout or throttle,
brute-force attacks against known email addresses are trivial. Add a per-IP or per-email rate limit
(e.g., via `slowapi` or a reverse-proxy rule) before exposing the service publicly.

**B-3 · Password policy is minimal**
File: `apps/api/main.py` — `RegisterRequest.validate_password`
The only check is non-empty. No minimum length, no complexity requirement. Before launch, enforce
at least 8 characters minimum.

**B-4 · `enable_query_expansion` accepted but silently ignored**
File: `apps/api/main.py` — `AuditCreateRequest`, `create_audit_record`
The field is stored on the Audit model but no expansion logic is executed server-side. The frontend
always sends `false`, so this is not currently harmful, but users who call the API directly and set
`enable_query_expansion: true` will get no queries expanded with no error or warning.
Either implement the feature or return a 400 for unsupported flags.

---

## 🟡 Important (high risk if left unaddressed)

### Backend

**B-5 · No pagination on `/audits` list endpoint**
File: `apps/api/main.py` — `list_audit_records`
`relative_audit_numbers()` computes sequential audit numbers by sorting the entire in-memory result.
When pagination is added later, the batch-computed numbers on the list page will disagree with the
single-query numbers returned by `/audits/{id}`, `/audits/{id}/status`, and `/audits/{id}/summary`.
Design pagination with this in mind, or store `audit_number` as a DB column at creation time.

**B-6 · Brand deduplication is name-only and lossy**
File: `apps/api/main.py` — `create_audit_record`
Brands are deduplicated case-insensitively on `brand_name`. Two consequences:
- Different products with the same name share a Brand record; the first registrant's domain wins.
- Two teams auditing the same brand under slightly different names (e.g., "Acme AI" vs "AcmeAI")
  create separate Brand records with no link between them.
Consider adding a per-user brand scope or requiring explicit brand_id reuse.

**B-7 · `build_audit_summary_response` executes a full results query on every call**
File: `apps/api/main.py` — `build_audit_summary_response`
The function calls `build_audit_results_response()` which issues a five-table JOIN loading every
Run, Query, ParsedResult, Score, and RawResponse for the audit. Summary is then computed in
Python. For audits with thousands of runs this will be slow and memory-heavy. Add result-level
caching or compute summary aggregates with SQL GROUP BY before launch.

### Frontend

**F-1 · Query expansion returns hardcoded sample strings**
File: `apps/web/src/features/audits/CreateAuditPage.tsx` — `mockExpandQueries`, `mockPaaQueries`,
`mockAiExpansionQueries`
Clicking "Query expansion" injects 12 hard-coded strings that look like AI-generated queries.
This violates the rule that the frontend must not generate AI recommendations. Before launch,
either connect this button to a real backend `/audits/expand-queries` endpoint, or rename/label
the button "Add sample queries" so the strings are clearly examples, not AI output.

**F-2 · Token cost estimate is fictional and unvalidated**
File: `apps/web/src/features/audits/CreateAuditPage.tsx` — `estimateAuditTokens`,
`queryExpansionTokenCost`
The formula `queries × providers × 10` (L2 multiplier 1.5, source-intelligence +5 per pair) and the
expansion cost of 15 tokens have no server-side counterpart. If the project introduces real billing,
users will be misled. Either remove the estimate, document it as approximate, or derive it from
a backend pricing endpoint.

---

## 🟠 Moderate (degrades UX or maintainability)

### Frontend

**F-3 · Language and country selects limited to 6 options each**
File: `apps/web/src/features/audits/CreateAuditPage.tsx` — `languageOptions`, `countryOptions`
Only 6 languages (en, uk, ru, es, de, fr) and 6 countries (US, UA, GB, CA, DE, FR) are offered.
Any user auditing a brand in Japanese, Portuguese, Italian, etc. cannot create a correctly localised
audit. Expand to full ISO 639-1 / ISO 3166-1 lists, or add a free-text fallback field.

**F-4 · No auto-refresh while audit is running**
File: `apps/web/src/features/audits/AuditDetailPage.tsx`
When an audit is in `running` status, the completion ratio and run counts update only when the user
clicks the Refresh button. Add a polling interval (e.g., `refetchInterval: 5000` on the summary
query) that activates while `status === "running"` and stops on completion.

**F-5 · No confirmation before starting an audit**
File: `apps/web/src/features/audits/AuditDetailPage.tsx` — Run button
Starting an audit is currently one click: no warning about token cost, no "Are you sure?". This is
especially important now that the page shows an estimated token count on creation. Add a
confirmation dialog that shows the cost estimate before triggering the run.

**F-6 · `optionalText()` applied to required `brandDomain` in payload builder**
File: `apps/web/src/features/audits/CreateAuditPage.tsx` — `buildPayload`
`brandDomain` is required by the Zod schema (`min(1)`), but `buildPayload` passes it through
`optionalText()` which returns `null` for an empty or whitespace-only string. Zod prevents this in
normal use, but the mismatch is a code smell and a subtle bug source if schema changes. Replace
with a direct `.trim()` or remove `optionalText()` for required fields.

**F-7 · Error message on audit detail page does not distinguish failure source**
File: `apps/web/src/features/audits/AuditDetailPage.tsx` — error branch
When either the detail query or the summary query fails, the page shows the same generic
"Audit unavailable." message. Consider distinguishing `detail.isError` from `summary.isError`
so users know whether the audit itself is missing or just the summary data is unavailable.

**F-8 · "Source intelligence" has no in-UI description**
File: `apps/web/src/features/audits/CreateAuditPage.tsx` — `enableSourceIntelligence` checkbox
The checkbox label is just "Source intelligence" with no hint text explaining what it does or
how much it costs. Add a short description or tooltip before launch.

### Backend

**B-8 · `/audits/{audit_id}/status` endpoint is unused**
File: `apps/api/main.py` — `get_audit_status`
After the AuditDetailPage refactor, the frontend no longer calls `/audits/{id}/status`. The
endpoint still exists and is tested. It is harmless, but either document it as a public API
surface or remove it to reduce maintenance scope.

---

## 🔵 Minor (polish and developer experience)

### Testing

**T-1 · Smoke test requires two `/auth/me` 401 responses (React StrictMode)**
File: `apps/web/src/test/authenticatedSmokeFlow.test.tsx` — `mockSmokeBackend`
`mockSmokeBackend()` queues two 401 responses for `/auth/me` to accommodate React StrictMode's
double-mount behaviour in Vitest. If `<React.StrictMode>` is ever removed from `main.tsx`,
the second queued 401 goes unconsumed and the smoke test will catch a spurious "unexpected API
call" failure. Add a comment explaining why two mocks are needed.

**T-2 · Fixture inconsistency: `auditCreateResponseFixture.audit_number = 2`**
File: `apps/web/src/test/fixtures.ts`
`auditCreateResponseFixture` has `audit_number: 2` while `auditDetailFixture` has `audit_number: 1`.
This does not cause failures but misrepresents the user flow in the smoke test (a newly created
audit should continue the numbering sequence, not jump backwards). Align the fixtures to tell a
coherent story.

**T-3 · No test for run-trigger error state in AuditDetailPage**
File: `apps/web/src/features/audits/AuditDetailPage.test.tsx`
The error inline banner "Unable to start audit." rendered when `runAuditMutation` fails is not
covered by any test. Add a test that mocks a 409 or 500 from `POST /audits/:id/run` and asserts
the banner appears.

**T-4 · No backend API integration tests**
Only unit tests and a frontend smoke flow exist. Schema changes (new required field, renamed key)
can break the frontend contract silently. Add at least a minimal `pytest` integration suite that
exercises the full HTTP stack against a test SQLite DB.

### Developer Experience

**D-1 · No dev user creation script**
There is no `scripts/create_dev_user.py` or equivalent. A new developer must hit `/auth/register`
via curl or Postman to set up a local account. Add a simple CLI script (or a `make seed` target)
that creates a default dev user.

**D-2 · No `.env.example` for the API**
`apps/web/.env.example` documents `VITE_API_BASE_URL`, but the backend has no equivalent.
The API requires `SECRET_KEY`, optionally `DATABASE_URL`, `AUTO_CREATE_SCHEMA`, and cookie
configuration variables. Create `apps/api/.env.example` listing all supported env vars with
safe example values.

**D-3 · `runs_per_query` is hardcoded to 1 in the frontend**
File: `apps/web/src/features/audits/CreateAuditPage.tsx` — `buildPayload`
The backend accepts `runs_per_query` 1–5 but the form always submits 1. If multi-run audits are
a planned feature, expose this in the UI before launch. If not, document the constraint.
