"""Post-process stored raw audit responses into parsed results and scores."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from libs.analysis import parser, scoring
from libs.analysis.competitor_extraction import (
    CompetitorCandidateExtraction,
    CompetitorExtractionInput,
    extract_competitor_candidates,
)
from libs.execution.provider_adapter import ProviderResponse
from libs.execution.safe_logging import duration_ms, log_event, perf_start
from libs.storage.models import (
    Audit,
    AuditStatus,
    AuditTarget,
    Brand,
    CompetitorCandidate,
    Concept,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    Score,
)

logger = logging.getLogger(__name__)

TERMINAL_RUN_STATUSES = {
    RunStatus.SUCCESS,
    RunStatus.ERROR,
    RunStatus.TIMEOUT,
    RunStatus.RATE_LIMITED,
}


@dataclass(frozen=True)
class RunProcessingError:
    run_id: int
    code: str
    message: str

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class AuditPostProcessingSummary:
    audit_id: int
    total_runs_inspected: int = 0
    runs_processed: int = 0
    skipped_already_processed: int = 0
    skipped_missing_raw_response: int = 0
    skipped_non_successful_run: int = 0
    errors: list[RunProcessingError] = field(default_factory=list)
    fatal_error: str | None = None
    audit_status: str | None = None

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "total_runs_inspected": self.total_runs_inspected,
            "runs_processed": self.runs_processed,
            "skipped_already_processed": self.skipped_already_processed,
            "skipped_missing_raw_response": self.skipped_missing_raw_response,
            "skipped_non_successful_run": self.skipped_non_successful_run,
            "errors": [error.safe_log_dict() for error in self.errors],
            "fatal_error": self.fatal_error,
            "audit_status": self.audit_status,
        }


async def process_audit_results(
    session: AsyncSession,
    audit_id: int,
) -> AuditPostProcessingSummary:
    """Process stored raw responses for one audit without calling providers."""
    processing_start = perf_start()
    log_event(logger, "post_processing_started", audit_id=audit_id)
    audit_row = (
        await session.execute(
            select(Audit, Brand).join(Brand, Audit.brand_id == Brand.id).where(
                Audit.id == audit_id
            )
        )
    ).first()
    if audit_row is None:
        log_event(
            logger,
            "post_processing_failed",
            audit_id=audit_id,
            duration_ms=duration_ms(processing_start),
            error_code="audit_not_found",
        )
        return AuditPostProcessingSummary(
            audit_id=audit_id,
            fatal_error=f"Audit with id={audit_id} was not found.",
        )

    audit, brand = audit_row
    counters = _MutableProcessingCounters(audit_id=audit_id)

    try:
        rows = (
            await session.execute(
                select(Run, Query, RawResponse, ParsedResult, Score)
                .join(Query, Run.query_id == Query.id)
                .outerjoin(RawResponse, RawResponse.run_id == Run.id)
                .outerjoin(ParsedResult, ParsedResult.run_id == Run.id)
                .outerjoin(Score, Score.run_id == Run.id)
                .where(Run.audit_id == audit_id)
                .order_by(Query.id, Run.provider, Run.run_number, Run.id)
            )
        ).all()
        counters.total_runs_inspected = len(rows)

        for run, query, raw_response, parsed_result, score in rows:
            await _process_run(
                session=session,
                brand=brand,
                run=run,
                query=query,
                raw_response=raw_response,
                parsed_result=parsed_result,
                score=score,
                counters=counters,
            )

        await session.flush()
        await _rebuild_concepts_and_competitor_candidates(
            session=session,
            audit=audit,
            brand=brand,
        )
        audit.status = await _derive_post_processing_status(
            session=session,
            audit=audit,
            processing_errors=bool(counters.errors),
            missing_raw_count=counters.skipped_missing_raw_response,
        )
        await session.commit()
        await session.refresh(audit)
        counters.audit_status = _enum_value(audit.status)
        summary = counters.to_summary()
        log_event(
            logger,
            "post_processing_completed",
            audit_id=audit_id,
            status=summary.audit_status,
            duration_ms=duration_ms(processing_start),
            runs_processed=summary.runs_processed,
        )
        return summary
    except SQLAlchemyError as exc:
        await session.rollback()
        log_event(
            logger,
            "post_processing_failed",
            audit_id=audit_id,
            duration_ms=duration_ms(processing_start),
            error_code=exc.__class__.__name__,
        )
        return counters.to_summary(
            fatal_error=f"Database failure during post-processing: {exc.__class__.__name__}."
        )


@dataclass
class _MutableProcessingCounters:
    audit_id: int
    total_runs_inspected: int = 0
    runs_processed: int = 0
    skipped_already_processed: int = 0
    skipped_missing_raw_response: int = 0
    skipped_non_successful_run: int = 0
    errors: list[RunProcessingError] = field(default_factory=list)
    audit_status: str | None = None

    def to_summary(self, fatal_error: str | None = None) -> AuditPostProcessingSummary:
        return AuditPostProcessingSummary(
            audit_id=self.audit_id,
            total_runs_inspected=self.total_runs_inspected,
            runs_processed=self.runs_processed,
            skipped_already_processed=self.skipped_already_processed,
            skipped_missing_raw_response=self.skipped_missing_raw_response,
            skipped_non_successful_run=self.skipped_non_successful_run,
            errors=list(self.errors),
            fatal_error=fatal_error,
            audit_status=self.audit_status,
        )


async def _process_run(
    *,
    session: AsyncSession,
    brand: Brand,
    run: Run,
    query: Query,
    raw_response: RawResponse | None,
    parsed_result: ParsedResult | None,
    score: Score | None,
    counters: _MutableProcessingCounters,
) -> None:
    run_processing_start = perf_start()
    if run.status != RunStatus.SUCCESS:
        counters.skipped_non_successful_run += 1
        return

    if raw_response is None or not _has_raw_answer(raw_response):
        counters.skipped_missing_raw_response += 1
        return

    if parsed_result is not None and score is not None:
        counters.skipped_already_processed += 1
        return

    try:
        parsed_payload = (
            _parsed_result_to_dict(parsed_result)
            if parsed_result is not None
            else parser.parse(
                brand_name=brand.name,
                brand_domain=brand.domain,
                query=query.text,
                provider_response=_provider_response_from_raw_response(raw_response),
            )
        )
        created_any = False

        if parsed_result is None:
            session.add(ParsedResult(run_id=run.id, **_parsed_result_fields(parsed_payload)))
            created_any = True

        if score is None:
            computed_score = scoring.compute_score(parsed_payload)
            session.add(Score(run_id=run.id, **_score_fields(computed_score)))
            created_any = True

        if created_any:
            counters.runs_processed += 1
            log_event(
                logger,
                "run_processing_completed",
                audit_id=counters.audit_id,
                run_id=run.id,
                query_id=query.id,
                raw_response_id=raw_response.id,
                parsed_result_id=parsed_result.id if parsed_result is not None else None,
                score_id=score.id if score is not None else None,
                duration_ms=duration_ms(run_processing_start),
                status="processed",
            )
        else:
            counters.skipped_already_processed += 1
    except Exception as exc:
        counters.errors.append(
            RunProcessingError(
                run_id=run.id,
                code="post_processing_error",
                message=f"Run post-processing failed: {exc.__class__.__name__}.",
            )
        )
        log_event(
            logger,
            "post_processing_failed",
            audit_id=counters.audit_id,
            run_id=run.id,
            query_id=query.id,
            raw_response_id=raw_response.id if raw_response is not None else None,
            duration_ms=duration_ms(run_processing_start),
            status="error",
            error_code="post_processing_error",
        )


def _has_raw_answer(raw_response: RawResponse) -> bool:
    return isinstance(raw_response.raw_answer, str) and bool(raw_response.raw_answer.strip())


def _provider_response_from_raw_response(raw_response: RawResponse) -> ProviderResponse:
    return ProviderResponse(
        status="success",
        raw_answer=raw_response.raw_answer,
        citations=raw_response.citations or [],
        response_time=raw_response.response_time,
        error=None,
        provider_metadata=raw_response.provider_metadata,
    )


def _parsed_result_fields(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "visible_brand": bool(parsed.get("visible_brand")),
        "brand_position_rank": _int_or_none(parsed.get("brand_position_rank")),
        "prominence_score": _float_or_default(parsed.get("prominence_score")),
        "sentiment": _float_or_default(parsed.get("sentiment")),
        "recommendation_score": _float_or_default(parsed.get("recommendation_score")),
        "source_quality_score": _float_or_default(parsed.get("source_quality_score")),
        "competitors": _list_or_empty(parsed.get("competitors")),
        "sources": _list_or_empty(parsed.get("sources")),
        "parsed_payload": _dict_or_empty(parsed.get("parsed_payload")),
    }


def _score_fields(score: dict[str, Any]) -> dict[str, float]:
    return {
        "visibility_score": _float_or_default(score.get("visibility_score")),
        "prominence_score": _float_or_default(score.get("prominence_score")),
        "sentiment_score": _float_or_default(score.get("sentiment_score")),
        "recommendation_score": _float_or_default(score.get("recommendation_score")),
        "source_quality_score": _float_or_default(score.get("source_quality_score")),
        "final_score": _float_or_default(score.get("final_score")),
    }


def _parsed_result_to_dict(parsed_result: ParsedResult) -> dict[str, Any]:
    return {
        "visible_brand": parsed_result.visible_brand,
        "brand_position_rank": parsed_result.brand_position_rank,
        "prominence_score": parsed_result.prominence_score,
        "sentiment": parsed_result.sentiment,
        "recommendation_score": parsed_result.recommendation_score,
        "source_quality_score": parsed_result.source_quality_score,
        "competitors": parsed_result.competitors,
        "sources": parsed_result.sources,
        "parsed_payload": parsed_result.parsed_payload,
    }


async def _rebuild_concepts_and_competitor_candidates(
    *,
    session: AsyncSession,
    audit: Audit,
    brand: Brand,
) -> None:
    await session.execute(delete(Concept).where(Concept.audit_id == audit.id))
    await session.execute(
        delete(CompetitorCandidate).where(CompetitorCandidate.audit_id == audit.id)
    )

    rows = (
        await session.execute(
            select(Run, Query, ParsedResult, RawResponse, AuditTarget)
            .join(Query, Run.query_id == Query.id)
            .join(ParsedResult, ParsedResult.run_id == Run.id)
            .outerjoin(RawResponse, RawResponse.run_id == Run.id)
            .outerjoin(AuditTarget, AuditTarget.id == Run.audit_target_id)
            .where(Run.audit_id == audit.id, Run.status == RunStatus.SUCCESS)
            .order_by(Query.id, Run.provider, Run.run_number, Run.id)
        )
    ).all()

    concepts: dict[str, dict[str, Any]] = {}
    candidates: dict[str, dict[str, Any]] = {}
    for run, query, parsed_result, raw_response, target in rows:
        _collect_legacy_concepts(
            concepts=concepts,
            audit=audit,
            run=run,
            query=query,
            parsed_result=parsed_result,
            raw_response=raw_response,
            target=target,
        )
        if raw_response is None or not _has_raw_answer(raw_response):
            continue
        for candidate in extract_competitor_candidates(
            CompetitorExtractionInput(
                answer_text=raw_response.raw_answer or "",
                query_text=query.text,
                brand_name=brand.name,
                brand_domain=brand.domain,
                query_id=query.id,
                run_id=run.id,
                target_id=target.id if target is not None else None,
                level=_run_level(audit, target),
                model_id=_provider_model_from_metadata(raw_response.provider_metadata),
            )
        ):
            _merge_competitor_candidate(candidates, candidate)

    for item in concepts.values():
        session.add(
            Concept(
                audit_id=audit.id,
                text=item["text"],
                category="legacy_phrase",
                count=item["count"],
                evidence_count=len(item["evidence"]),
                evidence=item["evidence"],
            )
        )
    for item in candidates.values():
        session.add(
            CompetitorCandidate(
                audit_id=audit.id,
                name=item["name"],
                domain=item["domain"],
                confidence=item["confidence"],
                evidence_type=item["evidence_type"],
                evidence_count=len(item["evidence"]),
                evidence=item["evidence"],
            )
        )


def _collect_legacy_concepts(
    *,
    concepts: dict[str, dict[str, Any]],
    audit: Audit,
    run: Run,
    query: Query,
    parsed_result: ParsedResult,
    raw_response: RawResponse | None,
    target: AuditTarget | None,
) -> None:
    for value in _list_or_empty(parsed_result.competitors):
        text = _legacy_competitor_text(value)
        if not text:
            continue
        normalized = text.casefold()
        concept = concepts.setdefault(
            normalized,
            {"text": text, "count": 0, "evidence": []},
        )
        concept["count"] += 1
        concept["evidence"].append(
            {
                "query_id": query.id,
                "run_id": run.id,
                "target_id": target.id if target is not None else None,
                "answer_excerpt": _evidence_excerpt(raw_response, text),
                "matched_phrase": text,
                "evidence_type": "legacy_parser_competitor",
                "level": _run_level(audit, target),
                "model_id": (
                    _provider_model_from_metadata(raw_response.provider_metadata)
                    if raw_response is not None
                    else None
                ),
                "execution_provider": run.provider,
            }
        )


def _merge_competitor_candidate(
    candidates: dict[str, dict[str, Any]],
    candidate: CompetitorCandidateExtraction,
) -> None:
    key = f"{candidate.name.casefold()}|{(candidate.domain or '').casefold()}"
    existing = candidates.setdefault(
        key,
        {
            "name": candidate.name,
            "domain": candidate.domain,
            "confidence": candidate.confidence,
            "evidence_type": candidate.evidence_type,
            "evidence": [],
        },
    )
    existing["confidence"] = max(existing["confidence"], candidate.confidence)
    if existing["domain"] is None:
        existing["domain"] = candidate.domain
    existing["evidence"].extend(evidence.to_dict() for evidence in candidate.evidence)


def _legacy_competitor_text(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        name = value.get("name") or value.get("brand") or value.get("competitor")
        if isinstance(name, str):
            return name.strip() or None
    return None


def _evidence_excerpt(raw_response: RawResponse | None, text: str) -> str:
    if raw_response is None or not _has_raw_answer(raw_response):
        return ""
    raw_answer = raw_response.raw_answer or ""
    index = raw_answer.casefold().find(text.casefold())
    if index < 0:
        return raw_answer[:240]
    start = max(index - 80, 0)
    end = min(index + len(text) + 80, len(raw_answer))
    return raw_answer[start:end][:240]


def _run_level(audit: Audit, target: AuditTarget | None) -> str:
    level = target.level if target is not None else audit.scdl_level
    return level.value if hasattr(level, "value") else str(level)


def _provider_model_from_metadata(provider_metadata: object) -> str | None:
    if isinstance(provider_metadata, dict):
        model = provider_metadata.get("model_id") or provider_metadata.get("model")
        return model if isinstance(model, str) else None
    return None


async def _derive_post_processing_status(
    *,
    session: AsyncSession,
    audit: Audit,
    processing_errors: bool,
    missing_raw_count: int,
) -> AuditStatus:
    expected_runs = await _expected_run_count(session, audit)
    total_runs = (
        await session.execute(select(func.count()).select_from(Run).where(Run.audit_id == audit.id))
    ).scalar_one()
    terminal_runs = (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .where(Run.audit_id == audit.id, Run.status.in_(TERMINAL_RUN_STATUSES))
        )
    ).scalar_one()
    terminal_failure_runs = (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .where(
                Run.audit_id == audit.id,
                Run.status.in_(
                    {
                        RunStatus.ERROR,
                        RunStatus.TIMEOUT,
                        RunStatus.RATE_LIMITED,
                    }
                ),
            )
        )
    ).scalar_one()
    successful_runs = (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .where(Run.audit_id == audit.id, Run.status == RunStatus.SUCCESS)
        )
    ).scalar_one()
    scored_successful_runs = (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .join(ParsedResult, ParsedResult.run_id == Run.id)
            .join(Score, Score.run_id == Run.id)
            .where(Run.audit_id == audit.id, Run.status == RunStatus.SUCCESS)
        )
    ).scalar_one()

    all_expected_terminal = expected_runs > 0 and terminal_runs >= expected_runs
    all_successful_runs_processed = scored_successful_runs == successful_runs
    if (
        all_expected_terminal
        and total_runs >= expected_runs
        and terminal_failure_runs == 0
        and all_successful_runs_processed
        and not processing_errors
        and missing_raw_count == 0
    ):
        return AuditStatus.COMPLETED

    if (
        terminal_failure_runs > 0
        or processing_errors
        or missing_raw_count > 0
    ):
        return AuditStatus.PARTIAL

    return AuditStatus.RUNNING if total_runs else audit.status


async def _expected_run_count(session: AsyncSession, audit: Audit) -> int:
    query_ids = list(
        (
            await session.execute(
                select(Query.id).where(Query.audit_id == audit.id).order_by(Query.id)
            )
        ).scalars().all()
    )
    if audit.max_queries is not None:
        query_ids = query_ids[: audit.max_queries]
    return len(query_ids) * len(audit.providers or []) * audit.runs_per_query


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _float_or_default(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    return float(value)


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if not isinstance(value, int):
        return None
    return value


def _list_or_empty(value: object) -> list:
    return value if isinstance(value, list) else []


def _dict_or_empty(value: object) -> dict:
    return value if isinstance(value, dict) else {}
