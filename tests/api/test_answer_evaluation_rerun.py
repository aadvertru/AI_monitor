from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import rerun_audit_answer_evaluation
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    AnswerEvaluation,
    AnswerEvaluationVerdict,
    Audit,
    AuditStatus,
    Base,
    Brand,
    BrandFact,
    BrandFactSource,
    BrandFactType,
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
NOW = datetime(2026, 5, 6, 11, 0, tzinfo=timezone.utc)


class AnswerEvaluationRerunAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_unauthenticated_request_is_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit_with_runs(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                with self.assertRaises(HTTPException) as exc:
                    await rerun_audit_answer_evaluation(
                        audit_id=audit_id,
                        request=Request({"type": "http", "headers": []}),
                        session=session,
                    )

        self.assertEqual(exc.exception.status_code, 401)

    async def test_non_owner_request_is_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit_id = await self._create_audit_with_runs(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                with self.assertRaises(HTTPException) as exc:
                    await rerun_audit_answer_evaluation(
                        audit_id=audit_id,
                        request=self._authenticated_request(other),
                        session=session,
                    )

        self.assertEqual(exc.exception.status_code, 404)

    async def test_owner_can_rerun_evaluation_without_mutating_pipeline_outputs(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit_with_runs(owner)

        async with self.session_factory() as session:
            before = await self._pipeline_snapshot(session, audit_id)
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                response = await rerun_audit_answer_evaluation(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )
            after = await self._pipeline_snapshot(session, audit_id)
            evaluations = list(
                (
                    await session.execute(
                        select(AnswerEvaluation).where(
                            AnswerEvaluation.audit_id == audit_id
                        )
                    )
                ).scalars()
            )
            audit = await session.get(Audit, audit_id)

        self.assertEqual(response.audit_id, audit_id)
        self.assertEqual(response.evaluated_runs, 1)
        self.assertEqual(response.skipped_runs, 2)
        self.assertEqual(response.status, "completed")
        self.assertNotIn("raw_answer", response.model_dump())
        self.assertNotIn("secret", str(response.model_dump()).lower())
        self.assertEqual(before, after)
        self.assertEqual(audit.status, AuditStatus.PARTIAL)
        self.assertEqual(len(evaluations), 1)
        self.assertEqual(evaluations[0].verdict, AnswerEvaluationVerdict.CORRECT)
        self.assertEqual(evaluations[0].evaluation_version, "mock-evaluator-v1")

    async def test_existing_evaluation_is_updated_in_place(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit_with_runs(owner, seed_existing=True)

        async with self.session_factory() as session:
            existing_before = (
                await session.execute(
                    select(AnswerEvaluation).where(AnswerEvaluation.audit_id == audit_id)
                )
            ).scalar_one()
            before_id = existing_before.id
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                response = await rerun_audit_answer_evaluation(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )
            existing_after = (
                await session.execute(
                    select(AnswerEvaluation).where(AnswerEvaluation.audit_id == audit_id)
                )
            ).scalar_one()

        self.assertEqual(response.evaluated_runs, 1)
        self.assertEqual(existing_after.id, before_id)
        self.assertEqual(existing_after.verdict, AnswerEvaluationVerdict.CORRECT)

    async def _create_user(self, email: str) -> User:
        async with self.session_factory() as session:
            user = User(email=email, hashed_password="hashed", role=UserRole.USER)
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

    async def _create_audit_with_runs(
        self,
        owner: User,
        *,
        seed_existing: bool = False,
    ) -> int:
        async with self.session_factory() as session:
            brand = Brand(
                name="Eval Runner",
                domain="eval-runner.example",
                description="Evaluation runner test brand.",
            )
            audit = Audit(
                brand=brand,
                user_id=owner.id,
                status=AuditStatus.PARTIAL,
                providers=["mock"],
                runs_per_query=1,
                scdl_level=SCDLLevel.L1,
            )
            session.add(audit)
            await session.flush()
            session.add(
                BrandFact(
                    audit_id=audit.id,
                    brand_id=brand.id,
                    fact_text="Brand name: Eval Runner",
                    fact_type=BrandFactType.BRAND_NAME,
                    source=BrandFactSource.BRAND_NAME,
                    confidence=1.0,
                )
            )
            query = Query(audit_id=audit.id, text="who is eval runner")
            session.add(query)
            await session.flush()
            success_run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            failed_run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=2,
                status=RunStatus.ERROR,
            )
            empty_run = Run(
                audit_id=audit.id,
                query_id=query.id,
                provider="mock",
                run_number=3,
                status=RunStatus.SUCCESS,
            )
            session.add_all([success_run, failed_run, empty_run])
            await session.flush()
            session.add_all(
                [
                    RawResponse(
                        run_id=success_run.id,
                        raw_answer="Eval Runner is the brand. [CORRECT]",
                        provider_status="success",
                        request_snapshot={"prompt": "original prompt"},
                    ),
                    RawResponse(
                        run_id=empty_run.id,
                        raw_answer="  ",
                        provider_status="success",
                    ),
                    ParsedResult(
                        run_id=success_run.id,
                        visible_brand=True,
                        parsed_payload={"before": "unchanged"},
                    ),
                    Score(run_id=success_run.id, final_score=0.75),
                ]
            )
            if seed_existing:
                session.add(
                    AnswerEvaluation(
                        audit_id=audit.id,
                        run_id=success_run.id,
                        query_id=query.id,
                        verdict=AnswerEvaluationVerdict.INCORRECT,
                        rationale="Old evaluation.",
                        confidence=0.1,
                        evaluation_version="old-eval",
                        evaluated_at=NOW,
                    )
                )
            await session.commit()
            return audit.id

    async def _pipeline_snapshot(self, session, audit_id: int) -> dict[str, object]:
        row = (
            await session.execute(
                select(RawResponse, ParsedResult, Score)
                .join(Run, RawResponse.run_id == Run.id)
                .outerjoin(ParsedResult, ParsedResult.run_id == Run.id)
                .outerjoin(Score, Score.run_id == Run.id)
                .where(Run.audit_id == audit_id, Run.status == RunStatus.SUCCESS)
                .order_by(Run.run_number)
            )
        ).first()
        assert row is not None
        raw_response, parsed_result, score = row
        return {
            "raw_answer": raw_response.raw_answer,
            "request_snapshot": raw_response.request_snapshot,
            "parsed_payload": parsed_result.parsed_payload if parsed_result else None,
            "final_score": score.final_score if score else None,
        }


if __name__ == "__main__":
    unittest.main()
