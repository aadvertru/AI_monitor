from __future__ import annotations

import unittest
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.audit_schemas import AnswerEvaluationResponse
from libs.evaluation.answer_evaluations import (
    AnswerEvaluationDraft,
    list_answer_evaluations_for_audit,
    upsert_answer_evaluation_for_run,
)
from libs.storage.models import (
    AnswerEvaluation,
    AnswerEvaluationVerdict,
    Audit,
    AuditStatus,
    AuditTarget,
    Base,
    Brand,
    Query,
    Run,
    RunStatus,
    SCDLLevel,
)

NOW = datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc)


class AnswerEvaluationModelTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_evaluation_can_link_to_run_query_and_target(self) -> None:
        async with self.session_factory() as session:
            run, target = await self._create_run(session)

            evaluation = await upsert_answer_evaluation_for_run(
                session,
                run,
                AnswerEvaluationDraft(
                    verdict=AnswerEvaluationVerdict.CORRECT,
                    rationale="  Correct according to facts.  ",
                    confidence=0.9,
                    evaluation_version="eval-v1",
                    evaluated_at=NOW,
                    evaluator_provider="mock",
                    evaluator_model="mock-evaluator",
                    facts_version="facts-v1",
                ),
            )
            await session.commit()

            evaluations = await list_answer_evaluations_for_audit(session, run.audit_id)

        self.assertEqual(len(evaluations), 1)
        self.assertEqual(evaluation.run_id, run.id)
        self.assertEqual(evaluation.query_id, run.query_id)
        self.assertEqual(evaluation.target_id, target.id)
        self.assertEqual(evaluation.verdict, AnswerEvaluationVerdict.CORRECT)
        self.assertEqual(evaluation.rationale, "Correct according to facts.")
        self.assertEqual(evaluation.confidence, 0.9)
        self.assertEqual(evaluation.evaluation_version, "eval-v1")
        self.assertEqual(evaluation.evaluator_provider, "mock")
        self.assertEqual(evaluations[0].facts_version, "facts-v1")

    async def test_upsert_replaces_current_evaluation_for_run(self) -> None:
        async with self.session_factory() as session:
            run, _target = await self._create_run(session)
            first = await upsert_answer_evaluation_for_run(
                session,
                run,
                AnswerEvaluationDraft(
                    verdict=AnswerEvaluationVerdict.PARTIAL,
                    evaluation_version="eval-v1",
                    confidence=0.5,
                    evaluated_at=NOW,
                ),
            )
            await session.flush()
            second = await upsert_answer_evaluation_for_run(
                session,
                run,
                AnswerEvaluationDraft(
                    verdict=AnswerEvaluationVerdict.INCORRECT,
                    evaluation_version="eval-v2",
                    confidence=0.7,
                    evaluated_at=NOW,
                ),
            )
            await session.commit()
            evaluations = await list_answer_evaluations_for_audit(session, run.audit_id)

        self.assertEqual(first.id, second.id)
        self.assertEqual(len(evaluations), 1)
        self.assertEqual(evaluations[0].verdict, AnswerEvaluationVerdict.INCORRECT)
        self.assertEqual(evaluations[0].evaluation_version, "eval-v2")

    async def test_invalid_verdict_and_confidence_are_rejected(self) -> None:
        async with self.session_factory() as session:
            run, _target = await self._create_run(session)
            session.add(
                AnswerEvaluation(
                    audit_id=run.audit_id,
                    run_id=run.id,
                    query_id=run.query_id,
                    target_id=run.audit_target_id,
                    verdict="bogus",
                    rationale=None,
                    confidence=1.5,
                    evaluation_version="eval-v1",
                    evaluated_at=NOW,
                )
            )

            with self.assertRaises((IntegrityError, LookupError, ValueError)):
                await session.flush()

    async def test_legacy_run_without_evaluation_remains_valid(self) -> None:
        async with self.session_factory() as session:
            run, _target = await self._create_run(session, with_target=False)
            evaluations = await list_answer_evaluations_for_audit(session, run.audit_id)

        self.assertEqual(evaluations, [])
        self.assertIsNone(run.audit_target_id)

    async def test_evaluation_dto_excludes_raw_prompt_response_and_secrets(self) -> None:
        payload = AnswerEvaluationResponse(
            verdict="correct",
            rationale="Safe rationale.",
            confidence=0.8,
            evaluation_version="eval-v1",
            evaluated_at=NOW,
        ).model_dump()

        serialized = str(payload)
        self.assertNotIn("prompt", serialized)
        self.assertNotIn("raw_response", serialized)
        self.assertNotIn("api_key", serialized)
        self.assertNotIn("sk-", serialized)

    async def test_answer_evaluations_table_exists_in_metadata(self) -> None:
        async with self.engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='answer_evaluations'"
                )
            )

        self.assertEqual(result.scalar_one(), "answer_evaluations")

    async def _create_run(
        self,
        session,
        *,
        with_target: bool = True,
    ) -> tuple[Run, AuditTarget | None]:
        brand = Brand(name=f"Eval Brand {id(session)}", domain="eval.example")
        audit = Audit(
            brand=brand,
            status=AuditStatus.COMPLETED,
            providers=["openrouter"],
            runs_per_query=1,
            scdl_level=SCDLLevel.L1,
        )
        session.add(audit)
        await session.flush()
        query = Query(audit_id=audit.id, text="best eval tools")
        session.add(query)
        await session.flush()
        target = None
        if with_target:
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="chatgpt",
                execution_provider="openrouter",
                model_provider="openai",
                model_id="openai/gpt-4o-mini",
                display_name="GPT-4o mini",
                level=SCDLLevel.L1,
                gateway=True,
            )
            session.add(target)
            await session.flush()
        run = Run(
            audit_id=audit.id,
            query_id=query.id,
            audit_target_id=target.id if target is not None else None,
            provider="openrouter",
            run_number=1,
            status=RunStatus.SUCCESS,
        )
        session.add(run)
        await session.flush()
        return run, target


if __name__ == "__main__":
    unittest.main()
