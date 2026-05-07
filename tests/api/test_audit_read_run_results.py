from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    cancel_audit_run,
    compare_audits,
    get_audit_detail,
    get_audit_progress,
    get_audit_results,
    get_audit_status,
    get_audit_summary,
    get_brand_audit_trends,
    get_comparison_candidates,
    get_raw_response_inspection,
    list_audits,
    retry_failed_audit_runs,
    run_audit,
    run_audit_pipeline_dev,
    run_audit_pipeline_owner,
)
from apps.api.security import create_access_token, load_auth_config
from libs.execution.audit_execution import AuditJobExecutionSummary
from libs.execution.pipeline import AuditPipelineSummary, AuditSchedulingSummary
from libs.execution.post_processing import AuditPostProcessingSummary
from libs.storage.models import (
    Audit,
    AuditStatus,
    AuditTarget,
    BackgroundJob,
    BackgroundJobStatus,
    Base,
    Brand,
    CompetitorCandidate,
    Concept,
    Job,
    JobStatus,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    Score,
    SeedQueryType,
    User,
    UserRole,
)

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}
NOW = datetime(2026, 4, 29, 9, 30, tzinfo=timezone.utc)


class AuditReadRunResultsAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(
        self,
        email: str = "owner@example.com",
        role: UserRole = UserRole.USER,
    ) -> User:
        async with self.session_factory() as session:
            user = User(
                email=email,
                hashed_password="hashed-password",
                role=role,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    def _authenticated_request(self, user: User) -> Request:
        config = load_auth_config(env=AUTH_ENV)
        token = create_access_token(user_id=user.id, role=user.role.value, config=config)
        return Request(
            {
                "type": "http",
                "headers": [(b"cookie", f"{config.cookie.name}={token}".encode("ascii"))],
            }
        )

    def _anonymous_request(self) -> Request:
        return Request({"type": "http", "headers": []})

    async def _create_audit(
        self,
        user: User,
        *,
        brand_name: str = "Acme AI",
        created_at: datetime = NOW,
        status: AuditStatus = AuditStatus.CREATED,
        providers: list[str] | None = None,
        runs_per_query: int = 1,
        query_texts: list[str] | None = None,
        scdl_level: SCDLLevel = SCDLLevel.L1,
    ) -> Audit:
        async with self.session_factory() as session:
            brand = Brand(
                name=brand_name,
                domain=f"{brand_name.lower().replace(' ', '-')}.example",
                description=f"{brand_name} description",
            )
            audit = Audit(
                brand=brand,
                user_id=user.id,
                status=status,
                providers=providers if providers is not None else ["mock"],
                runs_per_query=runs_per_query,
                scdl_level=scdl_level,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(audit)
            await session.flush()
            for query_text in (
                query_texts if query_texts is not None else ["best ai visibility monitor"]
            ):
                session.add(Query(audit_id=audit.id, text=query_text))
            await session.commit()
            await session.refresh(audit)
            return audit

    async def _add_successful_snapshot_data(
        self,
        audit: Audit,
        *,
        visible: bool = True,
        final_score: float = 0.8,
        source_domain: str = "example.com",
        concept_text: str = "Visibility",
        competitor_name: str = "Rival",
    ) -> None:
        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().first()
            assert query is not None
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="mock",
                execution_provider="mock",
                model_provider="mock",
                model_id="mock/default",
                display_name="Mock",
                level=SCDLLevel.L1,
            )
            session.add(target)
            await session.flush()
            run = Run(
                audit_id=audit.id,
                query_id=query.id,
                audit_target_id=target.id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            session.add(run)
            await session.flush()
            session.add_all(
                [
                    ParsedResult(
                        run_id=run.id,
                        visible_brand=visible,
                        competitors=[],
                        sources=[{"domain": source_domain, "url": f"https://{source_domain}/a"}],
                        parsed_payload={"raw_prompt": "hidden"},
                    ),
                    Score(run_id=run.id, final_score=final_score),
                    RawResponse(
                        run_id=run.id,
                        request_snapshot={"raw_prompt": "hidden"},
                        raw_answer="hidden raw answer",
                        citations=[],
                        provider_metadata={"api_key": "sk-hidden"},
                        provider_status="success",
                    ),
                    Concept(
                        audit_id=audit.id,
                        run_id=run.id,
                        query_id=query.id,
                        target_id=target.id,
                        text=concept_text,
                        count=1,
                        evidence_count=1,
                    ),
                    CompetitorCandidate(
                        audit_id=audit.id,
                        name=competitor_name,
                        confidence=0.8,
                        evidence_count=1,
                    ),
                ]
            )
            await session.commit()

    async def test_authenticated_user_can_list_only_owned_audits_ordered_newest_first(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        older = await self._create_audit(
            owner,
            brand_name="Older Brand",
            created_at=NOW - timedelta(days=1),
        )
        newer = await self._create_audit(owner, brand_name="Newer Brand", created_at=NOW)
        await self._create_audit(other, brand_name="Other Brand", created_at=NOW)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await list_audits(
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual([item.audit_id for item in result], [newer.id, older.id])
        self.assertEqual([item.brand_name for item in result], ["Newer Brand", "Older Brand"])

    async def test_admin_can_list_all_audits_with_simple_role_model(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        await self._create_audit(owner, brand_name="Owner Brand")
        await self._create_audit(other, brand_name="Other Brand")

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await list_audits(
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual({item.brand_name for item in result}, {"Owner Brand", "Other Brand"})

    async def test_admin_can_access_individual_endpoints_for_another_users_audit(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(owner, brand_name="Owner Brand")

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                request = self._authenticated_request(admin)
                detail = await get_audit_detail(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                status = await get_audit_status(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                results = await get_audit_results(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                summary = await get_audit_summary(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                trigger = await run_audit(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )

        self.assertEqual(detail.audit_id, audit.id)
        self.assertEqual(status.audit_id, audit.id)
        self.assertEqual(results.audit_id, audit.id)
        self.assertEqual(summary.audit_id, audit.id)
        self.assertEqual(trigger.audit_id, audit.id)
        self.assertEqual(trigger.status, "running")

    async def test_comparison_candidates_returns_owned_terminal_same_domain(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        current = await self._create_audit(
            owner,
            brand_name="Acme Current",
            status=AuditStatus.COMPLETED,
            created_at=NOW,
        )
        previous = await self._create_audit(
            owner,
            brand_name="Acme Previous",
            status=AuditStatus.COMPLETED,
            created_at=NOW - timedelta(days=1),
        )
        other_audit = await self._create_audit(
            other,
            brand_name="Acme Other",
            status=AuditStatus.COMPLETED,
        )
        async with self.session_factory() as session:
            for audit in [current, previous, other_audit]:
                stored = await session.get(Audit, audit.id)
                assert stored is not None
                brand = await session.get(Brand, stored.brand_id)
                assert brand is not None
                brand.domain = "acme.example"
            await session.commit()
        await self._add_successful_snapshot_data(current)
        await self._add_successful_snapshot_data(previous, final_score=0.4)
        await self._add_successful_snapshot_data(other_audit)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_comparison_candidates(
                    audit_id=current.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual([candidate.audit_id for candidate in result.candidates], [previous.id])
        self.assertEqual(result.candidates[0].summary.mentionability_l1, 100.0)

    async def test_compare_audits_returns_deltas_and_safe_changes(self) -> None:
        owner = await self._create_user()
        previous = await self._create_audit(
            owner,
            brand_name="Acme Previous",
            status=AuditStatus.COMPLETED,
            created_at=NOW - timedelta(days=1),
        )
        current = await self._create_audit(
            owner,
            brand_name="Acme Current",
            status=AuditStatus.COMPLETED,
            created_at=NOW,
        )
        async with self.session_factory() as session:
            for audit in [previous, current]:
                stored = await session.get(Audit, audit.id)
                assert stored is not None
                brand = await session.get(Brand, stored.brand_id)
                assert brand is not None
                brand.domain = "acme.example"
            await session.commit()
        await self._add_successful_snapshot_data(
            previous,
            visible=False,
            source_domain="old.example",
            concept_text="Old concept",
            competitor_name="Old rival",
        )
        await self._add_successful_snapshot_data(
            current,
            visible=True,
            source_domain="new.example",
            concept_text="New concept",
            competitor_name="New rival",
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await compare_audits(
                    audit_id=current.id,
                    previous_audit_id=previous.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.current_audit_id, current.id)
        self.assertEqual(result.overall_delta["mentionability_l1"].delta, 100.0)
        self.assertTrue(any(item.status == "added" for item in result.source_domain_changes))
        dumped = str(result.model_dump())
        self.assertNotIn("raw_prompt", dumped)
        self.assertNotIn("sk-hidden", dumped)

    async def test_compare_audits_enforces_ownership_for_previous_audit(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        current = await self._create_audit(
            owner,
            brand_name="Owner Compare",
            status=AuditStatus.COMPLETED,
        )
        previous = await self._create_audit(
            other,
            brand_name="Other Compare",
            status=AuditStatus.COMPLETED,
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await compare_audits(
                    audit_id=current.id,
                    previous_audit_id=previous.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_brand_trends_returns_owned_terminal_points_chronologically(self) -> None:
        owner = await self._create_user()
        old = await self._create_audit(
            owner,
            brand_name="Trend Brand",
            status=AuditStatus.COMPLETED,
            created_at=NOW - timedelta(days=2),
        )
        newer = await self._create_audit(
            owner,
            brand_name="Trend Brand Newer",
            status=AuditStatus.COMPLETED,
            created_at=NOW - timedelta(days=1),
        )
        draft = await self._create_audit(
            owner,
            brand_name="Trend Brand Draft",
            status=AuditStatus.CREATED,
            created_at=NOW,
        )
        async with self.session_factory() as session:
            old_stored = await session.get(Audit, old.id)
            newer_stored = await session.get(Audit, newer.id)
            draft_stored = await session.get(Audit, draft.id)
            assert old_stored is not None and newer_stored is not None and draft_stored is not None
            brand_id = old_stored.brand_id
            newer_stored.brand_id = brand_id
            draft_stored.brand_id = brand_id
            await session.commit()
        await self._add_successful_snapshot_data(old, visible=False)
        await self._add_successful_snapshot_data(newer, visible=True)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_brand_audit_trends(
                    brand_id=brand_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual([point.audit_id for point in result.points], [old.id, newer.id])
        self.assertEqual(result.points[0].mentionability_l1, 0.0)
        self.assertEqual(result.points[1].mentionability_l1, 100.0)

    async def test_progress_endpoint_rejects_unauthenticated_request(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await get_audit_progress(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_progress_endpoint_hides_cross_user_audit(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await get_audit_progress(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_progress_endpoint_reports_created_audit_zero_percent(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, query_texts=["query one", "query two"])

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_progress(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "created")
        self.assertEqual(result.total_runs, 2)
        self.assertEqual(result.queued_runs, 0)
        self.assertEqual(result.percent_complete, 0.0)

    async def test_progress_endpoint_reports_running_audit_counts(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.RUNNING)

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().one()
            session.add_all(
                [
                    Job(
                        audit_id=audit.id,
                        query_id=query.id,
                        provider="mock",
                        run_number=1,
                        status=JobStatus.PENDING,
                        idempotency_key=f"{audit.id}:{query.id}:mock:1",
                    ),
                    Job(
                        audit_id=audit.id,
                        query_id=query.id,
                        provider="mock",
                        run_number=2,
                        status=JobStatus.RUNNING,
                        idempotency_key=f"{audit.id}:{query.id}:mock:2",
                    ),
                    BackgroundJob(
                        job_type="audit_pipeline",
                        audit_id=audit.id,
                        user_id=owner.id,
                        status=BackgroundJobStatus.RUNNING,
                        progress_metadata={"stage": "execution"},
                    ),
                ]
            )
            await session.commit()
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_progress(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "running")
        self.assertEqual(result.queued_runs, 1)
        self.assertEqual(result.running_runs, 1)
        self.assertIsNotNone(result.current_job_id)
        self.assertEqual(result.percent_complete, 0.0)

    async def test_progress_endpoint_reports_completed_and_failed_runs_safely(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.PARTIAL,
            query_texts=["success query", "failed query"],
        )

        async with self.session_factory() as session:
            queries = (
                await session.execute(
                    select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars().all()
            success_run = Run(
                audit_id=audit.id,
                query_id=queries[0].id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            failed_run = Run(
                audit_id=audit.id,
                query_id=queries[1].id,
                provider="mock",
                run_number=1,
                status=RunStatus.ERROR,
            )
            session.add_all([success_run, failed_run])
            await session.flush()
            session.add(
                RawResponse(
                    run_id=failed_run.id,
                    request_snapshot={"raw_prompt": "hidden"},
                    raw_answer=None,
                    citations=[],
                    provider_metadata={"provider": "mock"},
                    provider_status="error",
                    error_object={
                        "code": "PROVIDER_REQUEST_FAILED",
                        "message": "Provider failed with sk-hidden",
                        "provider": "mock",
                    },
                )
            )
            await session.commit()
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_progress(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "partial")
        self.assertEqual(result.completed_runs, 1)
        self.assertEqual(result.failed_runs, 1)
        self.assertEqual(result.percent_complete, 100.0)
        dumped = str(result.model_dump())
        self.assertNotIn("sk-hidden", dumped)
        self.assertNotIn("raw_prompt", dumped)

    async def test_progress_endpoint_zero_total_is_safe(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, providers=[], query_texts=[])

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_progress(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.total_runs, 0)
        self.assertEqual(result.percent_complete, 0.0)

    async def test_cancel_endpoint_owner_can_cancel_running_audit(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.RUNNING)

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().one()
            completed_run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            pending_job = Job(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=2,
                status=JobStatus.PENDING,
                idempotency_key=f"{audit.id}:{query.id}:mock:2",
            )
            background_job = BackgroundJob(
                job_type="audit_pipeline",
                audit_id=audit.id,
                user_id=owner.id,
                status=BackgroundJobStatus.RUNNING,
                progress_metadata={"stage": "execution"},
            )
            session.add_all([completed_run, pending_job, background_job])
            await session.commit()
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await cancel_audit_run(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )
            saved_job = await session.get(Job, pending_job.id)
            saved_background_job = await session.get(BackgroundJob, background_job.id)
            saved_audit = await session.get(Audit, audit.id)

        self.assertEqual(result.status, "cancel_requested")
        self.assertEqual(result.audit_status, "cancelled")
        self.assertEqual(result.cancelled_jobs, 1)
        self.assertEqual(result.completed_runs_preserved, 1)
        assert saved_job is not None
        self.assertEqual(saved_job.status, JobStatus.CANCELLED)
        assert saved_background_job is not None
        self.assertEqual(saved_background_job.status, BackgroundJobStatus.CANCEL_REQUESTED)
        assert saved_audit is not None
        self.assertEqual(saved_audit.status, AuditStatus.CANCELLED)

    async def test_cancel_endpoint_hides_cross_user_audit(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner, status=AuditStatus.RUNNING)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await cancel_audit_run(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_cancel_endpoint_rejects_completed_audit(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.COMPLETED)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await cancel_audit_run(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)

    async def test_retry_failed_endpoint_retries_failed_runs_only(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.PARTIAL,
            query_texts=["success query", "failed query"],
        )

        async with self.session_factory() as session:
            queries = (
                await session.execute(
                    select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars().all()
            session.add_all(
                [
                    Run(
                        audit_id=audit.id,
                        query_id=queries[0].id,
                        provider="mock",
                        run_number=1,
                        status=RunStatus.SUCCESS,
                    ),
                    Run(
                        audit_id=audit.id,
                        query_id=queries[1].id,
                        provider="mock",
                        run_number=1,
                        status=RunStatus.ERROR,
                    ),
                ]
            )
            await session.commit()
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await retry_failed_audit_runs(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )
            retry_jobs = (
                await session.execute(
                    select(Job).where(Job.audit_id == audit.id).order_by(Job.id)
                )
            ).scalars().all()
            saved_audit = await session.get(Audit, audit.id)

        self.assertEqual(result.retry_run_count, 1)
        self.assertEqual(result.status, "running")
        self.assertEqual(result.background_job_status, "queued")
        self.assertEqual(len(retry_jobs), 1)
        self.assertEqual(retry_jobs[0].query_id, queries[1].id)
        self.assertEqual(retry_jobs[0].run_number, 2)
        self.assertEqual(retry_jobs[0].status, JobStatus.PENDING)
        assert saved_audit is not None
        self.assertEqual(saved_audit.status, AuditStatus.RUNNING)

    async def test_retry_failed_endpoint_hides_cross_user_audit(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner, status=AuditStatus.FAILED)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await retry_failed_audit_runs(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_retry_failed_endpoint_rejects_when_no_failed_runs(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.COMPLETED)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await retry_failed_audit_runs(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)

    async def test_retry_failed_endpoint_retries_cancelled_jobs(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.PARTIAL)

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().one()
            session.add(
                Job(
                    audit_id=audit.id,
                    query_id=query.id,
                    provider="mock",
                    run_number=1,
                    status=JobStatus.CANCELLED,
                    idempotency_key=f"{audit.id}:{query.id}:mock:1",
                )
            )
            await session.commit()
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await retry_failed_audit_runs(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )
            retry_jobs = (
                await session.execute(
                    select(Job).where(
                        Job.audit_id == audit.id,
                        Job.status == JobStatus.PENDING,
                    )
                )
            ).scalars().all()

        self.assertEqual(result.retry_run_count, 1)
        self.assertEqual(len(retry_jobs), 1)
        self.assertEqual(retry_jobs[0].run_number, 2)

    async def test_authenticated_user_can_fetch_owned_audit_detail(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            brand_name="Acme AI",
            query_texts=["first query", "second query"],
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_detail(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.brand_name, "Acme AI")
        self.assertEqual(result.scdl_level, "L1")
        self.assertEqual(result.seed_queries, ["first query", "second query"])
        self.assertNotIn("user_id", result.model_dump())

    async def test_read_endpoints_expose_l2_scdl_level(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, scdl_level=SCDLLevel.L2)

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().first()
            assert query is not None
            session.add(
                Run(
                    audit_id=audit.id,
                    query_id=query.id,
                    provider="mock",
                    run_number=1,
                    status=RunStatus.SUCCESS,
                )
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                request = self._authenticated_request(owner)
                list_result = await list_audits(request=request, session=session)
                detail_result = await get_audit_detail(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                status_result = await get_audit_status(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                results_result = await get_audit_results(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )

        self.assertEqual(list_result[0].scdl_level, "L2")
        self.assertEqual(detail_result.scdl_level, "L2")
        self.assertEqual(status_result.scdl_level, "L2")
        self.assertEqual(results_result.rows[0].scdl_level, "L2")

    async def test_status_and_results_expose_safe_target_metadata(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            providers=["openrouter"],
            query_texts=["target query"],
        )

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().one()
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="claude",
                execution_provider="openrouter",
                model_provider="anthropic",
                model_id="anthropic/claude-3.5-sonnet",
                display_name="Claude 3.5 Sonnet",
                level=SCDLLevel.L2,
                gateway=True,
                gateway_l2_experimental=True,
            )
            session.add(target)
            await session.flush()
            run = Run(
                audit_id=audit.id,
                query_id=query.id,
                audit_target_id=target.id,
                provider="openrouter",
                run_number=1,
                status=RunStatus.ERROR,
            )
            session.add(run)
            await session.flush()
            session.add(
                RawResponse(
                    run_id=run.id,
                    request_snapshot={"raw_prompt": "hidden"},
                    raw_answer=None,
                    citations=None,
                    provider_metadata={
                        "model_id": "anthropic/claude-3.5-sonnet",
                        "headers": {"authorization": "secret"},
                    },
                    provider_status="error",
                    error_object={
                        "code": "PROVIDER_REQUEST_FAILED",
                        "message": "Provider request failed.",
                    },
                )
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                status_result = await get_audit_status(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )
                results_result = await get_audit_results(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(len(status_result.model_targets), 1)
        self.assertEqual(
            status_result.model_targets[0].model_id,
            "anthropic/claude-3.5-sonnet",
        )
        row = results_result.rows[0]
        self.assertEqual(row.target_id, status_result.model_targets[0].target_id)
        assert row.target is not None
        self.assertEqual(row.target.execution_provider, "openrouter")
        self.assertEqual(row.target.level, "L2")
        self.assertTrue(row.target.gateway_l2_experimental)
        assert row.provider_error is not None
        self.assertEqual(row.provider_error.model, "anthropic/claude-3.5-sonnet")
        self.assertEqual(row.provider_error.level, "L2")
        dumped = results_result.model_dump()
        self.assertNotIn("raw_prompt", str(dumped))
        self.assertNotIn("authorization", str(dumped).lower())

    async def test_unauthenticated_list_and_detail_are_rejected(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as list_context,
            ):
                await list_audits(request=self._anonymous_request(), session=session)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as detail_context,
            ):
                await get_audit_detail(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(list_context.exception.status_code, 401)
        self.assertEqual(detail_context.exception.status_code, 401)

    async def test_cross_user_audit_detail_is_hidden(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await get_audit_detail(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_authenticated_user_can_get_owned_audit_status(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.PARTIAL,
            query_texts=["first query", "second query"],
        )

        async with self.session_factory() as session:
            queries = (
                await session.execute(
                    select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars().all()
            session.add_all(
                [
                    Run(
                        audit_id=audit.id,
                        query_id=queries[0].id,
                        provider="mock",
                        run_number=1,
                        status=RunStatus.SUCCESS,
                    ),
                    Run(
                        audit_id=audit.id,
                        query_id=queries[1].id,
                        provider="mock",
                        run_number=1,
                        status=RunStatus.ERROR,
                    ),
                ]
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_status(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "partial")
        self.assertEqual(result.total_runs, 2)
        self.assertEqual(result.completed_runs, 2)
        self.assertEqual(result.failed_runs, 1)
        self.assertEqual(result.completion_ratio, 1.0)

    async def test_unauthenticated_and_cross_user_status_are_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as unauth_context,
            ):
                await get_audit_status(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as cross_user_context,
            ):
                await get_audit_status(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(cross_user_context.exception.status_code, 404)

    async def test_cross_user_run_trigger_is_hidden(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_run_trigger_schedules_jobs_without_calling_provider(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            providers=["mock"],
            runs_per_query=2,
            query_texts=["first query", "second query"],
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "libs.execution.mock_provider.MockProviderAdapter.query",
                    side_effect=AssertionError("provider should not be called"),
                ),
            ):
                result = await run_audit(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "running")
        self.assertEqual(result.scheduled_jobs, 4)
        self.assertEqual(result.total_jobs, 4)

        async with self.session_factory() as session:
            jobs = (
                await session.execute(select(Job).where(Job.audit_id == audit.id))
            ).scalars().all()
            saved_audit = await session.get(Audit, audit.id)
        self.assertEqual(len(jobs), 4)
        self.assertTrue(all(job.status == JobStatus.PENDING for job in jobs))
        assert saved_audit is not None
        self.assertEqual(saved_audit.status, AuditStatus.RUNNING)

    async def test_run_trigger_policy_guard_runs_before_scheduling_jobs(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            providers=["openai"],
            runs_per_query=1,
            query_texts=["first query"],
        )

        async with self.session_factory() as session:
            with (
                patch.dict(
                    "os.environ",
                    {
                        **AUTH_ENV,
                        "PROVIDER_MODE": "openai",
                        "REAL_PROVIDER_ENABLED": "false",
                    },
                    clear=True,
                ),
                patch("apps.api.main.schedule_jobs_for_audit") as schedule_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Real provider execution is disabled", context.exception.detail)
        schedule_mock.assert_not_called()

    async def test_run_trigger_rejects_duplicate_running_audit(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.RUNNING)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)

    async def test_run_trigger_rejects_completed_audit_retrigger(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.COMPLETED)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)

    async def test_run_trigger_state_values_are_documented(self) -> None:
        documented = {"created", "running", "partial", "completed", "failed", "cancelled"}
        self.assertEqual({status.value for status in AuditStatus}, documented)

    async def test_dev_pipeline_endpoint_rejects_unauthenticated_request(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)
        pipeline_mock.assert_not_called()

    async def test_dev_pipeline_endpoint_rejects_non_admin_user(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 403)
        pipeline_mock.assert_not_called()

    async def test_dev_pipeline_endpoint_admin_can_run_full_pipeline_service(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(owner)
        pipeline_summary = AuditPipelineSummary(
            audit_id=audit.id,
            scheduling=AuditSchedulingSummary(
                audit_id=audit.id,
                scheduled_jobs=1,
                total_jobs=1,
            ),
            execution=AuditJobExecutionSummary(
                audit_id=audit.id,
                total_jobs_inspected=1,
                jobs_executed=1,
                success_count=1,
            ),
            post_processing=AuditPostProcessingSummary(
                audit_id=audit.id,
                total_runs_inspected=1,
                runs_processed=1,
                audit_status="completed",
            ),
            final_audit_status="completed",
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.run_audit_pipeline",
                    new=AsyncMock(return_value=pipeline_summary),
                ) as pipeline_mock,
            ):
                result = await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.final_audit_status, "completed")
        self.assertEqual(result.scheduling.scheduled_jobs, 1)
        self.assertEqual(result.execution.jobs_executed, 1)
        self.assertEqual(result.post_processing.runs_processed, 1)
        pipeline_mock.assert_awaited_once()
        self.assertEqual(pipeline_mock.await_args.args[1], audit.id)

    async def test_dev_pipeline_endpoint_missing_audit_is_hidden(self) -> None:
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_dev(
                    audit_id=999,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)
        pipeline_mock.assert_not_called()

    async def test_dev_pipeline_endpoint_cross_user_non_admin_is_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 403)
        pipeline_mock.assert_not_called()

    async def test_dev_pipeline_endpoint_response_does_not_expose_sensitive_fields(
        self,
    ) -> None:
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(admin)
        pipeline_summary = AuditPipelineSummary(
            audit_id=audit.id,
            scheduling=AuditSchedulingSummary(audit_id=audit.id),
            execution=AuditJobExecutionSummary(
                audit_id=audit.id,
                errors=[],
                fatal_error="Provider failed with key sk-secret-token",
            ),
            post_processing=AuditPostProcessingSummary(audit_id=audit.id),
            final_audit_status="failed",
            fatal_error="Bearer secret-cookie should not leak",
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.run_audit_pipeline",
                    new=AsyncMock(return_value=pipeline_summary),
                ),
            ):
                result = await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        dumped = str(result.model_dump())
        self.assertNotIn("sk-secret-token", dumped)
        self.assertNotIn("secret-cookie", dumped)
        self.assertNotIn("raw_answer", dumped)
        self.assertNotIn("request_snapshot", dumped)

    async def test_dev_pipeline_endpoint_respects_real_provider_guardrails_without_openai_call(
        self,
    ) -> None:
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(admin, providers=["openai"])

        async with self.session_factory() as session:
            with (
                patch.dict(
                    "os.environ",
                    {
                        **AUTH_ENV,
                        "PROVIDER_MODE": "openai",
                        "REAL_PROVIDER_ENABLED": "0",
                    },
                    clear=True,
                ),
                patch("libs.execution.audit_execution.build_provider_adapter") as factory_mock,
            ):
                result = await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(result.final_audit_status, "failed")
        self.assertIn("Real provider execution is disabled", result.fatal_error)
        factory_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_rejects_unauthenticated_request(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_owner_can_run_full_pipeline_service(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
            ):
                result = await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )
                background_job = await session.get(BackgroundJob, result.job_id)
                saved_audit = await session.get(Audit, audit.id)

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.status, "running")
        self.assertEqual(result.background_job_status, "queued")
        assert background_job is not None
        self.assertEqual(background_job.status, BackgroundJobStatus.QUEUED)
        self.assertEqual(background_job.audit_id, audit.id)
        assert saved_audit is not None
        self.assertEqual(saved_audit.status, AuditStatus.RUNNING)
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_admin_can_run_another_users_audit(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
            ):
                result = await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(admin),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.background_job_status, "queued")
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_cross_user_is_hidden(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_missing_audit_is_hidden(self) -> None:
        owner = await self._create_user("owner@example.com")

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_owner(
                    audit_id=999,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_rejects_already_running_audit(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner, status=AuditStatus.RUNNING)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "Audit is already running.")
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_prevents_duplicate_active_job(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                first = await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )
                saved_audit = await session.get(Audit, audit.id)
                assert saved_audit is not None
                saved_audit.status = AuditStatus.CREATED
                await session.commit()
                with self.assertRaises(HTTPException) as context:
                    await run_audit_pipeline_owner(
                        audit_id=audit.id,
                        request=self._authenticated_request(owner),
                        background_tasks=BackgroundTasks(),
                        session=session,
                    )

        self.assertGreater(first.job_id, 0)
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.detail,
            "Audit pipeline job is already queued or running.",
        )

    async def test_owner_pipeline_endpoint_rejects_completed_audit_retrigger(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner, status=AuditStatus.COMPLETED)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.detail,
            "Audit can only be triggered from the created state.",
        )
        pipeline_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_rejects_guardrail_before_provider_call(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner, providers=["openai"])

        async with self.session_factory() as session:
            with (
                patch.dict(
                    "os.environ",
                    {
                        **AUTH_ENV,
                        "PROVIDER_MODE": "openai",
                        "REAL_PROVIDER_ENABLED": "0",
                    },
                    clear=True,
                ),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock) as pipeline_mock,
                patch("libs.execution.audit_execution.build_provider_adapter") as factory_mock,
                self.assertRaises(HTTPException) as context,
            ):
                await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Real provider execution is disabled", context.exception.detail)
        pipeline_mock.assert_not_called()
        factory_mock.assert_not_called()

    async def test_owner_pipeline_endpoint_enqueue_response_does_not_expose_sensitive_fields(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.run_audit_pipeline", new_callable=AsyncMock),
            ):
                result = await run_audit_pipeline_owner(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    background_tasks=BackgroundTasks(),
                    session=session,
                )

        dumped = str(result.model_dump())
        self.assertNotIn("sk-secret-token", dumped)
        self.assertNotIn("secret-cookie", dumped)
        self.assertNotIn("raw_answer", dumped)
        self.assertNotIn("request_snapshot", dumped)

    async def test_results_endpoint_returns_success_and_failed_rows(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.PARTIAL,
            query_texts=["visible query", "failed query"],
        )

        async with self.session_factory() as session:
            queries = (
                await session.execute(
                    select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars().all()
            success_run = Run(
                audit_id=audit.id,
                query_id=queries[0].id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            failed_run = Run(
                audit_id=audit.id,
                query_id=queries[1].id,
                provider="mock",
                run_number=1,
                status=RunStatus.ERROR,
            )
            session.add_all([success_run, failed_run])
            await session.flush()
            session.add_all(
                [
                    ParsedResult(
                        run_id=success_run.id,
                        visible_brand=True,
                        brand_position_rank=1,
                        prominence_score=0.8,
                        sentiment=0.4,
                        recommendation_score=0.7,
                        source_quality_score=0.6,
                        competitors=[{"name": "Other Monitor"}],
                        sources=[
                            {
                                "title": "Source",
                                "url": "https://example.test/source",
                                "domain": "example.test",
                                "source_type": "blog",
                            }
                        ],
                        parsed_payload={"match_type": "exact"},
                    ),
                    Score(
                        run_id=success_run.id,
                        visibility_score=1.0,
                        prominence_score=0.8,
                        sentiment_score=0.4,
                        recommendation_score=0.7,
                        source_quality_score=0.6,
                        final_score=0.82,
                    ),
                    RawResponse(
                        run_id=success_run.id,
                        request_snapshot={"query": "visible query"},
                        raw_answer="do not expose this full answer",
                        citations=[],
                        provider_metadata={"provider": "mock"},
                        provider_status="success",
                    ),
                    RawResponse(
                        run_id=failed_run.id,
                        request_snapshot={"query": "failed query"},
                        raw_answer=None,
                        citations=None,
                        provider_metadata={"provider": "mock"},
                        provider_status="error",
                        error_object={"code": "mock_error", "message": "Provider failed."},
                    ),
                    Concept(
                        audit_id=audit.id,
                        text="persisted concept",
                        category="legacy_phrase",
                        count=2,
                        evidence_count=1,
                        evidence=[
                            {
                                "run_id": success_run.id,
                                "answer_excerpt": "safe excerpt",
                            }
                        ],
                    ),
                    CompetitorCandidate(
                        audit_id=audit.id,
                        name="Persisted Rival",
                        domain="rival.example",
                        confidence=0.8,
                        evidence_type="comparison",
                        evidence_count=1,
                        evidence=[
                            {
                                "run_id": success_run.id,
                                "answer_excerpt": "safe excerpt",
                            }
                        ],
                    ),
                ]
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_results(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.total, 2)
        success_row = result.rows[0]
        failed_row = result.rows[1]
        self.assertEqual(success_row.query, "visible query")
        self.assertEqual(success_row.run_status, "success")
        self.assertTrue(success_row.visible_brand)
        self.assertEqual(success_row.brand_position_rank, 1)
        self.assertEqual(success_row.final_score, 0.82)
        assert success_row.component_scores is not None
        self.assertEqual(success_row.component_scores.prominence_score, 0.8)
        self.assertEqual(success_row.competitors, ["Other Monitor"])
        self.assertEqual(success_row.concepts[0].text, "persisted concept")
        self.assertEqual(success_row.concepts[0].evidence_count, 1)
        self.assertEqual(success_row.competitor_candidates[0].name, "Persisted Rival")
        self.assertEqual(success_row.competitor_candidates[0].confidence, 0.8)
        self.assertEqual(success_row.sources[0].domain, "example.test")
        self.assertIsNotNone(success_row.raw_answer_ref)
        self.assertNotIn("raw_answer", success_row.model_dump())
        self.assertNotIn("do not expose this full answer", str(success_row.model_dump()))

        self.assertEqual(failed_row.run_status, "error")
        self.assertIsNone(failed_row.final_score)
        self.assertEqual(failed_row.error_code, "mock_error")
        self.assertEqual(failed_row.error_message, "Provider failed.")

    async def test_empty_results_response_is_stable(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_results(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.rows, [])
        self.assertEqual(result.total, 0)

    async def test_unauthenticated_and_cross_user_results_are_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as unauth_context,
            ):
                await get_audit_results(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as cross_user_context,
            ):
                await get_audit_results(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(cross_user_context.exception.status_code, 404)

    async def test_results_endpoint_does_not_run_parser_or_scoring(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("libs.analysis.parser.parse") as parse_mock,
                patch("libs.analysis.scoring.compute_score") as score_mock,
            ):
                result = await get_audit_results(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.total, 0)
        parse_mock.assert_not_called()
        score_mock.assert_not_called()

    async def test_completed_audit_summary_returns_frontend_safe_metrics(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.COMPLETED,
            query_texts=["visible query", "critical query"],
        )

        async with self.session_factory() as session:
            queries = (
                await session.execute(
                    select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars().all()
            queries[0].query_type = SeedQueryType.BRAND_DIRECT
            visible_run = Run(
                audit_id=audit.id,
                query_id=queries[0].id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            critical_run = Run(
                audit_id=audit.id,
                query_id=queries[1].id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            session.add_all([visible_run, critical_run])
            await session.flush()
            session.add_all(
                [
                    ParsedResult(
                        run_id=visible_run.id,
                        visible_brand=True,
                        brand_position_rank=1,
                        prominence_score=0.8,
                        sentiment=0.5,
                        recommendation_score=0.7,
                        source_quality_score=0.6,
                        competitors=[{"name": "Other Monitor"}],
                        sources=[
                            {
                                "title": "Source",
                                "url": "https://example.test/source",
                                "domain": "example.test",
                                "source_type": "blog",
                            }
                        ],
                        parsed_payload={},
                    ),
                    Score(
                        run_id=visible_run.id,
                        visibility_score=1.0,
                        prominence_score=0.8,
                        sentiment_score=0.5,
                        recommendation_score=0.7,
                        source_quality_score=0.6,
                        final_score=0.8,
                    ),
                    ParsedResult(
                        run_id=critical_run.id,
                        visible_brand=False,
                        brand_position_rank=None,
                        prominence_score=0.0,
                        sentiment=0.0,
                        recommendation_score=0.0,
                        source_quality_score=0.0,
                        competitors=[{"name": "Other Monitor"}],
                        sources=[],
                        parsed_payload={},
                    ),
                    Score(
                        run_id=critical_run.id,
                        visibility_score=0.0,
                        prominence_score=0.0,
                        sentiment_score=0.0,
                        recommendation_score=0.0,
                        source_quality_score=0.0,
                        final_score=0.1,
                    ),
                ]
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_summary(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.total_queries, 2)
        self.assertEqual(result.total_runs, 2)
        self.assertEqual(result.successful_runs, 2)
        self.assertEqual(result.failed_runs, 0)
        self.assertEqual(result.completion_ratio, 1.0)
        self.assertEqual(result.visibility_ratio, 0.5)
        self.assertEqual(result.average_score, 0.45)
        self.assertEqual(result.weighted_visibility_score, 0.45)
        self.assertEqual(result.provider_scores, {"mock": 0.45})
        self.assertEqual(
            [item.model_dump() for item in result.query_type_coverage],
            [
                {
                    "type": "brand_direct",
                    "total_queries": 1,
                    "processed_runs": 1,
                    "failed_runs": 0,
                    "brand_found_count": 1,
                    "brand_found_rate": 1.0,
                    "average_score": 0.8,
                },
                {
                    "type": "unknown",
                    "total_queries": 1,
                    "processed_runs": 1,
                    "failed_runs": 0,
                    "brand_found_count": 0,
                    "brand_found_rate": 0.0,
                    "average_score": 0.1,
                },
            ],
        )
        self.assertEqual(result.critical_query_count, 1)
        self.assertEqual(result.critical_queries[0].query, "critical query")
        self.assertEqual(result.competitors[0].name, "Other Monitor")
        self.assertEqual(result.competitors[0].mention_count, 2)
        self.assertEqual(result.sources[0].domain, "example.test")
        self.assertNotIn("user_id", result.model_dump())

    async def test_empty_or_failed_audit_summary_returns_stable_shape(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.FAILED)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_summary(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.total_queries, 0)
        self.assertEqual(result.total_runs, 0)
        self.assertIsNone(result.average_score)
        self.assertEqual(result.provider_scores, {})
        self.assertEqual(result.critical_queries, [])
        self.assertEqual(result.competitors, [])
        self.assertEqual(result.sources, [])

    async def test_summary_query_type_coverage_reports_failed_runs(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.PARTIAL,
            query_texts=["recommendation query"],
        )

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().one()
            query.query_type = SeedQueryType.RECOMMENDATION
            failed_run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=1,
                status=RunStatus.ERROR,
            )
            session.add(failed_run)
            await session.flush()
            session.add(
                RawResponse(
                    run_id=failed_run.id,
                    request_snapshot={"query": "recommendation query"},
                    raw_answer=None,
                    citations=[],
                    provider_metadata={"provider": "mock"},
                    provider_status="error",
                    error_object={"code": "mock_error", "message": "Provider failed."},
                )
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_audit_summary(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(
            [item.model_dump() for item in result.query_type_coverage],
            [
                {
                    "type": "recommendation",
                    "total_queries": 1,
                    "processed_runs": 0,
                    "failed_runs": 1,
                    "brand_found_count": 0,
                    "brand_found_rate": 0.0,
                    "average_score": None,
                }
            ],
        )

    async def test_unauthenticated_and_cross_user_summary_are_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as unauth_context,
            ):
                await get_audit_summary(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as cross_user_context,
            ):
                await get_audit_summary(
                    audit_id=audit.id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(cross_user_context.exception.status_code, 404)

    async def test_summary_endpoint_does_not_call_external_provider_or_parser(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "libs.execution.mock_provider.MockProviderAdapter.query",
                    side_effect=AssertionError("provider should not be called"),
                ) as provider_mock,
                patch("libs.analysis.parser.parse") as parse_mock,
                patch("libs.analysis.scoring.compute_score") as score_mock,
            ):
                result = await get_audit_summary(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.total_runs, 0)
        provider_mock.assert_not_called()
        parse_mock.assert_not_called()
        score_mock.assert_not_called()

    async def test_provider_diagnostics_are_exposed_on_status_results_and_summary(
        self,
    ) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            status=AuditStatus.PARTIAL,
            providers=["openai"],
        )
        await self._add_raw_response(
            audit,
            run_status=RunStatus.TIMEOUT,
            provider_status="timeout",
            raw_answer=None,
            provider_metadata={"provider": "openai", "model": "gpt-test"},
            error_object={
                "code": "TIMEOUT",
                "message": "OpenAI request timed out.",
                "provider": "openai",
                "model": "gpt-test",
                "level": "L1",
                "retryable": True,
                "details": {"traceback": "hidden"},
            },
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                request = self._authenticated_request(owner)
                status = await get_audit_status(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                results = await get_audit_results(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )
                summary = await get_audit_summary(
                    audit_id=audit.id,
                    request=request,
                    session=session,
                )

        self.assertEqual(status.provider_diagnostics[0].code, "TIMEOUT")
        self.assertEqual(status.provider_diagnostics[0].provider, "openai")
        self.assertEqual(status.provider_diagnostics[0].model, "gpt-test")
        self.assertTrue(status.provider_diagnostics[0].retryable)
        self.assertEqual(results.rows[0].provider_error.code, "TIMEOUT")
        self.assertEqual(results.provider_diagnostics[0].query_id, results.rows[0].query_id)
        self.assertEqual(summary.provider_diagnostics[0].code, "TIMEOUT")
        serialized = str(summary.model_dump())
        self.assertNotIn("traceback", serialized)
        self.assertNotIn("hidden", serialized)

    async def test_legacy_failed_run_gets_safe_generic_provider_diagnostic(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.FAILED)

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().one()
            session.add(
                Run(
                    audit_id=audit.id,
                    query_id=query.id,
                    provider="mock",
                    run_number=1,
                    status=RunStatus.ERROR,
                )
            )
            await session.commit()

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                results = await get_audit_results(
                    audit_id=audit.id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(results.rows[0].provider_error.code, "UNKNOWN_PROVIDER_ERROR")
        self.assertEqual(results.rows[0].provider_error.provider, "mock")

    async def test_pipeline_response_includes_safe_provider_diagnostic_for_fatal_error(
        self,
    ) -> None:
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(admin, providers=["openai"])
        pipeline_summary = AuditPipelineSummary(
            audit_id=audit.id,
            scheduling=AuditSchedulingSummary(
                audit_id=audit.id,
                fatal_error="Real provider execution is disabled with sk-hidden.",
            ),
            final_audit_status="failed",
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.run_audit_pipeline",
                    new=AsyncMock(return_value=pipeline_summary),
                ),
            ):
                result = await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(result.provider_diagnostics[0].code, "PROVIDER_DISABLED")
        self.assertEqual(result.provider_diagnostics[0].provider, "openai")
        self.assertNotIn("sk-hidden", str(result.model_dump()))

    async def test_pipeline_response_includes_safe_diagnostic_for_cap_failure(
        self,
    ) -> None:
        admin = await self._create_user("cap-admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(admin, providers=["openai"])
        pipeline_summary = AuditPipelineSummary(
            audit_id=audit.id,
            scheduling=AuditSchedulingSummary(
                audit_id=audit.id,
                fatal_error="Real-provider audit exceeds max queries cap with sk-hidden.",
            ),
            final_audit_status="failed",
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.run_audit_pipeline",
                    new=AsyncMock(return_value=pipeline_summary),
                ),
            ):
                result = await run_audit_pipeline_dev(
                    audit_id=audit.id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(result.provider_diagnostics[0].code, "CONFIGURATION_ERROR")
        self.assertEqual(result.provider_diagnostics[0].provider, "openai")
        self.assertNotIn("sk-hidden", str(result.model_dump()))

    async def test_admin_can_inspect_stored_successful_raw_response_with_redaction(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(
            owner,
            query_texts=["raw query"],
            providers=["openai"],
            scdl_level=SCDLLevel.L2,
        )
        run_id = await self._add_raw_response(
            audit,
            provider_status="success",
            raw_answer="Full raw answer for inspection.",
            provider_metadata={
                "provider": "openai",
                "api_key": "sk-secret",
                "nested": {"authorization": "Bearer sk-secret"},
            },
            error_object=None,
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_raw_response_inspection(
                    audit_id=audit.id,
                    run_id=run_id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.query, "raw query")
        self.assertEqual(result.provider, "openai")
        self.assertEqual(result.scdl_level, "L2")
        self.assertEqual(result.raw_answer, "Full raw answer for inspection.")
        self.assertEqual(result.provider_metadata["api_key"], "***")
        self.assertEqual(result.provider_metadata["nested"]["authorization"], "***")
        self.assertNotIn("sk-secret", str(result.model_dump()))

    async def test_admin_can_inspect_error_raw_response_with_redacted_error_object(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        audit = await self._create_audit(owner, providers=["openai"])
        run_id = await self._add_raw_response(
            audit,
            run_status=RunStatus.ERROR,
            provider_status="error",
            raw_answer=None,
            provider_metadata={"provider": "openai"},
            error_object={"code": "provider_error", "token": "secret-token"},
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await get_raw_response_inspection(
                    audit_id=audit.id,
                    run_id=run_id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(result.run_status, "error")
        self.assertEqual(result.error_object["token"], "***")
        self.assertNotIn("secret-token", str(result.model_dump()))

    async def test_raw_response_inspection_requires_admin_and_existing_raw_response(
        self,
    ) -> None:
        owner = await self._create_user("owner@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().first()
            assert query is not None
            run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = run.id

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as forbidden_context,
            ):
                await get_raw_response_inspection(
                    audit_id=audit.id,
                    run_id=run_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        admin = await self._create_user("admin@example.com", role=UserRole.ADMIN)
        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as missing_context,
            ):
                await get_raw_response_inspection(
                    audit_id=audit.id,
                    run_id=run_id,
                    request=self._authenticated_request(admin),
                    session=session,
                )

        self.assertEqual(forbidden_context.exception.status_code, 403)
        self.assertEqual(missing_context.exception.status_code, 404)

    async def _add_raw_response(
        self,
        audit: Audit,
        *,
        run_status: RunStatus = RunStatus.SUCCESS,
        provider_status: str,
        raw_answer: str | None,
        provider_metadata: dict,
        error_object: dict | None,
    ) -> int:
        async with self.session_factory() as session:
            query = (
                await session.execute(select(Query).where(Query.audit_id == audit.id))
            ).scalars().first()
            assert query is not None
            run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider=(audit.providers or ["mock"])[0],
                run_number=1,
                status=run_status,
            )
            session.add(run)
            await session.flush()
            session.add(
                RawResponse(
                    run_id=run.id,
                    request_snapshot={"query": query.text},
                    raw_answer=raw_answer,
                    citations=[{"url": "https://example.test", "title": "Example"}],
                    provider_metadata=provider_metadata,
                    provider_status=provider_status,
                    response_time=0.2,
                    error_object=error_object,
                )
            )
            await session.commit()
            return run.id


if __name__ == "__main__":
    unittest.main()
