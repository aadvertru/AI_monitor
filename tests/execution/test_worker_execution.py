from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

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
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session = Session(bind=self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def _create_job(self, provider_code: str = "mock") -> Job:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=[provider_code], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring tools")
        self.session.add_all([brand, audit, query])
        self.session.flush()

        job = Job(
            audit_id=audit.id,
            query_id=query.id,
            provider=provider_code,
            run_number=1,
            status=JobStatus.PENDING,
            idempotency_key=build_job_idempotency_key(audit.id, query.id, provider_code, 1),
        )
        self.session.add(job)
        self.session.commit()
        return job

    async def test_success_flow_persists_run_and_raw_response(self) -> None:
        job = self._create_job(provider_code="mock")

        run = await execute_job(self.session, job.id, _SuccessProvider())

        persisted_job = self.session.get(Job, job.id)
        persisted_run = self.session.get(Run, run.id)
        self.assertIsNotNone(persisted_job)
        self.assertIsNotNone(persisted_run)
        assert persisted_job is not None
        assert persisted_run is not None

        self.assertEqual(persisted_job.status, JobStatus.COMPLETED)
        self.assertEqual(persisted_run.status, RunStatus.SUCCESS)
        self.assertIsNotNone(persisted_run.raw_response)
        assert persisted_run.raw_response is not None
        self.assertEqual(persisted_run.raw_response.provider_status, "success")
        self.assertEqual(persisted_run.raw_response.raw_answer, "Answer for: best ai monitoring tools")
        self.assertEqual(persisted_run.raw_response.response_time, 0.25)
        self.assertIsNone(persisted_run.raw_response.error_object)

    async def test_error_flow_still_persists_run_and_raw_response(self) -> None:
        job = self._create_job(provider_code="mock")

        run = await execute_job(self.session, job.id, _ErrorProvider())

        persisted_job = self.session.get(Job, job.id)
        persisted_run = self.session.get(Run, run.id)
        assert persisted_job is not None
        assert persisted_run is not None
        assert persisted_run.raw_response is not None

        self.assertEqual(persisted_job.status, JobStatus.FAILED)
        self.assertEqual(persisted_run.status, RunStatus.ERROR)
        self.assertEqual(persisted_run.raw_response.provider_status, "error")
        self.assertIsNone(persisted_run.raw_response.raw_answer)
        self.assertEqual(
            persisted_run.raw_response.error_object,
            {"code": "mock_error", "message": "Provider failed."},
        )

    async def test_worker_does_not_parse_or_score(self) -> None:
        job = self._create_job(provider_code="mock")
        run = await execute_job(self.session, job.id, _SuccessProvider())

        persisted_run = self.session.get(Run, run.id)
        assert persisted_run is not None
        self.assertIsNone(persisted_run.parsed_result)
        self.assertIsNone(persisted_run.score)

        parsed_count = self.session.execute(
            select(ParsedResult).where(ParsedResult.run_id == run.id)
        ).scalars().all()
        score_count = self.session.execute(
            select(Score).where(Score.run_id == run.id)
        ).scalars().all()
        self.assertEqual(parsed_count, [])
        self.assertEqual(score_count, [])


if __name__ == "__main__":
    unittest.main()

