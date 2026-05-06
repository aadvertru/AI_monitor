"""Persistent answer evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.storage.models import AnswerEvaluation, AnswerEvaluationVerdict, Run


@dataclass(frozen=True)
class AnswerEvaluationDraft:
    verdict: AnswerEvaluationVerdict
    evaluation_version: str
    rationale: str | None = None
    confidence: float | None = None
    evaluated_at: datetime | None = None
    evaluator_provider: str | None = None
    evaluator_model: str | None = None
    facts_version: str | None = None


async def upsert_answer_evaluation_for_run(
    session: AsyncSession,
    run: Run,
    draft: AnswerEvaluationDraft,
) -> AnswerEvaluation:
    existing = (
        await session.execute(
            select(AnswerEvaluation).where(AnswerEvaluation.run_id == run.id)
        )
    ).scalar_one_or_none()
    evaluated_at = draft.evaluated_at or datetime.now(tz=timezone.utc)

    if existing is None:
        existing = AnswerEvaluation(
            audit_id=run.audit_id,
            run_id=run.id,
            query_id=run.query_id,
            target_id=run.audit_target_id,
            verdict=draft.verdict,
            rationale=_safe_rationale(draft.rationale),
            confidence=draft.confidence,
            evaluation_version=draft.evaluation_version,
            evaluated_at=evaluated_at,
            evaluator_provider=draft.evaluator_provider,
            evaluator_model=draft.evaluator_model,
            facts_version=draft.facts_version,
        )
        session.add(existing)
    else:
        existing.audit_id = run.audit_id
        existing.query_id = run.query_id
        existing.target_id = run.audit_target_id
        existing.verdict = draft.verdict
        existing.rationale = _safe_rationale(draft.rationale)
        existing.confidence = draft.confidence
        existing.evaluation_version = draft.evaluation_version
        existing.evaluated_at = evaluated_at
        existing.evaluator_provider = draft.evaluator_provider
        existing.evaluator_model = draft.evaluator_model
        existing.facts_version = draft.facts_version

    return existing


async def list_answer_evaluations_for_audit(
    session: AsyncSession,
    audit_id: int,
) -> list[AnswerEvaluation]:
    rows = (
        await session.execute(
            select(AnswerEvaluation)
            .where(AnswerEvaluation.audit_id == audit_id)
            .order_by(AnswerEvaluation.run_id)
        )
    ).scalars()
    return list(rows)


def _safe_rationale(value: str | None) -> str | None:
    normalized = " ".join((value or "").strip().split())
    return normalized or None
