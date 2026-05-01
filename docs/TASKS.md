# Phase F — Real Provider Pilot Tasks

This file contains the revised tasks for the OpenAI real-provider pilot after review feedback.

The pilot uses **OpenAI only** and supports two SCDL modes:

- `L1` = OpenAI answer without web search
- `L2` = OpenAI answer with web search enabled

The OpenAI pilot must use the **OpenAI Responses API**. Chat Completions must not be used unless Responses API is unavailable and the task escalates first.

---

## TASK-128 — Define real provider pilot constraints

### Status
Ready

### Goal
Define safe constraints for running the first real OpenAI provider pilot in L1 and L2 modes.

### Why
Real provider calls introduce cost, rate-limit, security, and data-quality risks, so the project needs explicit guardrails before OpenAI API execution is enabled.

### Context
The current MVP works on mock data. This phase introduces one real provider only: OpenAI. The pilot must support two SCDL execution modes:

- `L1` = OpenAI answer without web search
- `L2` = OpenAI answer with web search enabled

The OpenAI pilot uses the OpenAI Responses API.

This task defines constraints and configuration only. It must not implement the OpenAI adapter or call the real OpenAI API.

### Scope
- Add configuration flags for real-provider execution.
- Keep mock provider mode as the default behavior.
- Add or define provider mode setting:
  - `PROVIDER_MODE=mock`
  - `PROVIDER_MODE=openai`
- Add explicit real-provider enable flag:
  - `REAL_PROVIDER_ENABLED=false`
- Define the OpenAI pilot API family:
  - OpenAI Responses API
- Add a real-provider policy guard that runs before scheduling/execution and before provider adapter selection.
- Define provider mode rules:
  - `PROVIDER_MODE=mock` allows mock execution only.
  - `PROVIDER_MODE=openai` allows OpenAI execution only.
  - mixed provider lists are rejected during the pilot.
- Add default pilot caps:
  - `REAL_PROVIDER_ENABLED=false`
  - `PROVIDER_MODE=mock`
  - `REAL_PROVIDER_MAX_PROVIDERS=1`
  - `REAL_PROVIDER_MAX_QUERIES=5`
  - `REAL_PROVIDER_MAX_RUNS_PER_QUERY=1`
  - `REAL_PROVIDER_MAX_TOTAL_RUNS=5`
- Add separate constraints for local/dev real-provider testing if needed.
- Define how SCDL level maps to OpenAI execution mode at the policy level:
  - `L1` must not use web search.
  - `L2` may use web search.
- Add safe failure behavior when real provider mode is requested but disabled.
- Add safe failure behavior when a real audit exceeds configured caps.
- Add tests for configuration and cap enforcement where the project structure supports it.
- Document the pilot limits in the relevant docs or config comments.

### Out of scope
- Do not implement the OpenAI API adapter.
- Do not add OpenAI API key handling beyond naming required config fields if needed.
- Do not call the real OpenAI API.
- Do not implement web search execution.
- Do not change parser, scoring, aggregation, raw response, or provider contracts.
- Do not add support for providers other than OpenAI.
- Do not add billing or user-facing cost estimates.
- Do not change frontend UI unless a minimal config label is already required by existing code.
- Do not increase default audit limits for mock mode.

### Acceptance criteria
- Mock provider mode remains the default.
- Real provider calls are impossible unless explicitly enabled.
- OpenAI is the only real provider allowed by the pilot constraints.
- The OpenAI pilot API family is documented as Responses API.
- Real-provider policy guard is called before scheduling/execution.
- Real-provider audits are blocked if they exceed configured query/run/provider caps.
- `PROVIDER_MODE=mock` rejects OpenAI real execution.
- `PROVIDER_MODE=openai` rejects mock-only and mixed-provider execution.
- Mixed provider lists are rejected in real-provider pilot mode.
- `L1` and `L2` policy meanings are documented for OpenAI pilot usage.
- Attempting real provider execution while disabled returns a controlled error.
- Attempting unsupported provider execution returns a controlled error.
- Existing mock-provider tests still pass.
- No real external API calls happen in automated tests.

### Test requirements
- Add a test confirming mock provider mode is the default.
- Add a test confirming real provider execution is blocked when `REAL_PROVIDER_ENABLED=false`.
- Add a test confirming only OpenAI is allowed as real provider in pilot mode.
- Add a test confirming mixed provider lists are rejected in real-provider pilot mode.
- Add a test confirming the policy guard runs before scheduling/execution.
- Add a test confirming max providers per real audit is enforced.
- Add a test confirming max queries per real audit is enforced.
- Add a test confirming max runs per query is enforced.
- Add a test confirming max total real runs per audit is enforced.
- Add a test confirming unsupported real provider mode returns a controlled error.
- Add a test or assertion confirming no real OpenAI API call is made by this task.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...config...`
- `apps/api/...providers...`
- `apps/api/...orchestrator...`
- `apps/api/...scheduler...`
- `apps/api/...settings...`
- `tests/...config...`
- `tests/...providers...`
- `tests/...orchestrator...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend config/provider tests
- backend audit/provider tests affected by provider mode
- backend lint/typecheck commands if available

### Dependencies
- None

### Escalate if
- The project has no clear config/environment pattern.
- Existing provider selection does not support a clean mock/openai split.
- SCDL `L1`/`L2` is not available in audit settings.
- Enforcing caps requires changing provider, parser, scoring, raw response, or aggregation contracts.
- Real-provider enablement cannot be blocked before adapter execution.
- Existing scheduling/execution flow cannot support a pre-scheduling policy guard.
- Existing tests expect unrestricted provider execution.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document the pilot configuration names and default values.
- Document that OpenAI Responses API is the selected API family for the pilot.
- Confirm in the PR summary that no real OpenAI API call is made by this task.

---

## TASK-129 — Add OpenAI secrets and provider config handling

### Status
Ready

### Goal
Add secure backend configuration for OpenAI provider credentials, model defaults, API family, and pilot request settings without hardcoding secrets.

### Why
The real-provider pilot needs OpenAI API access, but provider credentials and model/cost choices must be configured safely before the adapter is implemented.

### Context
TASK-128 defined the real-provider pilot constraints. This task adds the secure configuration layer for OpenAI only. It prepares the project for the OpenAI adapter but must not implement real API calls yet.

The pilot provider is OpenAI only:
- `L1` = OpenAI answer without web search
- `L2` = OpenAI answer with web search enabled

The pilot uses the OpenAI Responses API.

### Scope
- Add OpenAI provider config fields using the existing backend config/environment pattern.
- Add config field for OpenAI API family and default it to Responses API.
- Add support for OpenAI API key.
- Add default OpenAI model config:
  - `OPENAI_L1_MODEL=gpt-4.1-mini`
  - `OPENAI_L2_MODEL=gpt-4.1-mini`
- Add request settings:
  - `OPENAI_REQUEST_TIMEOUT_SECONDS=30`
  - `OPENAI_MAX_OUTPUT_TOKENS=1200`
- Add `.env.example` placeholders or project-equivalent documentation for required OpenAI settings.
- Ensure OpenAI API key is never hardcoded.
- Ensure OpenAI API key is never returned by API responses.
- Ensure OpenAI API key is never printed in logs or test output.
- Add controlled error behavior when OpenAI provider mode is enabled but the API key is missing.
- Add controlled error behavior when required OpenAI config values are invalid.
- Add tests for config loading, missing config, default values, and secret-safety behavior.

### Out of scope
- Do not implement the OpenAI provider adapter.
- Do not call the real OpenAI API.
- Do not add support for providers other than OpenAI.
- Do not implement web search execution.
- Do not add frontend UI for entering API keys.
- Do not store provider keys in the database.
- Do not expose provider keys to users.
- Do not add billing, quotas, or user-level API-key management.
- Do not silently change default models if the configured model is unavailable.
- Do not change parser, scoring, aggregation, raw response, or provider contracts.

### Acceptance criteria
- OpenAI API key is read only from environment/config.
- OpenAI API family is configured as Responses API.
- OpenAI L1 and L2 model settings are configurable.
- Default L1 model is `gpt-4.1-mini`.
- Default L2 model is `gpt-4.1-mini`.
- OpenAI timeout and response limit settings are configurable.
- `.env.example` or equivalent config documentation includes OpenAI placeholders without real secrets.
- Missing OpenAI API key produces a controlled provider/config error when OpenAI mode is enabled.
- Invalid required OpenAI config produces a controlled error.
- Logs and API responses do not expose the API key.
- Existing mock-provider behavior remains unchanged.
- Existing backend tests still pass.
- No real external API calls happen in automated tests.

### Test requirements
- Add a test confirming OpenAI API key can be loaded from environment/config.
- Add a test confirming missing OpenAI API key fails safely when OpenAI mode is enabled.
- Add a test confirming missing OpenAI API key does not affect mock provider mode.
- Add a test confirming OpenAI API family defaults to Responses API.
- Add a test confirming OpenAI L1 model config is loaded.
- Add a test confirming OpenAI L2 model config is loaded.
- Add a test confirming timeout config is loaded or defaults safely.
- Add a test confirming max output tokens config is loaded or defaults safely.
- Add a test or assertion confirming secrets are masked or absent from string representations/loggable config output.
- Add a test or assertion confirming no real OpenAI API call is made by this task.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...config...`
- `apps/api/...settings...`
- `apps/api/...providers...`
- `.env.example`
- `tests/...config...`
- `tests/...providers...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend config/provider tests
- backend tests affected by provider mode
- backend lint/typecheck commands if available

### Dependencies
- TASK-128 — Define real provider pilot constraints

### Escalate if
- The repository has no clear environment/config pattern.
- Adding OpenAI config requires storing secrets in the database.
- Existing config objects expose secrets in logs or API responses.
- The configured default OpenAI model is unavailable in the project account.
- The Responses API cannot be used for the intended L1/L2 implementation.
- Missing-key behavior conflicts with the provider adapter contract.
- Implementing this task requires making a real OpenAI API call.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document the OpenAI environment variable names and safe local setup.
- Document the default OpenAI models and request settings.
- Confirm in the PR summary that no real OpenAI API call is made by this task.

---

## TASK-130 — Implement OpenAI real provider adapter for L1 and L2

### Status
Ready

### Goal
Implement the first real provider adapter for OpenAI Responses API that supports SCDL `L1` no-web answers and `L2` web-enabled answers through the existing provider contract.

### Why
The project needs one controlled real-provider implementation to verify that the SCDL audit pipeline works on real OpenAI responses while preserving the existing raw response, parser, scoring, and aggregation boundaries.

### Context
TASK-128 defined real-provider pilot constraints. TASK-129 added secure OpenAI config handling. This task adds the OpenAI adapter only. Automated tests must mock the internal OpenAI client wrapper and must not call the real OpenAI API.

SCDL behavior:
- `L1` = OpenAI answer without web search
- `L2` = OpenAI answer with web search enabled

The adapter must use OpenAI Responses API. Chat Completions must not be used unless Responses API is unavailable and the task escalates first.

### Scope
- Add a small internal OpenAI client wrapper/interface.
- Implement the adapter against the OpenAI Responses API.
- Ensure tests mock the internal OpenAI client wrapper, not the real network.
- Add an OpenAI provider adapter using the existing provider adapter interface/contract.
- Support `L1` execution without web search.
- Support `L2` execution with web search enabled if the selected OpenAI model/tooling supports it.
- For `L1`, ensure request payload does not include web search tools.
- For `L2`, enable web search through Responses API tools where supported.
- Map OpenAI text output into the existing `ProviderResponse` or project-equivalent normalized response.
- Map OpenAI metadata safely into provider metadata.
- Map OpenAI citations/sources into the existing citations/sources shape when available.
- For `L1`, return empty citations/sources unless the API response provides safe source data.
- Return controlled provider errors for:
  - missing/invalid config
  - OpenAI API error
  - timeout
  - rate limit
  - malformed response
  - unsupported SCDL level
  - unsupported web-search mode
- Ensure adapter never leaks the API key in errors, logs, metadata, or test output.
- Add unit/contract tests with mocked internal OpenAI client responses.
- Ensure existing mock provider tests still pass.

### Out of scope
- Do not call the real OpenAI API in automated tests.
- Do not use Chat Completions unless Responses API is unavailable and the task escalates first.
- Do not mock the external OpenAI SDK/network directly when the internal wrapper can be used.
- Do not implement providers other than OpenAI.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change aggregation logic.
- Do not change raw response storage contract.
- Do not change the provider contract unless the task escalates first.
- Do not add frontend UI.
- Do not add billing or cost tracking.
- Do not add user-supplied API keys.
- Do not implement retries beyond existing provider/execution policy unless already required by the provider contract.

### Acceptance criteria
- OpenAI adapter can be selected only when real provider mode is enabled and provider constraints allow it.
- Adapter uses the OpenAI Responses API.
- Adapter depends on an internal OpenAI client wrapper/interface.
- Tests prove the adapter uses the internal client wrapper.
- `L1` request path does not enable web search.
- `L1` request payload does not include web search tools.
- `L2` request path enables web search or returns a controlled unsupported-mode error if web search is unavailable in the configured OpenAI setup.
- `L2` request payload includes the configured web search tool when supported.
- Successful mocked OpenAI response returns a valid normalized provider response.
- Empty or malformed OpenAI response returns a controlled provider error or safe empty response according to existing provider contract.
- Timeout/rate-limit/API errors are normalized into controlled provider errors.
- API key is never included in normalized response, metadata, logs, or errors.
- Existing mock provider behavior remains unchanged.
- Existing parser/scoring/aggregation tests still pass.
- No real external API calls happen in automated tests.

### Test requirements
- Add contract test for successful mocked OpenAI `L1` response.
- Add contract test confirming `L1` request does not include web-search configuration/tools.
- Add contract test for successful mocked OpenAI `L2` response when web-search mode is supported by the adapter.
- Add test confirming `L2` uses web-search configuration/tools or returns controlled unsupported-mode error.
- Add test confirming adapter uses the internal OpenAI client wrapper.
- Add test for mapping text output to normalized `raw_answer`.
- Add test for mapping citations/sources when mocked response includes them.
- Add test for empty/malformed mocked response.
- Add test for timeout handling.
- Add test for rate-limit/API error handling.
- Add test confirming API key is not exposed in errors/metadata.
- Add regression test confirming mock provider path is unchanged.
- Add assertion or mock guard confirming no real OpenAI API call is made.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...providers/openai...`
- `apps/api/...providers...`
- `apps/api/...config...`
- `tests/...providers...`
- `tests/...execution...`
- `tests/...fixtures...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend provider contract tests
- backend execution tests affected by provider selection
- backend parser/scoring regression tests if provider response shape changed
- backend lint/typecheck commands if available

### Dependencies
- TASK-128 — Define real provider pilot constraints
- TASK-129 — Add OpenAI secrets and provider config handling

### Escalate if
- Existing provider contract cannot represent OpenAI L2 web citations/sources.
- The selected OpenAI API/model does not support web search in the intended way.
- The Responses API cannot be used for the intended L1/L2 implementation.
- Implementing L2 requires a different provider response shape.
- Mapping OpenAI response requires changing parser, scoring, aggregation, or raw response storage contracts.
- The adapter needs network calls in automated tests.
- OpenAI SDK/version choice is unclear or conflicts with the project dependency policy.
- Web-search usage requires product/cost/risk approval not present in the task.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document which OpenAI model/config is used for L1 and L2.
- Document that the adapter uses OpenAI Responses API.
- Document whether L2 web-search mode is implemented or returns a controlled unsupported-mode error.
- Confirm in the PR summary that automated tests do not call the real OpenAI API.

---

## TASK-131 — Add real-provider dry-run mode

### Status
Ready

### Goal
Add a controlled dry-run mode for executing a small OpenAI real-provider audit locally without changing production defaults or bypassing safety limits.

### Why
Before running larger real audits, the project needs a safe way to verify the OpenAI adapter, SCDL L1/L2 execution, raw response storage, parser, scoring, aggregation, and UI flow on a tiny real-data sample.

### Context
TASK-128 defined real-provider pilot constraints. TASK-129 added OpenAI config handling. TASK-130 implemented the OpenAI adapter for L1 and L2. This task adds a local/dev execution path for one small controlled real-provider audit. Mock mode must remain the default.

### Scope
- Add a dry-run execution mode for local/dev real-provider testing.
- Require explicit enablement before any real OpenAI request can run.
- Use the existing audit pipeline entry point where possible.
- Dry-run must call the same real-provider policy guard used by run trigger.
- Dry-run must reject mixed provider lists.
- Enforce real-provider caps from TASK-128:
  - allowed provider: OpenAI only
  - limited query count
  - limited runs per query
  - limited total real runs per audit
- Support dry-run execution for:
  - SCDL `L1` without web search
  - SCDL `L2` with web search if supported by TASK-130
- Add a clear command, endpoint, admin/dev-only path, or documented local procedure for running one dry-run audit.
- Log safe execution metadata:
  - audit id
  - provider mode
  - provider
  - configured caps
  - SCDL level
  - query count
  - runs per query
  - total run count
  - success/error counts
- Do not log prompts, full raw answers, API keys, or sensitive provider config unless the project already has an explicit safe debug mode.
- Add tests proving dry-run safety behavior without calling the real OpenAI API.
- Document how to run the dry-run locally.

### Out of scope
- Do not enable real provider mode by default.
- Do not remove or weaken mock provider behavior.
- Do not create a public user-facing “real provider” switch unless already part of the approved UI.
- Do not add billing, cost accounting, user quotas, or paid plan enforcement.
- Do not implement providers other than OpenAI.
- Do not change parser, scoring, aggregation, provider contract, or raw response storage contracts.
- Do not add broad E2E coverage for real provider calls.
- Do not run real OpenAI calls in automated tests.
- Do not expose raw provider answers publicly.

### Acceptance criteria
- Real-provider dry-run cannot run unless explicitly enabled.
- Dry-run calls the same real-provider policy guard used by run trigger or the project-equivalent execution path.
- Dry-run uses OpenAI only.
- Dry-run rejects mixed provider lists.
- Dry-run enforces configured real-provider caps.
- Dry-run supports L1 and L2 according to the OpenAI adapter capabilities.
- Dry-run returns or logs controlled status information for success and failure.
- Dry-run stores raw responses through the existing raw response path when an actual local run is executed.
- Dry-run does not expose API keys or secrets.
- Mock provider mode remains the default and still works.
- Automated tests do not call the real OpenAI API.
- Local dry-run procedure is documented.

### Test requirements
- Add test confirming dry-run is blocked when real provider mode is disabled.
- Add test confirming dry-run accepts OpenAI only.
- Add test confirming dry-run rejects mixed provider lists.
- Add test confirming query/run caps are enforced.
- Add test confirming L1 dry-run path selects no-web mode.
- Add test confirming L2 dry-run path selects web-enabled mode or controlled unsupported behavior.
- Add test confirming dry-run uses the existing provider adapter interface with a mocked OpenAI adapter/client.
- Add test confirming dry-run uses the real-provider policy guard.
- Add test confirming safe metadata is returned/logged without API key exposure.
- Add regression test confirming mock provider execution path is unchanged.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...providers...`
- `apps/api/...orchestrator...`
- `apps/api/...routes/audits...`
- `apps/api/...commands...`
- `apps/api/...config...`
- `tests/...providers...`
- `tests/...execution...`
- `tests/...api...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend provider tests
- backend execution/orchestrator tests
- backend audit API tests affected by run trigger or dry-run path
- backend lint/typecheck commands if available

### Dependencies
- TASK-128 — Define real provider pilot constraints
- TASK-129 — Add OpenAI secrets and provider config handling
- TASK-130 — Implement OpenAI real provider adapter for L1 and L2

### Escalate if
- There is no safe existing pipeline entry point for dry-run execution.
- Dry-run requires a new queue/background worker system.
- The dry-run path would need to bypass raw response storage.
- L2 web-search behavior is unsupported or ambiguous after TASK-130.
- Safe logging requirements conflict with existing observability behavior.
- The implementation would expose secrets, raw provider answers, or provider metadata unsafely.
- Automated tests require real OpenAI network calls.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document the exact local dry-run command or procedure.
- Document required environment variables.
- Confirm in the PR summary that mock mode remains default.
- Confirm in the PR summary that automated tests do not call OpenAI.

---

## TASK-132 — Add raw response inspection screen/log

### Status
Ready

### Goal
Add a safe raw response inspection path for local/dev real-provider pilot analysis.

### Why
Real OpenAI responses must be inspectable during the pilot so parser, scoring, aggregation, citations, and UI behavior can be compared against the actual provider output without guessing where errors originate.

### Context
TASK-130 adds the OpenAI adapter. TASK-131 adds dry-run execution. The project already stores raw responses as a core audit invariant. This task adds a controlled way to inspect stored raw responses for pilot/debug purposes only. It must not expose secrets, provider keys, or unsafe raw data publicly.

### Scope
- Add one safe raw response inspection mechanism, such as:
  - dev/admin-only backend endpoint
  - local CLI/debug command
  - backend log/report file generated during dry-run
  - minimal internal UI panel if already consistent with the current frontend structure
- Use existing stored `RawResponse` records or project-equivalent raw storage.
- Allow inspection by audit id and/or run id.
- Include useful debug fields where available:
  - audit id
  - query
  - provider
  - SCDL level
  - run number
  - run status
  - raw answer preview or full raw answer only if access is restricted
  - citations/sources
  - provider metadata with secrets removed
  - error object if present
  - response time if available
  - created timestamp
- Redact or omit secrets and provider credentials.
- Ensure inspection path is restricted to local/dev/admin usage.
- Add tests for access control/redaction behavior where applicable.
- Document how to use the inspection mechanism during the real-provider pilot.

### Out of scope
- Do not expose raw responses publicly to regular users unless an explicit product decision exists.
- Do not add export to PDF/DOCX/Excel.
- Do not add new parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not call the real OpenAI API in tests.
- Do not store extra copies of raw answers outside the approved raw response storage unless explicitly documented as a local-only debug artifact.
- Do not expose API keys, request headers, auth cookies, or provider secrets.

### Acceptance criteria
- A developer/admin can inspect stored raw responses for a pilot audit.
- Raw response inspection uses existing stored raw response data.
- Inspection output includes enough context to compare raw → parsed → score behavior.
- Secrets and provider credentials are not exposed.
- Regular unauthorized users cannot access raw response inspection if implemented as an endpoint/UI.
- Missing raw responses return a controlled not-found or empty result.
- Error runs are inspectable.
- Existing audit results/summary behavior remains unchanged.
- Automated tests do not call the real OpenAI API.

### Test requirements
- Add test for inspecting a stored successful raw response.
- Add test for inspecting an error raw response if raw error storage exists.
- Add test for missing raw response behavior.
- Add test or assertion confirming provider secrets/API keys are redacted or absent.
- Add access-control test if implemented as an endpoint or UI.
- Add regression test confirming existing results/summary endpoints are unchanged.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/debug...`
- `apps/api/...routes/audits...`
- `apps/api/...raw_responses...`
- `apps/api/...repositories...`
- `apps/web/src/...debug...` if a minimal UI is chosen
- `tests/...raw_responses...`
- `tests/...api...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend raw response / audit API tests
- backend auth/access-control tests if an endpoint is added
- frontend tests if a UI panel is added
- backend/frontend lint/typecheck commands affected by the chosen implementation

### Dependencies
- TASK-130 — Implement OpenAI real provider adapter for L1 and L2
- TASK-131 — Add real-provider dry-run mode

### Escalate if
- Raw response storage does not contain enough data for inspection.
- Access-control requirements for raw answers are unclear.
- Product requires regular users to see full raw provider answers.
- Inspecting raw responses would expose sensitive provider metadata.
- A UI screen is requested but no admin/dev-only route convention exists.
- The implementation requires changing raw response storage or parser/scoring contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document the inspection path and intended local/dev/admin use.
- Document what fields are intentionally redacted or omitted.
- Confirm in the PR summary that automated tests do not call OpenAI.

---

## TASK-133 — Run first real OpenAI audit pilot

### Status
Ready

### Goal
Run the first controlled real OpenAI audit pilot using both SCDL `L1` and `L2` modes on a very small query set.

### Why
The project needs a real-data validation pass to confirm that the OpenAI adapter, dry-run mode, raw response storage, parser, scoring, aggregation, and UI can work together beyond mocked data.

### Context
TASK-128 defined real-provider pilot constraints. TASK-129 added OpenAI secrets/config handling. TASK-130 implemented the OpenAI adapter. TASK-131 added dry-run mode. TASK-132 added raw response inspection.

This task is an execution and documentation task. It may include small bug fixes only when they are required to complete the pilot and remain within the pilot scope.

### Scope
- Configure local/dev environment for real OpenAI pilot execution.
- Use OpenAI as the only real provider.
- Run one small `L1` pilot audit with:
  - max 1 provider
  - max 3–5 queries
  - max 1–2 runs per query, but prefer the configured pilot default of 1
- Run one small `L2` pilot audit with:
  - max 1 provider
  - max 3–5 queries
  - max 1–2 runs per query, but prefer the configured pilot default of 1
- Use a controlled test brand and non-sensitive queries.
- Confirm pilot caps are enforced before execution.
- Confirm raw responses are stored.
- Inspect raw responses using the TASK-132 inspection path.
- Confirm parser produces parsed results.
- Confirm scoring produces bounded scores.
- Confirm aggregation produces summary/results.
- Confirm frontend can display the pilot audit status, summary, results, competitors, and sources where available.
- Record findings in a pilot notes document, for example `docs/REAL_PROVIDER_PILOT_NOTES.md`.
- Record any bugs discovered as follow-up tasks or bug entries instead of expanding this task.

### Out of scope
- Do not run large audits.
- Do not test multiple real providers.
- Do not increase real-provider caps.
- Do not add billing, quotas, or production usage logic.
- Do not use real customer data.
- Do not commit real API keys, raw secrets, or sensitive provider data.
- Do not rewrite parser/scoring based on pilot findings in this task.
- Do not change scoring formulas unless a blocking bug prevents pilot completion and escalation approves it.
- Do not add new UI features beyond minimal fixes required to inspect pilot results.
- Do not run real provider calls in automated tests.

### Acceptance criteria
- One small real OpenAI `L1` pilot audit is executed successfully or fails with a controlled documented provider error.
- One small real OpenAI `L2` pilot audit is executed successfully or fails with a controlled documented provider error.
- Pilot execution respects configured real-provider caps.
- Raw responses are stored for executed runs.
- Raw responses are inspectable without exposing secrets.
- Parser/scoring/aggregation run on the stored real responses.
- Final scores remain bounded to `[0,1]`.
- Frontend can display the pilot audit data or a controlled empty/error state.
- Pilot findings are documented.
- Any discovered issues are recorded as follow-up bugs/tasks.
- No secrets or real API keys are committed.

### Test requirements
- No automated test is required to call the real OpenAI API.
- Run existing backend provider/execution tests before the pilot.
- Run existing parser/scoring/aggregation tests before or after the pilot.
- Run existing frontend build/tests if pilot-related UI fixes are made.
- Manually verify the L1 pilot flow.
- Manually verify the L2 pilot flow.
- Manually verify raw response inspection.
- Manually verify that no API key or secret appears in logs, UI, raw inspection output, or committed files.
- Document the exact commands/manual steps used for the pilot.

### Files likely affected
Optional hint, not a hard boundary.
- `docs/REAL_PROVIDER_PILOT_NOTES.md`
- local `.env` file, not committed
- `docs/...`
- small backend/frontend fix files only if required to complete the pilot

### Commands
Use project commands from `/AGENTS.md`.

At minimum, before or after pilot execution run:
- backend provider/execution tests
- backend parser/scoring/aggregation tests
- frontend tests/build if UI was changed

The real OpenAI pilot command/procedure must be documented in the pilot notes.

### Dependencies
- TASK-128 — Define real provider pilot constraints
- TASK-129 — Add OpenAI secrets and provider config handling
- TASK-130 — Implement OpenAI real provider adapter for L1 and L2
- TASK-131 — Add real-provider dry-run mode
- TASK-132 — Add raw response inspection screen/log

### Escalate if
- L1 or L2 execution requires increasing pilot caps.
- L2 web search is not supported by the configured OpenAI model/API.
- Real responses cannot be represented by the existing provider contract.
- Raw responses are not stored.
- Parser/scoring cannot process real responses without contract changes.
- Any secret appears in logs, UI, raw inspection output, tests, or committed files.
- The pilot requires real customer data.
- A bug fix would require changing parser, scoring, aggregation, provider, raw response, or audit state contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- `docs/REAL_PROVIDER_PILOT_NOTES.md` includes:
  - environment mode used
  - provider and model names
  - OpenAI API family used
  - SCDL levels tested
  - query count and runs per query
  - whether L1 succeeded
  - whether L2 succeeded
  - raw response inspection result
  - parser/scoring/aggregation observations
  - UI observations
  - follow-up bugs/tasks
- PR summary confirms no real API keys or secrets were committed.

---

## TASK-134 — Compare parser and scoring behavior on real OpenAI responses

### Status
Ready

### Goal
Evaluate how the existing parser, scoring, aggregation, and UI behave on real OpenAI `L1` and `L2` pilot responses.

### Why
Real provider output may differ from mock data, so the project needs a structured comparison before changing parser/scoring logic or expanding to more providers.

### Context
TASK-133 executed the first controlled real OpenAI audit pilot and documented raw responses, parsed results, scores, summaries, and UI observations. This task is an analysis and follow-up planning task. It should identify gaps and propose next tasks, not immediately rewrite parser or scoring logic.

### Scope
- Review stored raw OpenAI `L1` and `L2` responses from the pilot.
- Compare each raw response against its parsed result.
- Compare each parsed result against its score.
- Compare per-run scores against aggregate query/provider/audit summaries.
- Compare backend results against frontend display.
- Identify parser mismatches, such as:
  - missed brand mentions
  - false brand mentions
  - missed competitors
  - incorrect rank/position
  - missed citations/sources
  - malformed source handling
  - sentiment/recommendation misclassification
- Identify scoring mismatches, such as:
  - unreasonable final score
  - incorrect visibility cap behavior
  - component score inconsistency
  - score not matching parsed signals
- Identify L1 versus L2 differences:
  - web-enabled source availability
  - citation quality
  - brand visibility differences
  - competitor differences
  - parser behavior differences
- Identify UI display issues caused by real response shapes.
- Document findings in `docs/REAL_PROVIDER_PILOT_NOTES.md` or a follow-up analysis document.
- Create concrete follow-up task proposals for any parser, scoring, aggregation, provider, or UI fixes.

### Out of scope
- Do not change parser logic in this task.
- Do not change scoring formulas in this task.
- Do not change aggregation logic in this task.
- Do not change provider adapter behavior in this task unless a tiny documentation-only correction is needed.
- Do not run large additional real-provider audits.
- Do not add new providers.
- Do not increase pilot caps.
- Do not implement UI redesign.
- Do not add AI-generated recommendations.
- Do not make product decisions silently.

### Acceptance criteria
- At least one `L1` real OpenAI response is compared raw → parsed → scored → displayed, if available from the pilot.
- At least one `L2` real OpenAI response is compared raw → parsed → scored → displayed, if available from the pilot.
- Parser issues are classified as false positive, false negative, missing extraction, malformed source handling, or acceptable behavior.
- Scoring issues are classified as formula issue, component issue, visibility issue, aggregation issue, or acceptable behavior.
- L1/L2 differences are documented.
- UI issues caused by real data are documented separately from backend parser/scoring issues.
- Follow-up fixes are written as concrete task proposals or bug entries.
- No parser/scoring/provider contract changes are made in this task.
- No secrets or API keys are included in the analysis document.

### Test requirements
- No new automated tests are required if this task only documents analysis.
- If tiny non-behavioral documentation or fixture changes are made, run relevant docs/static checks if available.
- Manually verify that cited pilot examples exist in stored raw response inspection or pilot notes.
- Manually verify that no API keys, secrets, or sensitive raw data are included in committed documentation.
- If follow-up fixtures are added from real responses, redact sensitive data and add a reviewer note explaining what was redacted.

### Files likely affected
Optional hint, not a hard boundary.
- `docs/REAL_PROVIDER_PILOT_NOTES.md`
- `docs/REAL_RESPONSE_ANALYSIS.md`
- `docs/TASKS.md` or follow-up task backlog
- redacted fixtures only if explicitly needed

### Commands
Use project commands from `/AGENTS.md`.

If this is documentation-only, no full test run is required unless project policy requires it.

If fixtures or code are changed, run the relevant backend/frontend tests affected by those changes.

### Dependencies
- TASK-133 — Run first real OpenAI audit pilot

### Escalate if
- Pilot data is unavailable or incomplete.
- Real OpenAI responses cannot be inspected safely.
- Real response data contains sensitive information that cannot be committed.
- L1 or L2 behavior is too ambiguous to evaluate without a product decision.
- Parser/scoring fixes are urgently required before analysis can be completed.
- Follow-up changes would require altering parser, scoring, aggregation, provider, raw response, or audit state contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Analysis document clearly separates:
  - provider adapter issues
  - parser issues
  - scoring issues
  - aggregation issues
  - UI issues
  - product/question-design issues
- Follow-up work is listed as concrete tasks or bug entries.
- PR summary confirms no secrets or API keys were committed.

---

## Phase G — Post-pilot stabilization

Tasks in this phase must be written only after TASK-133 and TASK-134 are complete.

Potential areas:
- OpenAI adapter fixes
- OpenAI L2 citation/source mapping fixes
- parser improvements based on real responses
- scoring calibration
- aggregation fixes for real response shapes
- redacted real-response fixtures
- UI fixes for real response shapes
- second provider integration
