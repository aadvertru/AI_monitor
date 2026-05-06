from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import duplicate_audit
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    AnswerEvaluation,
    AnswerEvaluationVerdict,
    Audit,
    AuditStatus,
    AuditTarget,
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
    SeedQuerySource,
    SeedQueryType,
    User,
    UserRole,
)

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class DuplicateAuditAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(
        self,
        email: str,
        *,
        role: UserRole = UserRole.USER,
    ) -> User:
        async with self.session_factory() as session:
            user = User(email=email, hashed_password="hashed", role=role)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

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

    async def _create_source_audit(self, owner: User) -> Audit:
        async with self.session_factory() as session:
            brand = Brand(
                name="Duplicate Source",
                domain="duplicate.example",
                description="Config description",
            )
            audit = Audit(
                brand=brand,
                user_id=owner.id,
                status=AuditStatus.COMPLETED,
                providers=["openrouter"],
                runs_per_query=2,
                language="en",
                country="US",
                locale="en-US",
                max_queries=5,
                enable_query_expansion=False,
                enable_source_intelligence=True,
                follow_up_depth=0,
                scdl_level=SCDLLevel.L2,
            )
            session.add(audit)
            await session.flush()
            query = Query(
                audit_id=audit.id,
                text="best duplicate tools",
                query_type=SeedQueryType.RECOMMENDATION,
                source=SeedQuerySource.AI,
            )
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
                provider_config_snapshot={"model": "anthropic/claude-3.5-sonnet"},
                model_display_order=3,
                capability_metadata={"supports_web": True},
            )
            session.add_all([query, target])
            await session.flush()
            job = Job(
                audit_id=audit.id,
                query_id=query.id,
                audit_target_id=target.id,
                provider="openrouter",
                run_number=1,
                status=JobStatus.COMPLETED,
                idempotency_key=f"audit:{audit.id}:query:{query.id}:target:{target.id}:run:1",
            )
            run = Run(
                audit_id=audit.id,
                query_id=query.id,
                audit_target_id=target.id,
                provider="openrouter",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            session.add_all([job, run])
            await session.flush()
            session.add_all(
                [
                    RawResponse(
                        run_id=run.id,
                        request_snapshot={"prompt": "hidden"},
                        raw_answer="source raw answer",
                        citations=[{"url": "https://source.example"}],
                        provider_metadata={"model": "anthropic/claude-3.5-sonnet"},
                        provider_status="success",
                    ),
                    ParsedResult(
                        run_id=run.id,
                        visible_brand=True,
                        brand_position_rank=1,
                        competitors=["Result Rival"],
                        sources=[{"url": "https://source.example"}],
                        parsed_payload={"raw": "hidden"},
                    ),
                    Score(run_id=run.id, final_score=0.8),
                    AnswerEvaluation(
                        audit_id=audit.id,
                        run_id=run.id,
                        query_id=query.id,
                        target_id=target.id,
                        verdict=AnswerEvaluationVerdict.CORRECT,
                        confidence=0.9,
                        evaluation_version="eval-v1",
                    ),
                    Concept(
                        audit_id=audit.id,
                        text="Result Rival",
                        category="competitor",
                        count=1,
                        evidence={"run_ids": [run.id]},
                    ),
                    CompetitorCandidate(
                        audit_id=audit.id,
                        name="Result Rival",
                        confidence=0.9,
                        evidence_type="known",
                        evidence_count=1,
                        evidence=[{"run_id": run.id}],
                    ),
                ]
            )
            await session.commit()
            await session.refresh(audit)
            return audit

    async def _count_for_audit(self, model: type, audit_id: int) -> int:
        async with self.session_factory() as session:
            return await session.scalar(
                select(func.count()).select_from(model).where(model.audit_id == audit_id)
            )

    async def _count_by_run_for_audit(self, model: type, audit_id: int) -> int:
        async with self.session_factory() as session:
            return await session.scalar(
                select(func.count())
                .select_from(model)
                .join(Run, model.run_id == Run.id)
                .where(Run.audit_id == audit_id)
            )

    async def test_unauthenticated_duplicate_is_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        source = await self._create_source_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await duplicate_audit(
                    audit_id=source.id,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_non_owner_duplicate_is_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        source = await self._create_source_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await duplicate_audit(
                    audit_id=source.id,
                    request=self._request(other),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 404)

    async def test_owner_duplicates_config_without_results(self) -> None:
        owner = await self._create_user("owner@example.com")
        source = await self._create_source_audit(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await duplicate_audit(
                    audit_id=source.id,
                    request=self._request(owner),
                    session=session,
                )

        self.assertNotEqual(result.audit_id, source.id)
        self.assertEqual(result.status, "created")
        self.assertEqual(result.providers, ["openrouter"])
        self.assertEqual(result.runs_per_query, 2)
        self.assertEqual(result.scdl_level, "L2")
        self.assertEqual(result.seed_queries, ["best duplicate tools"])
        self.assertEqual(result.seed_query_items[0].type, "recommendation")
        self.assertEqual(result.seed_query_items[0].source, "ai")
        self.assertEqual(len(result.model_targets), 1)
        self.assertEqual(result.model_targets[0].model_id, "anthropic/claude-3.5-sonnet")
        self.assertTrue(result.model_targets[0].gateway_l2_experimental)

        async with self.session_factory() as session:
            duplicated = await session.get(Audit, result.audit_id)
            self.assertIsNotNone(duplicated)
            assert duplicated is not None
            self.assertEqual(duplicated.user_id, owner.id)
            self.assertEqual(duplicated.status, AuditStatus.CREATED)
            self.assertEqual(duplicated.brand_id, source.brand_id)
            self.assertTrue(duplicated.enable_source_intelligence)
            copied_target = (
                await session.execute(
                    select(AuditTarget).where(AuditTarget.audit_id == duplicated.id)
                )
            ).scalar_one()
            source_target = (
                await session.execute(select(AuditTarget).where(AuditTarget.audit_id == source.id))
            ).scalar_one()
            self.assertEqual(
                copied_target.provider_config_snapshot,
                source_target.provider_config_snapshot,
            )
            self.assertEqual(copied_target.capability_metadata, source_target.capability_metadata)

        for model in [Job, Run, Concept, CompetitorCandidate]:
            self.assertEqual(await self._count_for_audit(model, result.audit_id), 0)
        for model in [RawResponse, ParsedResult, Score, AnswerEvaluation]:
            self.assertEqual(await self._count_by_run_for_audit(model, result.audit_id), 0)

        self.assertEqual(await self._count_for_audit(Job, source.id), 1)
        self.assertEqual(await self._count_for_audit(Run, source.id), 1)
