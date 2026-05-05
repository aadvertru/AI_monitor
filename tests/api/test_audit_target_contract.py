from __future__ import annotations

import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    AuditCreateRequest,
    AuditEstimateRequest,
    build_audit_detail_response,
    create_audit_record,
    estimate_audit_payload,
)
from libs.control.job_scheduler import schedule_jobs_for_audit
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.worker import execute_job
from libs.storage.models import (
    Audit,
    AuditTarget,
    Base,
    Brand,
    Job,
    Query,
    RawResponse,
    Run,
    User,
    UserRole,
)
from tests.audit_target_fixtures import (
    BACKEND_AUDIT_TARGET_FIXTURES,
    LEGACY_SINGLE_PROVIDER_L1,
    TWO_OPENROUTER_SAME_LEVEL_TARGETS,
)


class _RecordingProvider(BaseProviderAdapter):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        self.calls.append({"query": query, **kwargs})
        return ProviderResponse(
            status="success",
            raw_answer=f"Answer for {query}",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata={
                "provider": kwargs.get("execution_provider"),
                "model_id": kwargs.get("model_id"),
                "model_provider": kwargs.get("model_provider"),
                "gateway": kwargs.get("gateway"),
                "gateway_l2_experimental": kwargs.get("gateway_l2_experimental"),
            },
        )


class AuditTargetContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

        @event.listens_for(self.engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(self) -> User:
        async with self.session_factory() as session:
            user = User(
                email="target-contract@example.com",
                hashed_password="hashed",
                role=UserRole.USER,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def test_backend_fixture_payloads_are_schema_stable(self) -> None:
        for name, fixture in BACKEND_AUDIT_TARGET_FIXTURES.items():
            with self.subTest(name=name):
                payload = AuditCreateRequest.model_validate(deepcopy(fixture))
                self.assertGreater(len(payload.seed_queries or []), 0)
                if payload.model_targets:
                    self.assertIsNone(payload.providers)
                    self.assertGreater(len(payload.model_targets), 0)
                    for target in payload.model_targets:
                        self.assertIn(target.level, {"L1", "L2"})
                        if target.gateway_l2_experimental:
                            self.assertEqual(target.level, "L2")
                else:
                    self.assertGreater(len(payload.providers or []), 0)

    async def test_legacy_conversion_and_canonical_detail_are_stable(self) -> None:
        user = await self._create_user()
        async with self.session_factory() as session:
            legacy = await create_audit_record(
                session,
                AuditCreateRequest.model_validate(deepcopy(LEGACY_SINGLE_PROVIDER_L1)),
                user_id=user.id,
            )
            canonical = await create_audit_record(
                session,
                AuditCreateRequest.model_validate(
                    deepcopy(TWO_OPENROUTER_SAME_LEVEL_TARGETS)
                ),
                user_id=user.id,
            )

            legacy_audit = await session.get(Audit, legacy.audit_id)
            canonical_audit = await session.get(Audit, canonical.audit_id)
            assert legacy_audit is not None
            assert canonical_audit is not None
            legacy_brand = await session.get(Brand, legacy_audit.brand_id)
            canonical_brand = await session.get(Brand, canonical_audit.brand_id)
            assert legacy_brand is not None
            assert canonical_brand is not None

            legacy_detail = await build_audit_detail_response(
                session,
                legacy_audit,
                legacy_brand,
            )
            canonical_detail = await build_audit_detail_response(
                session,
                canonical_audit,
                canonical_brand,
            )

        self.assertEqual(len(legacy_detail.model_targets), 1)
        self.assertEqual(legacy_detail.model_targets[0].model_id, "mock")
        self.assertEqual(legacy_detail.providers, ["mock"])
        self.assertEqual(canonical_detail.providers, ["openrouter"])
        self.assertEqual(len(canonical_detail.model_targets), 2)
        self.assertEqual(
            {target.model_id for target in canonical_detail.model_targets},
            {"openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"},
        )

    async def test_existing_legacy_audit_without_targets_remains_readable(self) -> None:
        user = await self._create_user()
        async with self.session_factory() as session:
            brand = Brand(name="Legacy DB", domain="legacy.example")
            audit = Audit(brand=brand, providers=["mock"], runs_per_query=1, user_id=user.id)
            session.add_all([brand, audit])
            await session.flush()
            session.add(Query(audit_id=audit.id, text="legacy query"))
            await session.commit()
            await session.refresh(audit)

            detail = await build_audit_detail_response(session, audit, brand)

        self.assertEqual(detail.providers, ["mock"])
        self.assertEqual(detail.model_targets, [])
        self.assertEqual(detail.seed_queries, ["legacy query"])

    async def test_caps_fixture_reports_stable_over_cap_violation(self) -> None:
        estimate = AuditEstimateRequest.model_validate(
            {
                "seed_queries": ["query one", "query two", "query three"],
                "runs_per_query": 5,
                "model_targets": deepcopy(
                    TWO_OPENROUTER_SAME_LEVEL_TARGETS["model_targets"]
                ),
            }
        )

        with patch.dict(
            "os.environ",
            {
                "MAX_QUERIES_PER_AUDIT": "2",
                "MAX_TOTAL_RUNS_PER_AUDIT": "20",
            },
            clear=False,
        ):
            result = estimate_audit_payload(estimate)

        self.assertTrue(result.over_cap)
        self.assertEqual(result.query_count, 3)
        self.assertEqual(result.target_count, 2)
        self.assertEqual(result.model_count, 2)
        self.assertEqual(result.estimated_runs, 30)
        self.assertEqual(
            {violation.code for violation in result.violations},
            {"MAX_QUERIES_PER_AUDIT_EXCEEDED", "MAX_TOTAL_RUNS_EXCEEDED"},
        )

    async def test_scheduling_expands_queries_by_targets_and_preserves_target_id(
        self,
    ) -> None:
        user = await self._create_user()
        payload = deepcopy(TWO_OPENROUTER_SAME_LEVEL_TARGETS)
        payload["seed_queries"] = ["query one", "query two"]

        async with self.session_factory() as session:
            created = await create_audit_record(
                session,
                AuditCreateRequest.model_validate(payload),
                user_id=user.id,
            )
            await session.run_sync(schedule_jobs_for_audit, created.audit_id)
            jobs = (
                await session.execute(
                    select(Job).where(Job.audit_id == created.audit_id).order_by(Job.id)
                )
            ).scalars().all()
            targets = (
                await session.execute(
                    select(AuditTarget)
                    .where(AuditTarget.audit_id == created.audit_id)
                    .order_by(AuditTarget.id)
                )
            ).scalars().all()

        self.assertEqual(len(jobs), 4)
        self.assertEqual({job.audit_target_id for job in jobs}, {target.id for target in targets})
        self.assertEqual(len({job.idempotency_key for job in jobs}), 4)

    async def test_provider_request_uses_each_same_level_target_model_id(self) -> None:
        user = await self._create_user()
        async with self.session_factory() as session:
            created = await create_audit_record(
                session,
                AuditCreateRequest.model_validate(
                    deepcopy(TWO_OPENROUTER_SAME_LEVEL_TARGETS)
                ),
                user_id=user.id,
            )
            await session.run_sync(schedule_jobs_for_audit, created.audit_id)
            jobs = (
                await session.execute(
                    select(Job).where(Job.audit_id == created.audit_id).order_by(Job.id)
                )
            ).scalars().all()
            provider = _RecordingProvider()
            for job in jobs:
                await execute_job(session, job.id, provider)

            runs = (
                await session.execute(
                    select(Run).where(Run.audit_id == created.audit_id).order_by(Run.id)
                )
            ).scalars().all()
            raw_responses = (
                await session.execute(
                    select(RawResponse)
                    .join(Run, RawResponse.run_id == Run.id)
                    .where(Run.audit_id == created.audit_id)
                    .order_by(RawResponse.id)
                )
            ).scalars().all()

        self.assertEqual(
            {call["model_id"] for call in provider.calls},
            {"openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"},
        )
        self.assertEqual(
            {run.audit_target_id for run in runs},
            {job.audit_target_id for job in jobs},
        )
        self.assertEqual(
            {raw.request_snapshot["model_id"] for raw in raw_responses},
            {"openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"},
        )
        self.assertTrue(all(raw.provider_metadata["gateway"] for raw in raw_responses))

    async def test_fixtures_do_not_contain_raw_provider_payloads_or_secrets(self) -> None:
        dumped = json.dumps(BACKEND_AUDIT_TARGET_FIXTURES).lower()

        for forbidden in (
            "raw_answer",
            "raw_response",
            "raw_prompt",
            "authorization",
            "api_key",
            "secret",
            "sk-",
        ):
            self.assertNotIn(forbidden, dumped)


if __name__ == "__main__":
    unittest.main()
