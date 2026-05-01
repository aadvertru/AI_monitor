from __future__ import annotations

import unittest
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.execution.audit_execution import execute_audit_jobs
from libs.execution.dry_run import execute_real_provider_dry_run
from libs.execution.pilot_config import PilotPolicyError, RealProviderPilotConfig
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    Query,
    RawResponse,
    Run,
    SCDLLevel,
)


class _RecordingProvider(BaseProviderAdapter):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        self.calls.append({"query": query, **kwargs})
        return ProviderResponse(
            status="success",
            raw_answer=f"Answer: {query}",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata={"provider": "openai", "mode": kwargs.get("scdl_level")},
        )


class RealProviderDryRunTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.session: AsyncSession = self.session_factory()

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _create_audit(
        self,
        *,
        providers: list[str] | None = None,
        query_texts: list[str] | None = None,
        runs_per_query: int = 1,
        scdl_level: SCDLLevel = SCDLLevel.L1,
    ) -> Audit:
        brand = Brand(name="Acme AI")
        audit = Audit(
            brand=brand,
            providers=providers or ["openai"],
            runs_per_query=runs_per_query,
            scdl_level=scdl_level,
            status=AuditStatus.CREATED,
        )
        self.session.add(audit)
        await self.session.flush()
        for query_text in query_texts or ["best ai monitoring tools"]:
            self.session.add(Query(audit_id=audit.id, text=query_text))
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def test_dry_run_is_blocked_when_real_provider_mode_is_disabled(self) -> None:
        audit = await self._create_audit()

        with self.assertRaisesRegex(PilotPolicyError, "dry-run is disabled"):
            await execute_real_provider_dry_run(self.session, audit.id)

    async def test_dry_run_accepts_openai_only_and_rejects_mixed_providers(self) -> None:
        audit = await self._create_audit(providers=["openai", "mock"])

        with self.assertRaisesRegex(PilotPolicyError, "mixed provider lists"):
            await execute_real_provider_dry_run(
                self.session,
                audit.id,
                pilot_config=_enabled_openai_config(),
            )

    async def test_dry_run_enforces_query_and_run_caps(self) -> None:
        audit = await self._create_audit(
            query_texts=["one", "two"],
            runs_per_query=1,
        )

        with self.assertRaisesRegex(PilotPolicyError, "max queries"):
            await execute_real_provider_dry_run(
                self.session,
                audit.id,
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openai",
                    max_queries=1,
                    max_runs_per_query=1,
                    max_total_runs=5,
                ),
            )

    async def test_l1_dry_run_selects_no_web_mode_through_worker_context(self) -> None:
        audit = await self._create_audit(scdl_level=SCDLLevel.L1)
        provider = _RecordingProvider()

        result = await execute_real_provider_dry_run(
            self.session,
            audit.id,
            pilot_config=_enabled_openai_config(),
            provider_factory=lambda _provider_code: provider,
        )

        self.assertEqual(result.audit_status, "completed")
        self.assertEqual(provider.calls[0]["scdl_level"], "L1")

    async def test_l2_dry_run_selects_web_enabled_mode_through_worker_context(self) -> None:
        audit = await self._create_audit(scdl_level=SCDLLevel.L2)
        provider = _RecordingProvider()

        result = await execute_real_provider_dry_run(
            self.session,
            audit.id,
            pilot_config=_enabled_openai_config(),
            provider_factory=lambda _provider_code: provider,
        )

        self.assertEqual(result.audit_status, "completed")
        self.assertEqual(provider.calls[0]["scdl_level"], "L2")

    async def test_dry_run_uses_existing_worker_and_persists_raw_response(self) -> None:
        audit = await self._create_audit(query_texts=["one", "two"])
        provider = _RecordingProvider()

        result = await execute_real_provider_dry_run(
            self.session,
            audit.id,
            pilot_config=_enabled_openai_config(),
            provider_factory=lambda _provider_code: provider,
        )

        runs = (
            await self.session.execute(select(Run).where(Run.audit_id == audit.id))
        ).scalars().all()
        raw_responses = (
            await self.session.execute(
                select(RawResponse).where(RawResponse.run_id.in_([run.id for run in runs]))
            )
        ).scalars().all()
        self.assertEqual(result.executed_jobs, 2)
        self.assertEqual(result.success_count, 2)
        self.assertEqual(len(raw_responses), 2)

    async def test_dry_run_reuses_audit_job_execution_service(self) -> None:
        audit = await self._create_audit()
        provider = _RecordingProvider()

        with patch(
            "libs.execution.dry_run.execute_audit_jobs",
            wraps=execute_audit_jobs,
        ) as execution_service:
            result = await execute_real_provider_dry_run(
                self.session,
                audit.id,
                pilot_config=_enabled_openai_config(),
                provider_factory=lambda _provider_code: provider,
            )

        self.assertEqual(result.audit_status, "completed")
        execution_service.assert_called_once()

    async def test_safe_metadata_does_not_expose_api_key(self) -> None:
        audit = await self._create_audit()
        provider = _RecordingProvider()

        result = await execute_real_provider_dry_run(
            self.session,
            audit.id,
            pilot_config=_enabled_openai_config(),
            provider_factory=lambda _provider_code: provider,
        )

        self.assertNotIn("api_key", result.safe_log_dict())
        self.assertNotIn("sk-", str(result.safe_log_dict()))


def _enabled_openai_config() -> RealProviderPilotConfig:
    return RealProviderPilotConfig(
        real_provider_enabled=True,
        provider_mode="openai",
        max_providers=1,
        max_queries=5,
        max_runs_per_query=1,
        max_total_runs=5,
    )


if __name__ == "__main__":
    unittest.main()
