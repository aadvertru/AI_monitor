from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import get_audit_summary_v2
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    Audit,
    AuditStatus,
    AuditTarget,
    Base,
    Brand,
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
NOW = datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc)


class ResultsV2SummaryAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.auth_env = patch.dict("os.environ", AUTH_ENV, clear=True)
        self.auth_env.start()
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.auth_env.stop()

    async def _create_user(
        self,
        email: str = "owner@example.com",
        role: UserRole = UserRole.USER,
    ) -> User:
        async with self.session_factory() as session:
            user = User(email=email, hashed_password="hashed", role=role)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def _create_audit(
        self,
        user: User,
        *,
        providers: list[str] | None = None,
        status: AuditStatus = AuditStatus.CREATED,
    ) -> Audit:
        async with self.session_factory() as session:
            brand = Brand(name=f"Acme {user.id}", domain="acme.example")
            audit = Audit(
                brand=brand,
                user_id=user.id,
                status=status,
                providers=providers or ["mock"],
                runs_per_query=1,
                scdl_level=SCDLLevel.L1,
                created_at=NOW,
                updated_at=NOW,
            )
            session.add(audit)
            await session.flush()
            session.add(Query(audit_id=audit.id, text="best acme tools"))
            await session.commit()
            await session.refresh(audit)
            return audit

    def _request(self, user: User) -> Request:
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

    async def test_summary_v2_requires_auth_and_enforces_ownership(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as unauth_context:
                await get_audit_summary_v2(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )
            with self.assertRaises(HTTPException) as other_context:
                await get_audit_summary_v2(
                    audit_id=audit.id,
                    request=self._request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(other_context.exception.status_code, 404)

    async def test_summary_v2_returns_safe_empty_summary(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, status=AuditStatus.CREATED)

        async with self.session_factory() as session:
            result = await get_audit_summary_v2(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.status, "created")
        self.assertEqual(result.totals.query_count, 1)
        self.assertEqual(result.totals.target_count, 1)
        self.assertEqual(result.totals.run_count, 0)
        self.assertEqual(result.overall.mentionability_l1.total, 0)
        self.assertIsNone(result.overall.accuracy_l1)
        self.assertEqual(result.concepts, [])
        self.assertEqual(result.competitor_candidates, [])

    async def test_summary_v2_groups_model_summaries_and_mentionability_by_level(
        self,
    ) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, providers=["openrouter"])
        await self._add_targeted_success_run(
            audit,
            level=SCDLLevel.L1,
            visible=True,
            final_score=0.8,
            sentiment_score=0.25,
        )
        await self._add_targeted_success_run(
            audit,
            level=SCDLLevel.L2,
            visible=False,
            final_score=0.2,
            sentiment_score=-0.25,
        )

        async with self.session_factory() as session:
            result = await get_audit_summary_v2(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(result.totals.levels, ["L1", "L2"])
        self.assertEqual(result.totals.completed_runs, 2)
        self.assertEqual(result.overall.mentionability_l1.percentage, 100.0)
        self.assertEqual(result.overall.mentionability_l2.percentage, 0.0)
        self.assertEqual(result.overall.tone.positive, 1)
        self.assertEqual(result.overall.tone.negative, 1)
        self.assertEqual(len(result.model_summaries), 1)
        model = result.model_summaries[0]
        self.assertEqual(model.model_id, "openai/gpt-4o-mini")
        self.assertEqual(model.execution_provider, "openrouter")
        self.assertEqual(model.mr_l1, 100.0)
        self.assertEqual(model.mr_l2, 0.0)
        self.assertEqual(model.delta_mr, -100.0)
        self.assertIsNone(model.accuracy_l1)
        self.assertIsNone(model.accuracy_l2)
        self.assertEqual(model.tone_l1, "positive")
        self.assertEqual(model.tone_l2, "negative")

    async def test_summary_v2_partial_audit_exposes_safe_provider_diagnostics(
        self,
    ) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, providers=["openrouter"])
        await self._add_targeted_success_run(
            audit,
            level=SCDLLevel.L1,
            visible=True,
            final_score=0.8,
            sentiment_score=0.0,
        )
        await self._add_failed_run(audit)

        async with self.session_factory() as session:
            result = await get_audit_summary_v2(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(result.totals.run_count, 2)
        self.assertEqual(result.totals.completed_runs, 1)
        self.assertEqual(result.totals.failed_runs, 1)
        self.assertEqual(result.provider_diagnostics[0].code, "RATE_LIMIT")
        serialized = str(result.model_dump())
        self.assertNotIn("sk-hidden", serialized)
        self.assertNotIn("traceback", serialized)
        self.assertNotIn("raw_answer", serialized)

    async def _query_id(self, audit: Audit) -> int:
        async with self.session_factory() as session:
            query_id = (
                await session.execute(select(Query.id).where(Query.audit_id == audit.id))
            ).scalar_one()
            return int(query_id)

    async def _add_targeted_success_run(
        self,
        audit: Audit,
        *,
        level: SCDLLevel,
        visible: bool,
        final_score: float,
        sentiment_score: float,
    ) -> None:
        query_id = await self._query_id(audit)
        async with self.session_factory() as session:
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="chatgpt",
                execution_provider="openrouter",
                model_provider="openai",
                model_id="openai/gpt-4o-mini",
                display_name="GPT-4o mini",
                level=level,
                gateway=True,
                gateway_l2_experimental=level == SCDLLevel.L2,
            )
            session.add(target)
            await session.flush()
            run = Run(
                audit_id=audit.id,
                query_id=query_id,
                audit_target_id=target.id,
                provider="openrouter",
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
                        brand_position_rank=1 if visible else None,
                        prominence_score=0.5,
                        sentiment=sentiment_score,
                        recommendation_score=0.5,
                        source_quality_score=0.0,
                        competitors=[],
                        sources=[],
                        parsed_payload={},
                    ),
                    Score(
                        run_id=run.id,
                        visibility_score=1.0 if visible else 0.0,
                        prominence_score=0.5,
                        sentiment_score=sentiment_score,
                        recommendation_score=0.5,
                        source_quality_score=0.0,
                        final_score=final_score,
                    ),
                    RawResponse(
                        run_id=run.id,
                        request_snapshot={"query": "safe"},
                        raw_answer="hidden raw answer",
                        citations=[],
                        provider_metadata={"model": "openai/gpt-4o-mini"},
                        provider_status="success",
                    ),
                ]
            )
            await session.commit()

    async def _add_failed_run(self, audit: Audit) -> None:
        query_id = await self._query_id(audit)
        async with self.session_factory() as session:
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="chatgpt",
                execution_provider="openrouter",
                model_provider="google",
                model_id="google/gemini-2.0-flash-001",
                display_name="Gemini 2.0 Flash",
                level=SCDLLevel.L1,
                gateway=True,
            )
            session.add(target)
            await session.flush()
            run = Run(
                audit_id=audit.id,
                query_id=query_id,
                audit_target_id=target.id,
                provider="openrouter",
                run_number=1,
                status=RunStatus.RATE_LIMITED,
            )
            session.add(run)
            await session.flush()
            session.add(
                RawResponse(
                    run_id=run.id,
                    request_snapshot={"headers": "sk-hidden"},
                    raw_answer=None,
                    citations=[],
                    provider_metadata={"model": "google/gemini-2.0-flash-001"},
                    provider_status="rate_limited",
                    error_object={
                        "code": "RATE_LIMIT",
                        "message": "traceback with sk-hidden",
                    },
                )
            )
            await session.commit()


if __name__ == "__main__":
    unittest.main()
