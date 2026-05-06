"""Audit answer evaluation runner."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.evaluation.answer_evaluations import (
    AnswerEvaluationDraft,
    upsert_answer_evaluation_for_run,
)
from libs.evaluation.brand_facts import list_brand_facts_for_audit
from libs.evaluation.evaluator import (
    AnswerEvaluationInput,
    AnswerEvaluator,
    MockAnswerEvaluator,
    evaluate_answer_safely,
)
from libs.storage.models import Audit, AuditTarget, Query, RawResponse, Run, RunStatus


@dataclass(frozen=True)
class AnswerEvaluationRerunSummary:
    audit_id: int
    evaluated_runs: int = 0
    skipped_runs: int = 0
    status: str = "completed"
    warnings: list[str] = field(default_factory=list)


async def rerun_answer_evaluations_for_audit(
    session: AsyncSession,
    audit: Audit,
    *,
    evaluator: AnswerEvaluator | None = None,
) -> AnswerEvaluationRerunSummary:
    evaluator = evaluator or MockAnswerEvaluator()
    brand_facts = await list_brand_facts_for_audit(session, audit.id)
    warnings: list[str] = []
    if not brand_facts:
        warnings.append("No brand facts were available for answer evaluation.")

    rows = (
        await session.execute(
            select(Run, Query, RawResponse, AuditTarget)
            .join(Query, Run.query_id == Query.id)
            .outerjoin(RawResponse, RawResponse.run_id == Run.id)
            .outerjoin(AuditTarget, AuditTarget.id == Run.audit_target_id)
            .where(Run.audit_id == audit.id)
            .order_by(Run.id)
        )
    ).all()

    evaluated_runs = 0
    skipped_runs = 0
    for run, query, raw_response, target in rows:
        answer_text = _usable_answer_text(run, raw_response)
        if answer_text is None:
            skipped_runs += 1
            continue

        level = _level_for_run(audit, target)
        model_id = _model_id_for_run(run, target)
        result = await evaluate_answer_safely(
            evaluator,
            AnswerEvaluationInput(
                audit_id=audit.id,
                run_id=run.id,
                query_text=query.text,
                answer_text=answer_text,
                brand_facts=brand_facts,
                level=level,
                model_id=model_id,
            ),
        )
        await upsert_answer_evaluation_for_run(
            session,
            run,
            AnswerEvaluationDraft(
                verdict=result.verdict,
                rationale=result.rationale,
                confidence=result.confidence,
                evaluation_version=result.evaluation_version,
                evaluator_provider="mock",
                evaluator_model=model_id,
                facts_version="brand-facts-v1",
            ),
        )
        evaluated_runs += 1

    await session.commit()
    return AnswerEvaluationRerunSummary(
        audit_id=audit.id,
        evaluated_runs=evaluated_runs,
        skipped_runs=skipped_runs,
        warnings=warnings,
    )


def _usable_answer_text(run: Run, raw_response: RawResponse | None) -> str | None:
    if run.status != RunStatus.SUCCESS or raw_response is None:
        return None
    normalized = " ".join((raw_response.raw_answer or "").strip().split())
    return normalized or None


def _level_for_run(audit: Audit, target: AuditTarget | None) -> str:
    level = target.level if target is not None else audit.scdl_level
    return level.value if hasattr(level, "value") else str(level)


def _model_id_for_run(run: Run, target: AuditTarget | None) -> str:
    if target is not None:
        return target.model_id
    return run.provider
