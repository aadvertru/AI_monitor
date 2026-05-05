from __future__ import annotations

import unittest

from sqlalchemy import event, select
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.worker import execute_job
from libs.storage.models import (
    Audit,
    AuditTarget,
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


class _UnserializableMetadataProvider(BaseProviderAdapter):
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        return ProviderResponse(
            status="success",
            raw_answer=f"Answer for: {query}",
            citations=[{"url": "https://example.com", "title": "Example"}],
            response_time=0.1,
            error=None,
            provider_metadata={"invalid": {1, 2, 3}},
        )


class _RaisingProvider(BaseProviderAdapter):
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        raise self.exc


class _RecordingProvider(BaseProviderAdapter):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        self.calls.append({"query": query, **kwargs})
        return ProviderResponse(
            status="success",
            raw_answer=f"Answer for: {query}",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata={
                "provider": kwargs.get("execution_provider") or kwargs.get("provider"),
                "execution_provider": kwargs.get("execution_provider"),
                "model_id": kwargs.get("model_id"),
                "model_provider": kwargs.get("model_provider"),
                "gateway": kwargs.get("gateway"),
                "gateway_l2_experimental": kwargs.get("gateway_l2_experimental"),
                "level": kwargs.get("scdl_level"),
            },
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

    async def _create_target_job(self, *, model_id: str) -> Job:
        brand = Brand(name=f"Target Brand {model_id}")
        audit = Audit(brand=brand, providers=["openrouter"], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring tools")
        self.session.add_all([brand, audit, query])
        await self.session.flush()
        target = AuditTarget(
            audit_id=audit.id,
            ai_family="chatgpt",
            execution_provider="openrouter",
            model_provider=model_id.split("/", 1)[0],
            model_id=model_id,
            display_name=model_id,
            level="L1",
            gateway=True,
        )
        self.session.add(target)
        await self.session.flush()
        job = Job(
            audit_id=audit.id,
            query_id=query.id,
            audit_target_id=target.id,
            provider="openrouter",
            run_number=1,
            status=JobStatus.PENDING,
            idempotency_key=build_job_idempotency_key(
                audit.id,
                query.id,
                "openrouter",
                1,
                audit_target_id=target.id,
            ),
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
        self.assertEqual(raw_response.error_object["code"], "PROVIDER_REQUEST_FAILED")
        self.assertEqual(raw_response.error_object["provider"], "mock")
        self.assertEqual(raw_response.error_object["level"], "L1")

    async def test_provider_exception_fallback_does_not_persist_raw_exception_message(
        self,
    ) -> None:
        job = await self._create_job(provider_code="mock")
        secret = "sk-test-secret"

        run = await execute_job(
            self.session,
            job.id,
            _RaisingProvider(RuntimeError(f"boom {secret}")),
        )

        raw_response = (
            await self.session.execute(select(RawResponse).where(RawResponse.run_id == run.id))
        ).scalar_one_or_none()
        assert raw_response is not None
        self.assertEqual(raw_response.provider_status, "error")
        self.assertEqual(raw_response.error_object["code"], "UNKNOWN_PROVIDER_ERROR")
        self.assertNotIn(secret, raw_response.error_object["message"])

    async def test_empty_success_response_is_persisted_as_provider_error(self) -> None:
        class _EmptySuccessProvider(BaseProviderAdapter):
            async def query(self, query: str, **kwargs) -> ProviderResponse:
                return ProviderResponse(
                    status="success",
                    raw_answer="",
                    citations=[],
                    response_time=0.2,
                    error=None,
                    provider_metadata={"provider": "mock"},
                )

        job = await self._create_job(provider_code="mock")

        run = await execute_job(self.session, job.id, _EmptySuccessProvider())

        persisted_job = await self.session.get(Job, job.id)
        raw_response = (
            await self.session.execute(select(RawResponse).where(RawResponse.run_id == run.id))
        ).scalar_one_or_none()
        assert persisted_job is not None
        assert raw_response is not None
        self.assertEqual(persisted_job.status, JobStatus.FAILED)
        self.assertEqual(run.status, RunStatus.ERROR)
        self.assertEqual(raw_response.provider_status, "error")
        self.assertEqual(raw_response.error_object["code"], "EMPTY_RESPONSE")

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

    async def test_target_metadata_is_passed_to_provider_and_persisted_on_run(
        self,
    ) -> None:
        job = await self._create_target_job(model_id="openai/gpt-4o-mini")
        provider = _RecordingProvider()

        run = await execute_job(self.session, job.id, provider)

        self.assertEqual(provider.calls[0]["model_id"], "openai/gpt-4o-mini")
        self.assertEqual(provider.calls[0]["model_provider"], "openai")
        self.assertEqual(provider.calls[0]["execution_provider"], "openrouter")
        self.assertEqual(provider.calls[0]["audit_target_id"], job.audit_target_id)
        self.assertTrue(provider.calls[0]["gateway"])

        persisted_run = await self.session.get(Run, run.id)
        raw_response = (
            await self.session.execute(select(RawResponse).where(RawResponse.run_id == run.id))
        ).scalar_one_or_none()
        assert persisted_run is not None
        assert raw_response is not None
        self.assertEqual(persisted_run.audit_target_id, job.audit_target_id)
        self.assertEqual(raw_response.request_snapshot["audit_target_id"], job.audit_target_id)
        self.assertEqual(raw_response.request_snapshot["model_id"], "openai/gpt-4o-mini")

    async def test_worker_rolls_back_when_persistence_fails(self) -> None:
        job = await self._create_job(provider_code="mock")
        job_id = job.id
        audit_id = job.audit_id
        query_id = job.query_id
        provider_code = job.provider
        run_number = job.run_number

        with self.assertRaises(StatementError):
            await execute_job(self.session, job_id, _UnserializableMetadataProvider())

        persisted_job = await self.session.get(Job, job_id)
        assert persisted_job is not None
        self.assertEqual(persisted_job.status, JobStatus.PENDING)

        persisted_runs = (
            await self.session.execute(
                select(Run).where(
                    Run.audit_id == audit_id,
                    Run.query_id == query_id,
                    Run.provider == provider_code,
                    Run.run_number == run_number,
                )
            )
        ).scalars().all()
        self.assertEqual(persisted_runs, [])


if __name__ == "__main__":
    unittest.main()
