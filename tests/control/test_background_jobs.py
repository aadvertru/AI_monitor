from __future__ import annotations

import unittest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.control.audit_pipeline_background import execute_audit_pipeline_background_job
from libs.control.background_jobs import (
    enqueue_background_job,
    fetch_next_queued_job,
    mark_background_job_cancelled,
    mark_background_job_completed,
    mark_background_job_failed,
    mark_background_job_running,
    request_background_job_cancel,
)
from libs.execution.pipeline import AuditPipelineSummary, AuditSchedulingSummary
from libs.storage.models import (
    Audit,
    AuditStatus,
    BackgroundJobStatus,
    Base,
    Brand,
    User,
)


class BackgroundJobServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.session: AsyncSession = self.session_factory()
        self.user, self.audit = await self._create_user_and_audit()

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _create_user_and_audit(self) -> tuple[User, Audit]:
        user = User(email="owner@example.com", hashed_password="hash")
        brand = Brand(name="Acme", domain="acme.com")
        audit = Audit(
            brand=brand,
            user=user,
            providers=["mock"],
            runs_per_query=1,
            status=AuditStatus.CREATED,
        )
        self.session.add_all([user, brand, audit])
        await self.session.commit()
        await self.session.refresh(user)
        await self.session.refresh(audit)
        return user, audit

    async def test_job_can_be_enqueued(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
            progress_metadata={"scheduled_jobs": 3},
        )

        self.assertIsNotNone(job.id)
        self.assertEqual(job.status, BackgroundJobStatus.QUEUED)
        self.assertEqual(job.audit_id, self.audit.id)
        self.assertEqual(job.user_id, self.user.id)
        self.assertEqual(job.progress_metadata, {"scheduled_jobs": 3})

    async def test_queued_to_running_transition(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )

        updated = await mark_background_job_running(
            self.session,
            job.id,
            progress_metadata={"step": "execution"},
        )

        self.assertEqual(updated.status, BackgroundJobStatus.RUNNING)
        self.assertIsNotNone(updated.started_at)
        self.assertEqual(updated.progress_metadata["step"], "execution")

    async def test_running_to_completed_transition(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )
        await mark_background_job_running(self.session, job.id)

        updated = await mark_background_job_completed(
            self.session,
            job.id,
            progress_metadata={"runs_processed": 2},
        )

        self.assertEqual(updated.status, BackgroundJobStatus.COMPLETED)
        self.assertIsNotNone(updated.finished_at)
        self.assertEqual(updated.progress_metadata["runs_processed"], 2)

    async def test_running_to_failed_transition_stores_safe_error(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )
        await mark_background_job_running(self.session, job.id)

        updated = await mark_background_job_failed(
            self.session,
            job.id,
            error_code="Provider_Error",
            error_message="failed with Authorization Bearer sk-hidden",
            progress_metadata={
                "raw_prompt": "secret",
                "safe_count": 1,
                "nested": {"api_key": "sk-hidden", "stage": "provider"},
            },
        )

        self.assertEqual(updated.status, BackgroundJobStatus.FAILED)
        self.assertEqual(updated.error_code, "provider_error")
        self.assertEqual(updated.error_message_safe, "Background job failed.")
        self.assertEqual(updated.progress_metadata["safe_count"], 1)
        self.assertEqual(updated.progress_metadata["nested"], {"stage": "provider"})
        combined = str(updated.progress_metadata).lower()
        self.assertNotIn("raw_prompt", combined)
        self.assertNotIn("sk-hidden", combined)

    async def test_running_to_cancel_requested_transition(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )
        await mark_background_job_running(self.session, job.id)

        updated = await request_background_job_cancel(self.session, job.id)

        self.assertEqual(updated.status, BackgroundJobStatus.CANCEL_REQUESTED)
        self.assertIsNotNone(updated.cancel_requested_at)

    async def test_cancel_requested_to_cancelled_transition(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )
        await mark_background_job_running(self.session, job.id)
        await request_background_job_cancel(self.session, job.id)

        updated = await mark_background_job_cancelled(self.session, job.id)

        self.assertEqual(updated.status, BackgroundJobStatus.CANCELLED)
        self.assertIsNotNone(updated.finished_at)

    async def test_worker_can_fetch_next_queued_job(self) -> None:
        first = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )
        await enqueue_background_job(
            self.session,
            job_type="profile_sync",
            audit_id=None,
            user_id=self.user.id,
        )

        next_job = await fetch_next_queued_job(
            self.session,
            job_type="audit_pipeline",
        )

        assert next_job is not None
        self.assertEqual(next_job.id, first.id)
        self.assertEqual(next_job.status, BackgroundJobStatus.QUEUED)

    async def test_background_audit_pipeline_job_executes_mocked_pipeline(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )
        calls: list[int] = []

        async def pipeline_runner(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPipelineSummary:
            calls.append(audit_id)
            audit = await _session.get(Audit, audit_id)
            assert audit is not None
            audit.status = AuditStatus.COMPLETED
            await _session.commit()
            return AuditPipelineSummary(
                audit_id=audit_id,
                scheduling=AuditSchedulingSummary(audit_id=audit_id),
                final_audit_status="completed",
            )

        updated = await execute_audit_pipeline_background_job(
            self.session,
            job.id,
            pipeline_runner=pipeline_runner,
        )
        saved_audit = await self.session.get(Audit, self.audit.id)

        self.assertEqual(calls, [self.audit.id])
        self.assertEqual(updated.status, BackgroundJobStatus.COMPLETED)
        self.assertEqual(updated.progress_metadata["final_audit_status"], "completed")
        assert saved_audit is not None
        self.assertEqual(saved_audit.status, AuditStatus.COMPLETED)

    async def test_background_audit_pipeline_job_stores_safe_provider_failure(self) -> None:
        job = await enqueue_background_job(
            self.session,
            job_type="audit_pipeline",
            audit_id=self.audit.id,
            user_id=self.user.id,
        )

        async def pipeline_runner(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPipelineSummary:
            return AuditPipelineSummary(
                audit_id=audit_id,
                scheduling=AuditSchedulingSummary(audit_id=audit_id),
                final_audit_status="failed",
                fatal_error="Provider failed with Authorization Bearer sk-hidden",
            )

        updated = await execute_audit_pipeline_background_job(
            self.session,
            job.id,
            pipeline_runner=pipeline_runner,
        )

        self.assertEqual(updated.status, BackgroundJobStatus.FAILED)
        self.assertEqual(updated.error_code, "audit_pipeline_failed")
        self.assertEqual(updated.error_message_safe, "Background job failed.")


if __name__ == "__main__":
    unittest.main()
