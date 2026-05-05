# Active Context

Last updated: 2026-05-05

## Current Project State

AI Brand Visibility Monitor has a working SCDL audit flow with:

- FastAPI backend with async SQLAlchemy.
- React/Vite frontend in `apps/web`.
- Email/password auth with httpOnly cookie session.
- User-owned audits with admin access where implemented.
- Audit create/edit/list/detail/summary/results/sources UI.
- One-click audit pipeline from UI: schedule, execute provider jobs, post-process, score, and update status.
- OpenAI as the current baseline real provider.
- Mock provider for deterministic local/test execution.

## Current Provider Status

OpenAI:

- Baseline status: ready with known limitations.
- L1: implemented and manually verified.
- L2: implemented and manually verified.
- Provider errors are normalized.
- Provider diagnostics are exposed through API and rendered safely in UI.
- Automated tests must not call real OpenAI APIs.

Mock:

- Required for tests/dev.
- Must not be used as silent fallback when a real provider is configured.

OpenRouter:

- Active gateway provider integration with mocked backend coverage.
- Gateway provider for many L1 model comparisons through one key.
- L1 runs without web access/tools/search.
- L2 is experimental through OpenRouter web-search server tool behavior.
- Live OpenRouter L1 verification passed locally with routed Gemini/Claude-style
  model ids after correcting model configuration.
- Live OpenRouter L2 source/citation verification is still pending.
- Native provider/source parity is not assumed.

Anthropic/Claude:

- Native branch implemented or partially implemented but not live-verified.
- Native Anthropic is deferred while OpenRouter gateway integration is active.
- Claude L1 may be tested through OpenRouter model ids.
- Native Claude L2 remains future work unless a task explicitly reactivates it.

## Important Product Rules

- Frontend must never call provider APIs directly.
- Parser/scoring must not depend on frontend behavior.
- Do not expose raw provider responses, raw prompts, request headers, stack traces, API keys, or secrets.
- Do not silently fallback from one provider to another.
- No real external provider calls in automated tests.
- Keep changes task-scoped and reviewable.

## Active Docs

Use these as the current source of truth:

- `docs/PROVIDER_CONTRACT.md` for provider adapter rules.
- `docs/PROVIDER_PARITY.md` for provider readiness criteria.
- `docs/OPENAI_ONE_CLICK_VERIFICATION_RESULTS.md` for current OpenAI baseline evidence.
- `docs/CLAUDE_READINESS_DECISION.md` for historical Claude readiness scope.
- `docs/OPENROUTER_GATEWAY_VERIFICATION.md` for current OpenRouter live verification status.
- `docs/phase_l_openrouter_tasks/` for OpenRouter gateway task contracts.

Avoid reading archived or old task files unless the user explicitly asks.

## Current Working Mode

The user plans to give one task at a time, usually pointing to one task file or one task section.

Recommended approach:

1. Read only the requested task file or the specific task section.
2. Inspect only directly relevant code.
3. Implement the task.
4. Run task-scoped tests.
5. Report concise summary and verification.

## Common Verification Commands

Backend:

```powershell
.\venv\Scripts\python.exe -m pytest tests\execution
.\venv\Scripts\python.exe -m pytest tests\api\test_audit_read_run_results.py tests\api\test_audit_schemas.py
.\venv\Scripts\python.exe -m ruff check apps\api libs\execution tests\api tests\execution
```

Frontend:

```powershell
cd apps\web
npm test -- src/features/audits/AuditDetailPage.test.tsx src/features/audits/AuditSummaryPage.test.tsx src/features/audits/AuditResultsPage.test.tsx src/test/fixtures.test.ts src/lib/api/client.test.ts
npm run typecheck
npm run build
```

Use narrower commands when a task touches fewer files.

## Local Noise To Ignore

Ignore unrelated dirty or generated files unless the user asks:

- `.claude/worktrees/*`
- `.pytest_cache/`
- `pytest-cache-files-*`
- `__pycache__/`
- `.ruff_cache/`
- `apps/web/dist/`
- Vite cache files

Do not delete local database files or virtual environments unless explicitly asked.
