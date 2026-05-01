"""Local real-provider dry-run execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.control.job_scheduler import schedule_jobs_for_audit
from libs.execution.audit_execution import execute_audit_jobs
from libs.execution.pilot_config import (
    PilotPolicyError,
    RealProviderPilotConfig,
    load_real_provider_pilot_config,
    validate_audit_against_pilot_config,
)
from libs.execution.provider_adapter import BaseProviderAdapter
from libs.execution.provider_factory import build_provider_adapter
from libs.storage.models import Audit, AuditStatus, Job, Query, RunStatus

ProviderFactory = Callable[[str], BaseProviderAdapter]


@dataclass(frozen=True)
class DryRunResult:
    audit_id: int
    provider_mode: str
    providers: list[str]
    scdl_level: str
    query_count: int
    runs_per_query: int
    total_jobs: int
    executed_jobs: int
    success_count: int
    error_count: int
    timeout_count: int
    rate_limited_count: int
    audit_status: str

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "provider_mode": self.provider_mode,
            "providers": self.providers,
            "scdl_level": self.scdl_level,
            "query_count": self.query_count,
            "runs_per_query": self.runs_per_query,
            "total_jobs": self.total_jobs,
            "executed_jobs": self.executed_jobs,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "rate_limited_count": self.rate_limited_count,
            "audit_status": self.audit_status,
        }


async def execute_real_provider_dry_run(
    session: AsyncSession,
    audit_id: int,
    *,
    pilot_config: RealProviderPilotConfig | None = None,
    provider_factory: ProviderFactory | None = None,
) -> DryRunResult:
    config = pilot_config or load_real_provider_pilot_config()
    if config.provider_mode != "openai" or not config.real_provider_enabled:
        raise PilotPolicyError("Real-provider dry-run is disabled.")

    audit = await session.get(Audit, audit_id)
    if audit is None:
        raise PilotPolicyError(f"Audit with id={audit_id} was not found.")

    providers = [provider.strip().lower() for provider in audit.providers or []]
    query_count = await _effective_query_count(session, audit)
    scdl_level = (
        audit.scdl_level.value
        if hasattr(audit.scdl_level, "value")
        else str(audit.scdl_level)
    )
    validate_audit_against_pilot_config(
        providers=providers,
        query_count=query_count,
        runs_per_query=audit.runs_per_query,
        scdl_level=scdl_level,
        config=config,
    )

    if audit.status not in {AuditStatus.CREATED, AuditStatus.RUNNING}:
        raise PilotPolicyError("Dry-run can only execute created or running audits.")

    await session.run_sync(
        lambda sync_session: schedule_jobs_for_audit(sync_session, audit_id, commit=False)
    )
    audit.status = AuditStatus.RUNNING
    await session.commit()

    factory = provider_factory or (
        lambda provider_code: build_provider_adapter(
            provider_code,
            pilot_config=config,
        )
    )
    execution_summary = await execute_audit_jobs(
        session,
        audit_id,
        pilot_config=config,
        provider_factory=factory,
    )
    if execution_summary.fatal_error is not None:
        raise PilotPolicyError(execution_summary.fatal_error)

    run_counts = await _run_status_counts(session, audit_id)
    total_jobs = (
        await session.execute(select(func.count()).select_from(Job).where(Job.audit_id == audit_id))
    ).scalar_one()
    executed_jobs = execution_summary.jobs_executed
    success_count = run_counts.get(RunStatus.SUCCESS, 0)
    non_success_count = executed_jobs - success_count

    refreshed_audit = await session.get(Audit, audit_id)
    if refreshed_audit is None:
        raise ValueError(f"Audit id={audit_id} disappeared after job execution.")
    if executed_jobs >= total_jobs and total_jobs > 0:
        refreshed_audit.status = (
            AuditStatus.COMPLETED if non_success_count == 0 else AuditStatus.PARTIAL
        )
    elif non_success_count > 0:
        refreshed_audit.status = AuditStatus.PARTIAL
    else:
        refreshed_audit.status = AuditStatus.RUNNING
    await session.commit()
    await session.refresh(refreshed_audit)

    return DryRunResult(
        audit_id=audit_id,
        provider_mode=config.provider_mode,
        providers=providers,
        scdl_level=scdl_level,
        query_count=query_count,
        runs_per_query=audit.runs_per_query,
        total_jobs=total_jobs,
        executed_jobs=executed_jobs,
        success_count=success_count,
        error_count=run_counts.get(RunStatus.ERROR, 0),
        timeout_count=run_counts.get(RunStatus.TIMEOUT, 0),
        rate_limited_count=run_counts.get(RunStatus.RATE_LIMITED, 0),
        audit_status=refreshed_audit.status.value,
    )


async def _effective_query_count(session: AsyncSession, audit: Audit) -> int:
    query_ids = list(
        (
            await session.execute(
                select(Query.id).where(Query.audit_id == audit.id).order_by(Query.id)
            )
        ).scalars().all()
    )
    if audit.max_queries is not None:
        query_ids = query_ids[: audit.max_queries]
    return len(query_ids)


async def _run_status_counts(session: AsyncSession, audit_id: int) -> dict[RunStatus, int]:
    from libs.storage.models import Run

    rows = (
        await session.execute(
            select(Run.status, func.count()).where(Run.audit_id == audit_id).group_by(Run.status)
        )
    ).all()
    return {status: count for status, count in rows}
