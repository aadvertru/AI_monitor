from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import get_audit_answer_matrix
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
    SeedQueryType,
    User,
    UserRole,
)

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}
NOW = datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc)


class ResultsV2AnswerMatrixAPITests(unittest.IsolatedAsyncioTestCase):
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
    ) -> Audit:
        async with self.session_factory() as session:
            brand = Brand(name=f"Matrix {user.id}", domain=f"matrix-{user.id}.example")
            audit = Audit(
                brand=brand,
                user_id=user.id,
                status=AuditStatus.PARTIAL,
                providers=providers or ["openrouter"],
                runs_per_query=1,
                scdl_level=SCDLLevel.L1,
                created_at=NOW,
                updated_at=NOW,
            )
            session.add(audit)
            await session.flush()
            session.add_all(
                [
                    Query(
                        audit_id=audit.id,
                        text="best matrix tools",
                        query_type=SeedQueryType.CATEGORY_DISCOVERY,
                    ),
                    Query(audit_id=audit.id, text="matrix alternatives"),
                ]
            )
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

    async def test_answer_matrix_requires_auth_and_enforces_ownership(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as unauth_context:
                await get_audit_answer_matrix(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )
            with self.assertRaises(HTTPException) as other_context:
                await get_audit_answer_matrix(
                    audit_id=audit.id,
                    request=self._request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(other_context.exception.status_code, 404)

    async def test_answer_matrix_maps_queries_targets_and_safe_cells(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner)
        query_ids = await self._query_ids(audit)
        l1_target = await self._add_target(audit, level=SCDLLevel.L1)
        l2_target = await self._add_target(audit, level=SCDLLevel.L2)
        await self._add_success_run(
            audit_id=audit.id,
            query_id=query_ids[0],
            target_id=l1_target.id,
            provider="openrouter",
        )
        await self._add_failed_run(
            audit_id=audit.id,
            query_id=query_ids[0],
            target_id=l2_target.id,
            provider="openrouter",
        )

        async with self.session_factory() as session:
            result = await get_audit_answer_matrix(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual([column.level for column in result.columns], ["L1", "L2"])
        self.assertEqual([column.gateway for column in result.columns], [True, True])
        self.assertEqual(
            [column.gateway_l2_experimental for column in result.columns],
            [False, True],
        )
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(result.rows[0].query_text, "best matrix tools")
        self.assertEqual(result.rows[0].query_type, "category_discovery")

        completed_cell = result.rows[0].cells[0]
        self.assertEqual(completed_cell.status, "completed")
        self.assertEqual(completed_cell.brand_mentioned, True)
        self.assertEqual(completed_cell.score, 0.73)
        self.assertEqual(completed_cell.sources_count, 2)
        self.assertIsNone(completed_cell.evaluation)
        self.assertLessEqual(len(completed_cell.answer_excerpt or ""), 503)
        self.assertNotIn("hidden-tail", completed_cell.answer_excerpt or "")
        self.assertEqual(completed_cell.concepts, [])
        self.assertEqual(completed_cell.competitor_candidates, [])

        failed_cell = result.rows[0].cells[1]
        self.assertEqual(failed_cell.status, "failed")
        self.assertEqual(failed_cell.provider_error.code, "RATE_LIMIT")
        self.assertEqual(failed_cell.provider_error.provider, "openrouter")

        missing_cell = result.rows[1].cells[0]
        self.assertEqual(missing_cell.status, "not_run")
        self.assertIsNone(missing_cell.provider_error)

        serialized = str(result.model_dump())
        self.assertNotIn("sk-hidden", serialized)
        self.assertNotIn("traceback", serialized)
        self.assertNotIn("raw_answer", serialized)
        self.assertEqual(result.provider_diagnostics[0].code, "RATE_LIMIT")

    async def test_answer_matrix_uses_legacy_provider_columns_without_targets(
        self,
    ) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, providers=["mock"])
        query_ids = await self._query_ids(audit)
        await self._add_success_run(
            audit_id=audit.id,
            query_id=query_ids[0],
            target_id=None,
            provider="mock",
        )

        async with self.session_factory() as session:
            result = await get_audit_answer_matrix(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(len(result.columns), 1)
        self.assertEqual(result.columns[0].target_id, "legacy:mock:L1")
        self.assertEqual(result.columns[0].label, "mock / L1")
        self.assertEqual(result.rows[0].cells[0].status, "completed")
        self.assertEqual(result.rows[1].cells[0].status, "not_run")

    async def _query_ids(self, audit: Audit) -> list[int]:
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    select(Query.id).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars()
            return [int(query_id) for query_id in rows]

    async def _add_target(self, audit: Audit, *, level: SCDLLevel) -> AuditTarget:
        async with self.session_factory() as session:
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="chatgpt",
                execution_provider="openrouter",
                model_provider="openai",
                model_id="openai/gpt-4o-mini",
                display_name=f"GPT-4o mini {level.value}",
                level=level,
                gateway=True,
                gateway_l2_experimental=level == SCDLLevel.L2,
            )
            session.add(target)
            await session.commit()
            await session.refresh(target)
            return target

    async def _add_success_run(
        self,
        *,
        audit_id: int,
        query_id: int,
        target_id: int | None,
        provider: str,
    ) -> None:
        raw_answer = "Matrix answer " + ("x" * 520) + " hidden-tail"
        async with self.session_factory() as session:
            run = Run(
                audit_id=audit_id,
                query_id=query_id,
                audit_target_id=target_id,
                provider=provider,
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            session.add(run)
            await session.flush()
            session.add_all(
                [
                    ParsedResult(
                        run_id=run.id,
                        visible_brand=True,
                        brand_position_rank=1,
                        prominence_score=0.5,
                        sentiment=0.0,
                        recommendation_score=0.5,
                        source_quality_score=0.0,
                        competitors=[],
                        sources=[{"url": "https://one.example"}, {"url": "https://two.example"}],
                        parsed_payload={},
                    ),
                    Score(
                        run_id=run.id,
                        visibility_score=1.0,
                        prominence_score=0.5,
                        sentiment_score=0.0,
                        recommendation_score=0.5,
                        source_quality_score=0.0,
                        final_score=0.73,
                    ),
                    RawResponse(
                        run_id=run.id,
                        request_snapshot={"query": "safe"},
                        raw_answer=raw_answer,
                        citations=[],
                        provider_metadata={"model": "openai/gpt-4o-mini"},
                        provider_status="success",
                    ),
                ]
            )
            await session.commit()

    async def _add_failed_run(
        self,
        *,
        audit_id: int,
        query_id: int,
        target_id: int,
        provider: str,
    ) -> None:
        async with self.session_factory() as session:
            run = Run(
                audit_id=audit_id,
                query_id=query_id,
                audit_target_id=target_id,
                provider=provider,
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
                    provider_metadata={"model": "openai/gpt-4o-mini"},
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
