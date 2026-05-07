"""Immutable audit metric snapshots for longitudinal analytics."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.storage.models import (
    AnswerEvaluation,
    AnswerEvaluationVerdict,
    Audit,
    AuditMetricsSnapshot,
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

SOURCE_AGGREGATION_VERSION = "source-domains-v1"
COMPETITOR_EXTRACTOR_VERSION = "competitor-extractor-v1"

TERMINAL_SNAPSHOT_STATUSES = {
    AuditStatus.COMPLETED,
    AuditStatus.PARTIAL,
    AuditStatus.CANCELLED,
    AuditStatus.FAILED,
}


@dataclass(frozen=True)
class SnapshotBuildResult:
    snapshot: AuditMetricsSnapshot | None
    skipped_reason: str | None = None


def normalize_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    value = domain.strip().lower().rstrip("/")
    value = re.sub(r"^https?://", "", value)
    value = value.split("/", 1)[0].split("?", 1)[0]
    if value.startswith("www."):
        value = value[4:]
    return value or None


def normalize_brand_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


async def create_audit_metrics_snapshot(
    session: AsyncSession,
    audit_id: int,
    *,
    force_new_version: bool = False,
) -> SnapshotBuildResult:
    audit = await session.get(Audit, audit_id)
    if audit is None:
        return SnapshotBuildResult(snapshot=None, skipped_reason="audit_not_found")
    if audit.status not in TERMINAL_SNAPSHOT_STATUSES:
        return SnapshotBuildResult(snapshot=None, skipped_reason="audit_not_terminal")

    brand = await session.get(Brand, audit.brand_id)
    if brand is None:
        return SnapshotBuildResult(snapshot=None, skipped_reason="brand_not_found")

    existing = await latest_audit_snapshot(session, audit_id)
    if existing is not None and not force_new_version:
        return SnapshotBuildResult(snapshot=existing)

    payload = await build_snapshot_payload(session, audit, brand)
    if not _has_usable_snapshot_data(payload) and audit.status in {
        AuditStatus.FAILED,
        AuditStatus.CANCELLED,
    }:
        return SnapshotBuildResult(snapshot=None, skipped_reason="no_usable_data")

    version = (existing.snapshot_version + 1) if existing is not None else 1
    snapshot = AuditMetricsSnapshot(
        audit_id=audit.id,
        brand_id=audit.brand_id,
        user_id=audit.user_id,
        normalized_domain=normalize_domain(brand.domain),
        normalized_brand_name=normalize_brand_name(brand.name),
        snapshot_version=version,
        audit_status=audit.status,
        audit_created_at=audit.created_at,
        audit_completed_at=audit.updated_at,
        summary_metrics=payload["summary_metrics"],
        model_summaries=payload["model_summaries"],
        source_domains_summary=payload["source_domains_summary"],
        concepts_summary=payload["concepts_summary"],
        competitors_summary=payload["competitors_summary"],
        parser_version=payload["versions"].get("parser_version"),
        scoring_version=payload["versions"].get("scoring_version"),
        evaluation_version=payload["versions"].get("evaluation_version"),
        source_aggregation_version=SOURCE_AGGREGATION_VERSION,
        competitor_extractor_version=COMPETITOR_EXTRACTOR_VERSION,
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return SnapshotBuildResult(snapshot=snapshot)


async def latest_audit_snapshot(
    session: AsyncSession,
    audit_id: int,
) -> AuditMetricsSnapshot | None:
    return (
        await session.execute(
            select(AuditMetricsSnapshot)
            .where(AuditMetricsSnapshot.audit_id == audit_id)
            .order_by(AuditMetricsSnapshot.snapshot_version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def latest_snapshots_for_user(
    session: AsyncSession,
    user_id: int | None,
) -> list[AuditMetricsSnapshot]:
    rows = (
        await session.execute(
            select(AuditMetricsSnapshot)
            .where(AuditMetricsSnapshot.user_id == user_id)
            .order_by(
                AuditMetricsSnapshot.audit_completed_at.desc(),
                AuditMetricsSnapshot.id.desc(),
            )
        )
    ).scalars()
    latest: dict[int, AuditMetricsSnapshot] = {}
    for snapshot in rows:
        latest.setdefault(snapshot.audit_id, snapshot)
    return list(latest.values())


async def build_snapshot_payload(
    session: AsyncSession,
    audit: Audit,
    brand: Brand,
) -> dict[str, Any]:
    rows = await _run_rows(session, audit.id)
    query_count = await _query_count(session, audit.id)
    target_count = await _target_count(session, audit)
    evaluations = {
        evaluation.run_id: evaluation
        for evaluation in (
            await session.execute(
                select(AnswerEvaluation).where(AnswerEvaluation.audit_id == audit.id)
            )
        ).scalars()
    }

    summary_metrics = {
        "query_count": query_count,
        "target_count": target_count,
        "run_count": len(rows),
        "completed_runs": sum(1 for row in rows if row["run"].status == RunStatus.SUCCESS),
        "failed_runs": sum(
            1
            for row in rows
            if row["run"].status
            in {RunStatus.ERROR, RunStatus.TIMEOUT, RunStatus.RATE_LIMITED}
        ),
        "mentionability_l1": _mentionability(rows, "L1"),
        "mentionability_l2": _mentionability(rows, "L2"),
        "accuracy_l1": _accuracy(rows, evaluations, "L1"),
        "accuracy_l2": _accuracy(rows, evaluations, "L2"),
    }

    return {
        "summary_metrics": summary_metrics,
        "model_summaries": _model_summaries(rows, evaluations),
        "source_domains_summary": _source_domains(rows),
        "concepts_summary": await _concepts(session, audit.id),
        "competitors_summary": await _competitors(session, audit.id),
        "versions": await _analysis_versions(session, audit.id),
        "normalized_domain": normalize_domain(brand.domain),
        "normalized_brand_name": normalize_brand_name(brand.name),
    }


async def _run_rows(session: AsyncSession, audit_id: int) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(Run, AuditTarget, ParsedResult, Score)
            .outerjoin(AuditTarget, AuditTarget.id == Run.audit_target_id)
            .outerjoin(ParsedResult, ParsedResult.run_id == Run.id)
            .outerjoin(Score, Score.run_id == Run.id)
            .where(Run.audit_id == audit_id)
            .order_by(Run.id)
        )
    ).all()
    return [
        {"run": run, "target": target, "parsed": parsed, "score": score}
        for run, target, parsed, score in rows
    ]


async def _query_count(session: AsyncSession, audit_id: int) -> int:
    return int(
        (
            await session.execute(
                select(func.count()).select_from(Query).where(Query.audit_id == audit_id)
            )
        ).scalar_one()
    )


async def _target_count(session: AsyncSession, audit: Audit) -> int:
    count = int(
        (
            await session.execute(
                select(func.count())
                .select_from(AuditTarget)
                .where(AuditTarget.audit_id == audit.id)
            )
        ).scalar_one()
    )
    return count or len(audit.providers or [])


def _row_level(row: dict[str, Any]) -> str:
    target = row["target"]
    if target is not None:
        return _enum_value(target.level)
    return "L1"


def _mentionability(rows: list[dict[str, Any]], level: str) -> float | None:
    processed = [
        row
        for row in rows
        if _row_level(row) == level
        and row["run"].status == RunStatus.SUCCESS
        and row["parsed"] is not None
    ]
    if not processed:
        return None
    found = sum(1 for row in processed if row["parsed"].visible_brand)
    return round((found / len(processed)) * 100, 2)


def _accuracy(
    rows: list[dict[str, Any]],
    evaluations: dict[int, AnswerEvaluation],
    level: str,
) -> float | None:
    relevant = [
        evaluations[row["run"].id]
        for row in rows
        if _row_level(row) == level and row["run"].id in evaluations
    ]
    strict = [
        item
        for item in relevant
        if _enum_value(item.verdict) in {"correct", "partial", "incorrect"}
    ]
    if not strict:
        return None
    correct = sum(1 for item in strict if item.verdict == AnswerEvaluationVerdict.CORRECT)
    return round(correct / len(strict), 4)


def _model_summaries(
    rows: list[dict[str, Any]],
    evaluations: dict[int, AnswerEvaluation],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        target = row["target"]
        key = target.model_id if target is not None else row["run"].provider
        grouped[key].append(row)

    summaries = []
    for model_id, group in sorted(grouped.items()):
        target = next((row["target"] for row in group if row["target"] is not None), None)
        summaries.append(
            {
                "model_id": model_id,
                "label": target.display_name if target is not None else model_id,
                "execution_provider": (
                    target.execution_provider if target is not None else group[0]["run"].provider
                ),
                "level": _row_level(group[0]),
                "run_count": len(group),
                "mentionability": _mentionability(group, _row_level(group[0])),
                "accuracy": _accuracy(group, evaluations, _row_level(group[0])),
            }
        )
    return summaries


def _source_domains(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domains: Counter[str] = Counter()
    for row in rows:
        parsed = row["parsed"]
        if parsed is None or not isinstance(parsed.sources, list):
            continue
        for source in parsed.sources:
            if not isinstance(source, dict):
                continue
            domain = source.get("domain")
            if isinstance(domain, str) and domain:
                domains[domain.lower()] += 1
    return [
        {"domain": domain, "source_count": count}
        for domain, count in sorted(domains.items(), key=lambda item: (-item[1], item[0]))
    ]


async def _concepts(session: AsyncSession, audit_id: int) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(Concept).where(Concept.audit_id == audit_id).order_by(Concept.text)
        )
    ).scalars()
    return [
        {
            "text": concept.text,
            "category": concept.category,
            "count": concept.count,
            "evidence_count": concept.evidence_count,
        }
        for concept in rows
    ]


async def _competitors(session: AsyncSession, audit_id: int) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(CompetitorCandidate)
            .where(CompetitorCandidate.audit_id == audit_id)
            .order_by(CompetitorCandidate.name)
        )
    ).scalars()
    return [
        {
            "name": candidate.name,
            "domain": candidate.domain,
            "confidence": candidate.confidence,
            "evidence_type": candidate.evidence_type,
            "evidence_count": candidate.evidence_count,
        }
        for candidate in rows
    ]


async def _analysis_versions(session: AsyncSession, audit_id: int) -> dict[str, str | None]:
    raw_rows = (
        await session.execute(
            select(RawResponse.provider_metadata)
            .join(Run, RawResponse.run_id == Run.id)
            .where(Run.audit_id == audit_id)
        )
    ).scalars()
    parser_version = None
    scoring_version = None
    for metadata in raw_rows:
        if not isinstance(metadata, dict):
            continue
        parser_version = parser_version or _safe_str(metadata.get("parser_version"))
        scoring_version = scoring_version or _safe_str(metadata.get("scoring_version"))

    evaluation_version = (
        await session.execute(
            select(AnswerEvaluation.evaluation_version)
            .where(AnswerEvaluation.audit_id == audit_id)
            .limit(1)
        )
    ).scalar_one_or_none()

    return {
        "parser_version": parser_version,
        "scoring_version": scoring_version,
        "evaluation_version": evaluation_version,
    }


def _has_usable_snapshot_data(payload: dict[str, Any]) -> bool:
    metrics = payload["summary_metrics"]
    return bool(metrics["completed_runs"] or payload["model_summaries"])


def _safe_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)
