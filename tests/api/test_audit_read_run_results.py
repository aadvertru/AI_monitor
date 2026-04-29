from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    get_audit_detail,
    get_audit_results,
    get_audit_status,
    get_audit_summary,
    list_audits,
    run_audit,
)
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    Job,
    JobStatus,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    Score,
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
                providers=providers or ["mock"],
                runs_per_query=runs_per_query,
                scdl_level=scdl_level,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(audit)
            await session.flush()
            for query_text in query_texts or ["best ai visibility monitor"]:
                session.add(Query(audit_id=audit.id, text=query_text))
            await session.commit()
            await session.refresh(audit)
            return audit

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
        documented = {"created", "running", "partial", "completed", "failed"}
        self.assertEqual({status.value for status in AuditStatus}, documented)

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
        self.assertEqual(success_row.sources[0].domain, "example.test")
        self.assertIsNotNone(success_row.raw_answer_ref)
        self.assertNotIn("raw_answer", success_row.model_dump())

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
        self.assertEqual(result.provider_scores, {"mock": 0.45})
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


if __name__ == "__main__":
    unittest.main()
