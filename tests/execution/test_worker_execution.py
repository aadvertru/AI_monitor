from __future__ import annotations

import unittest

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.worker import execute_job
from libs.storage.models import (
    Audit,
    Base,
    Brand,
    Job,
    JobStatus,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    Score,
    build_job_idempotency_key,
)


class _SuccessProvider(BaseProviderAdapter):
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        return ProviderResponse(
            status="success",
            raw_answer=f"Answer for: {query}",
            citations=[{"url": "https://example.com", "title": "Example"}],
            response_time=0.25,
            error=None,
            provider_metadata={"provider": "mock-success"},
        )


class _ErrorProvider(BaseProviderAdapter):
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        return ProviderResponse(
            status="error",
            raw_answer=None,
            citations=None,
            response_time=0.3,
            error={"code": "mock_error", "message": "Provider failed."},
            provider_metadata={"provider": "mock-error"},
        )


class WorkerExecutionTests(unittest.IsolatedAsyncioTestCase):
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
        self.session: AsyncSession = self.session_factory()

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _create_job(self, provider_code: str = "mock") -> Job:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=[provider_code], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring tools")
        self.session.add_all([brand, audit, query])
        await self.session.flush()

        job = Job(
            audit_id=audit.id,
            query_id=query.id,
            provider=provider_code,
            run_number=1,
            status=JobStatus.PENDING,
            idempotency_key=build_job_idempotency_key(audit.id, query.id, provider_code, 1),
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def test_success_flow_persists_run_and_raw_response(self) -> None:
        job = await self._create_job(provider_code="mock")

        run = await execute_job(self.session, job.id, _SuccessProvider())

        persisted_job = await self.session.get(Job, job.id)
        persisted_run = await self.session.get(Run, run.id)
        raw_response = (
            await self.session.execute(select(RawResponse).where(RawResponse.run_id == run.id))
        ).scalar_one_or_none()
        self.assertIsNotNone(persisted_job)
        self.assertIsNotNone(persisted_run)
        self.assertIsNotNone(raw_response)
        assert persisted_job is not None
        assert persisted_run is not None
        assert raw_response is not None

        self.assertEqual(persisted_job.status, JobStatus.COMPLETED)
        self.assertEqual(persisted_run.status, RunStatus.SUCCESS)
        self.assertEqual(raw_response.provider_status, "success")
        self.assertEqual(raw_response.raw_answer, "Answer for: best ai monitoring tools")
        self.assertEqual(raw_response.response_time, 0.25)
        self.assertIsNone(raw_response.error_object)

    async def test_error_flow_still_persists_run_and_raw_response(self) -> None:
        job = await self._create_job(provider_code="mock")

        run = await execute_job(self.session, job.id, _ErrorProvider())

        persisted_job = await self.session.get(Job, job.id)
        persisted_run = await self.session.get(Run, run.id)
        raw_response = (
            await self.session.execute(select(RawResponse).where(RawResponse.run_id == run.id))
        ).scalar_one_or_none()
        assert persisted_job is not None
        assert persisted_run is not None
        assert raw_response is not None

        self.assertEqual(persisted_job.status, JobStatus.FAILED)
        self.assertEqual(persisted_run.status, RunStatus.ERROR)
        self.assertEqual(raw_response.provider_status, "error")
        self.assertIsNone(raw_response.raw_answer)
        self.assertEqual(
            raw_response.error_object,
            {"code": "mock_error", "message": "Provider failed."},
        )

    async def test_worker_does_not_parse_or_score(self) -> None:
        job = await self._create_job(provider_code="mock")
        run = await execute_job(self.session, job.id, _SuccessProvider())

        persisted_run = await self.session.get(Run, run.id)
        assert persisted_run is not None

        parsed_count = (await self.session.execute(
            select(ParsedResult).where(ParsedResult.run_id == run.id)
        )).scalars().all()
        score_count = (await self.session.execute(
            select(Score).where(Score.run_id == run.id)
        )).scalars().all()
        self.assertEqual(parsed_count, [])
        self.assertEqual(score_count, [])


if __name__ == "__main__":
    unittest.main()
