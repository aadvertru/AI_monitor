from __future__ import annotations

import unittest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.execution.audit_execution import execute_audit_jobs
from libs.execution.pilot_config import RealProviderPilotConfig
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    Job,
    JobStatus,
    Query,
    RawResponse,
    Run,
    build_job_idempotency_key,
)


class _RecordingProvider(BaseProviderAdapter):
    def __init__(self, response: ProviderResponse | None = None) -> None:
        self.calls: list[dict] = []
        self.response = response or ProviderResponse(
            status="success",
            raw_answer="Acme AI is visible in this answer.",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata={"provider": "mock"},
        )

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        self.calls.append({"query": query, **kwargs})
        return self.response


class _RaisingProvider(BaseProviderAdapter):
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        raise RuntimeError("provider failed with sk-hidden")


class AuditExecutionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.session: AsyncSession = self.session_factory()

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _create_audit_with_job(
        self,
        *,
        brand_name: str = "Acme AI",
        provider: str = "mock",
        job_status: JobStatus = JobStatus.PENDING,
        query_text: str = "best ai monitoring tools",
        runs_per_query: int = 1,
    ) -> tuple[Audit, Job]:
        brand = Brand(name=brand_name)
        audit = Audit(
            brand=brand,
            providers=[provider],
            runs_per_query=runs_per_query,
            status=AuditStatus.RUNNING,
        )
        query = Query(audit=audit, text=query_text)
        self.session.add_all([brand, audit, query])
        await self.session.flush()
        job = Job(
            audit_id=audit.id,
            query_id=query.id,
            provider=provider,
            run_number=1,
            status=job_status,
            idempotency_key=build_job_idempotency_key(audit.id, query.id, provider, 1),
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(audit)
        await self.session.refresh(job)
        return audit, job

    async def test_executes_pending_mock_jobs_for_one_audit(self) -> None:
        audit, job = await self._create_audit_with_job()
        provider = _RecordingProvider()

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        persisted_job = await self.session.get(Job, job.id)
        raw_response = (
            await self.session.execute(select(RawResponse))
        ).scalar_one_or_none()
        self.assertEqual(summary.total_jobs_inspected, 1)
        self.assertEqual(summary.jobs_executed, 1)
        self.assertEqual(summary.jobs_skipped, 0)
        self.assertEqual(summary.success_count, 1)
        self.assertEqual(provider.calls[0]["query"], "best ai monitoring tools")
        assert persisted_job is not None
        self.assertEqual(persisted_job.status, JobStatus.COMPLETED)
        assert raw_response is not None
        self.assertEqual(raw_response.provider_status, "success")

    async def test_jobs_from_another_audit_are_not_executed(self) -> None:
        audit, _job = await self._create_audit_with_job(brand_name="First")
        other_audit, other_job = await self._create_audit_with_job(brand_name="Second")
        provider = _RecordingProvider()

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        persisted_other_job = await self.session.get(Job, other_job.id)
        runs = (
            await self.session.execute(select(Run).where(Run.audit_id == other_audit.id))
        ).scalars().all()
        self.assertEqual(summary.jobs_executed, 1)
        self.assertEqual(len(provider.calls), 1)
        assert persisted_other_job is not None
        self.assertEqual(persisted_other_job.status, JobStatus.PENDING)
        self.assertEqual(runs, [])

    async def test_terminal_jobs_are_skipped(self) -> None:
        audit, job = await self._create_audit_with_job(job_status=JobStatus.COMPLETED)
        provider = _RecordingProvider()

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        self.assertEqual(summary.total_jobs_inspected, 1)
        self.assertEqual(summary.jobs_executed, 0)
        self.assertEqual(summary.jobs_skipped, 1)
        self.assertEqual(provider.calls, [])
        persisted_job = await self.session.get(Job, job.id)
        assert persisted_job is not None
        self.assertEqual(persisted_job.status, JobStatus.COMPLETED)

    async def test_provider_error_is_recorded_as_run_error_without_per_job_failure(
        self,
    ) -> None:
        audit, _job = await self._create_audit_with_job()
        provider = _RecordingProvider(
            ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=0.2,
                error={"code": "mock_error", "message": "Provider failed."},
                provider_metadata={"provider": "mock"},
            )
        )

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        raw_response = (
            await self.session.execute(select(RawResponse))
        ).scalar_one_or_none()
        self.assertEqual(summary.jobs_executed, 1)
        self.assertEqual(summary.success_count, 0)
        self.assertEqual(summary.error_count, 1)
        self.assertEqual(summary.errors, [])
        assert raw_response is not None
        self.assertEqual(raw_response.provider_status, "error")
        self.assertEqual(raw_response.error_object["code"], "mock_error")

    async def test_provider_exception_is_normalized_by_existing_worker_path(self) -> None:
        audit, _job = await self._create_audit_with_job()

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            provider_factory=lambda _provider: _RaisingProvider(),
        )

        raw_response = (
            await self.session.execute(select(RawResponse))
        ).scalar_one_or_none()
        self.assertEqual(summary.jobs_executed, 1)
        self.assertEqual(summary.error_count, 1)
        assert raw_response is not None
        self.assertEqual(raw_response.error_object["code"], "provider_exception")
        self.assertNotIn("sk-hidden", raw_response.error_object["message"])

    async def test_execution_summary_reports_job_factory_errors_safely(self) -> None:
        audit, _job = await self._create_audit_with_job()

        def failing_factory(_provider: str) -> BaseProviderAdapter:
            raise RuntimeError("factory failed with sk-hidden")

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            provider_factory=failing_factory,
        )

        self.assertEqual(summary.jobs_executed, 0)
        self.assertEqual(summary.jobs_skipped, 0)
        self.assertEqual(len(summary.errors), 1)
        self.assertEqual(summary.errors[0].code, "job_execution_error")
        self.assertNotIn("sk-hidden", summary.errors[0].message)

    async def test_openai_execution_is_blocked_when_real_provider_disabled(self) -> None:
        audit, _job = await self._create_audit_with_job(provider="openai")

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=False,
                provider_mode="openai",
            ),
        )

        self.assertEqual(summary.jobs_executed, 0)
        self.assertIn("Real provider execution is disabled", summary.fatal_error or "")

    async def test_real_provider_caps_are_enforced_before_execution(self) -> None:
        audit, _job = await self._create_audit_with_job(
            provider="openai",
            runs_per_query=2,
        )

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="openai",
                max_runs_per_query=1,
            ),
            provider_factory=lambda _provider: _RecordingProvider(),
        )

        self.assertEqual(summary.jobs_executed, 0)
        self.assertIn("max runs per query", summary.fatal_error or "")

    async def test_automated_tests_do_not_need_openai_adapter_for_openai_policy_errors(
        self,
    ) -> None:
        audit, _job = await self._create_audit_with_job(provider="openai")

        summary = await execute_audit_jobs(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="mock",
            ),
            provider_factory=lambda _provider: _RecordingProvider(),
        )

        self.assertIn("Provider mode 'mock'", summary.fatal_error or "")


if __name__ == "__main__":
    unittest.main()
