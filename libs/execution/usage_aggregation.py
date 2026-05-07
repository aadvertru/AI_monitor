"""Provider usage aggregation over persisted audit run responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.storage.models import Audit, AuditTarget, RawResponse, Run

USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_tokens",
    "reasoning_tokens",
    "web_search_requests",
    "duration_ms",
)


@dataclass(frozen=True)
class ProviderUsageTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    web_search_requests: int = 0
    duration_ms: int = 0

    def add(self, other: "ProviderUsageTotals") -> "ProviderUsageTotals":
        return ProviderUsageTotals(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            web_search_requests=self.web_search_requests + other.web_search_requests,
            duration_ms=self.duration_ms + other.duration_ms,
        )

    def to_dict(self) -> dict[str, int]:
        return {key: getattr(self, key) for key in USAGE_KEYS}


@dataclass(frozen=True)
class ProviderUsageRun:
    audit_id: int
    user_id: int | None
    run_id: int
    target_id: int | None
    provider: str
    model_id: str | None
    level: str | None
    totals: ProviderUsageTotals

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "user_id": self.user_id,
            "run_id": self.run_id,
            "target_id": self.target_id,
            "provider": self.provider,
            "model_id": self.model_id,
            "level": self.level,
            **self.totals.to_dict(),
        }


@dataclass(frozen=True)
class ProviderTargetUsageSummary:
    audit_id: int
    target_id: int | None
    provider: str
    model_id: str | None
    level: str | None
    run_count: int
    totals: ProviderUsageTotals

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "target_id": self.target_id,
            "provider": self.provider,
            "model_id": self.model_id,
            "level": self.level,
            "run_count": self.run_count,
            **self.totals.to_dict(),
        }


@dataclass(frozen=True)
class ProviderUsageSummary:
    totals: ProviderUsageTotals
    run_count: int
    runs: tuple[ProviderUsageRun, ...] = field(default_factory=tuple)
    targets: tuple[ProviderTargetUsageSummary, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_count": self.run_count,
            "totals": self.totals.to_dict(),
            "runs": [run.to_dict() for run in self.runs],
            "targets": [target.to_dict() for target in self.targets],
        }


async def aggregate_audit_usage(
    session: AsyncSession,
    audit_id: int,
) -> ProviderUsageSummary:
    rows = await _usage_rows(session, audit_id=audit_id)
    return _summary_from_rows(rows)


async def aggregate_user_usage(
    session: AsyncSession,
    user_id: int,
) -> ProviderUsageSummary:
    rows = await _usage_rows(session, user_id=user_id)
    return _summary_from_rows(rows)


async def aggregate_target_usage(
    session: AsyncSession,
    audit_id: int,
) -> tuple[ProviderTargetUsageSummary, ...]:
    summary = await aggregate_audit_usage(session, audit_id)
    return summary.targets


async def _usage_rows(
    session: AsyncSession,
    *,
    audit_id: int | None = None,
    user_id: int | None = None,
) -> list[ProviderUsageRun]:
    statement = (
        select(Run, Audit, AuditTarget, RawResponse)
        .join(Audit, Audit.id == Run.audit_id)
        .outerjoin(AuditTarget, AuditTarget.id == Run.audit_target_id)
        .outerjoin(RawResponse, RawResponse.run_id == Run.id)
        .order_by(Run.id)
    )
    if audit_id is not None:
        statement = statement.where(Run.audit_id == audit_id)
    if user_id is not None:
        statement = statement.where(Audit.user_id == user_id)

    records: list[ProviderUsageRun] = []
    for run, audit, target, raw_response in (await session.execute(statement)).all():
        metadata = _safe_mapping(
            raw_response.provider_metadata if raw_response is not None else None
        )
        totals = _usage_totals(metadata, raw_response)
        records.append(
            ProviderUsageRun(
                audit_id=run.audit_id,
                user_id=audit.user_id,
                run_id=run.id,
                target_id=run.audit_target_id,
                provider=_provider_for_run(run, metadata, target),
                model_id=_model_id_for_run(metadata, target),
                level=_level_for_run(metadata, target, audit),
                totals=totals,
            )
        )
    return records


def _summary_from_rows(rows: list[ProviderUsageRun]) -> ProviderUsageSummary:
    totals = ProviderUsageTotals()
    grouped: dict[
        tuple[int, int | None, str, str | None, str | None],
        tuple[int, ProviderUsageTotals],
    ] = {}
    for row in rows:
        totals = totals.add(row.totals)
        key = (row.audit_id, row.target_id, row.provider, row.model_id, row.level)
        count, existing_totals = grouped.get(key, (0, ProviderUsageTotals()))
        grouped[key] = (count + 1, existing_totals.add(row.totals))

    targets = tuple(
        ProviderTargetUsageSummary(
            audit_id=audit_id,
            target_id=target_id,
            provider=provider,
            model_id=model_id,
            level=level,
            run_count=count,
            totals=target_totals,
        )
        for (audit_id, target_id, provider, model_id, level), (
            count,
            target_totals,
        ) in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1] or 0))
    )
    return ProviderUsageSummary(
        totals=totals,
        run_count=len(rows),
        runs=tuple(rows),
        targets=targets,
    )


def _usage_totals(
    metadata: dict[str, Any],
    raw_response: RawResponse | None,
) -> ProviderUsageTotals:
    usage = _safe_mapping(metadata.get("usage"))
    input_tokens = _non_negative_int(usage.get("input_tokens"))
    output_tokens = _non_negative_int(usage.get("output_tokens"))
    total_tokens = _non_negative_int(usage.get("total_tokens"))
    if total_tokens == 0 and (input_tokens or output_tokens):
        total_tokens = input_tokens + output_tokens

    return ProviderUsageTotals(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cached_tokens=_non_negative_int(usage.get("cached_tokens")),
        reasoning_tokens=_non_negative_int(usage.get("reasoning_tokens")),
        web_search_requests=_non_negative_int(usage.get("web_search_requests")),
        duration_ms=_duration_ms(usage, raw_response),
    )


def _duration_ms(
    usage: dict[str, Any],
    raw_response: RawResponse | None,
) -> int:
    usage_duration = _non_negative_int(usage.get("duration_ms"))
    if usage_duration:
        return usage_duration
    if raw_response is None:
        return 0
    if isinstance(raw_response.response_time, int | float) and raw_response.response_time >= 0:
        return int(round(raw_response.response_time * 1000))
    return 0


def _provider_for_run(
    run: Run,
    metadata: dict[str, Any],
    target: AuditTarget | None,
) -> str:
    return (
        _str_or_none(metadata.get("execution_provider"))
        or _str_or_none(metadata.get("provider"))
        or (target.execution_provider if target is not None else None)
        or run.provider
    )


def _model_id_for_run(
    metadata: dict[str, Any],
    target: AuditTarget | None,
) -> str | None:
    return (
        _str_or_none(metadata.get("model_id"))
        or _str_or_none(metadata.get("model"))
        or (target.model_id if target is not None else None)
    )


def _level_for_run(
    metadata: dict[str, Any],
    target: AuditTarget | None,
    audit: Audit,
) -> str | None:
    level = (
        _str_or_none(metadata.get("level"))
        or (target.level.value if target is not None else None)
        or audit.scdl_level.value
    )
    return level


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int | float) and value >= 0:
        return int(value)
    return 0


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        value = value.value
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None
