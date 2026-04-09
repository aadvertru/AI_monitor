# T1–T15 Quick Verification (repo reality check)

Date: 2026-04-09 (UTC)

## Overall snapshot

The repository contains implementations not only for T1–T15, but also multiple Analysis-layer modules (parser/scoring/aggregation and tests).

## Task-by-task status

- **T1 — Project structure:** **Implemented**.
  - Present: `apps/api`, `libs/control`, `libs/execution`, `libs/analysis`, `libs/storage`, `docs`, scripts, tests.

- **T2 — DB setup:** **Implemented**.
  - DB config and connectivity check exist in `libs/storage/db_config.py` and `libs/storage/db.py`.
  - Connectivity test exists in `tests/storage/test_db_setup.py`.

- **T3 — Core models:** **Implemented**.
  - Models include `Brand`, `Audit`, `Query`, `Run`, `RawResponse`, `ParsedResult`, `Score`, plus `Job`.
  - Relation/constraints tests exist in `tests/storage/test_core_models.py`.

- **T4 — API create audit:** **Implemented**.
  - `POST /audits` and input validation are implemented in `apps/api/main.py`.
  - Happy/invalid tests exist in `tests/api/test_create_audit.py`.

- **T5 — Normalize seed queries:** **Implemented**.
  - Function exists in `libs/control/query_normalization.py`.
  - Tests exist in `tests/control/test_query_normalization.py`.

- **T6 — Deduplicate queries:** **Partially verified**.
  - Function exists in `libs/control/query_deduplication.py`.
  - **Gap:** no dedicated unit test file found for dedup behavior.

- **T7 — Apply max_queries cap:** **Implemented**.
  - Function exists in `libs/control/query_capping.py`.
  - Tests exist in `tests/control/test_query_capping.py`.

- **T8 — Intent tagging:** **Implemented**.
  - Rule-based tagging exists in `libs/control/intent_tagging.py`.
  - Tests exist in `tests/control/test_intent_tagging.py`.

- **T9 — BaseProviderAdapter / ProviderResponse contract:** **Implemented**.
  - Contract is in `libs/execution/provider_adapter.py`.
  - Contract tests are in `tests/execution/test_provider_contract.py`.

- **T10 — Mock provider:** **Implemented**.
  - Adapter exists in `libs/execution/mock_provider.py`.
  - Determinism/mode tests exist in `tests/execution/test_mock_provider.py`.

- **T11 — Real provider (OpenAI):** **Implemented**.
  - Adapter exists in `libs/execution/openai_provider.py`.
  - Success/error/malformed citation tests exist in `tests/execution/test_openai_provider.py`.

- **T12 — Job model:** **Implemented**.
  - `Job` model + idempotency key helper exist in `libs/storage/models.py`.
  - Tests exist in `tests/storage/test_job_model.py`.

- **T13 — Job scheduler:** **Implemented**.
  - Scheduler exists in `libs/control/job_scheduler.py`.
  - Combination/no-duplicates tests exist in `tests/control/test_job_scheduler.py`.

- **T14 — Worker execution:** **Implemented**.
  - Worker flow exists in `libs/execution/worker.py`.
  - Success/error + “does not parse/score” tests exist in `tests/execution/test_worker_execution.py`.

- **T15 — RawResponse storage:** **Implemented with a spec-risk**.
  - RawResponse persistence fields are handled in `libs/execution/worker.py` and model in `libs/storage/models.py`.
  - **Spec-risk:** `RawResponse` can be updated on re-execution in worker (`else:` branch mutates existing row), while architecture notes expect immutable raw payload after write.
  - **Gap:** no explicit immutable-check test found for `RawResponse`.

## Current practical blockers observed locally

- Running `pytest -q` currently fails at collection due to missing environment dependencies (`pydantic`, `sqlalchemy`, `asyncpg`) in the current container.

## Recommended next step before parser block

1. Add/restore project dependency installation (lockfile or requirements/poetry/uv config).
2. Add missing T6 dedup unit tests.
3. Decide/align on `RawResponse` immutability policy and enforce it in code/tests.
4. Then proceed to parser block (T16+).
