"""Reusable audit job execution service."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.execution.pilot_config import (
    PilotConfigError,
    PilotPolicyError,
    RealProviderPilotConfig,
    load_real_provider_pilot_config,
    validate_audit_against_pilot_config,
)
from libs.execution.provider_adapter import BaseProviderAdapter
from libs.execution.provider_factory import build_provider_adapter
from libs.execution.safe_logging import duration_ms, log_event, perf_start
from libs.execution.worker import execute_job
from libs.storage.models import Audit, Job, JobStatus, Query, Run, RunStatus

ProviderFactory = Callable[[str], BaseProviderAdapter]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobExecutionError:
    job_id: int
    code: str
    message: str

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class AuditJobExecutionSummary:
    audit_id: int
    total_jobs_inspected: int = 0
    jobs_executed: int = 0
    jobs_skipped: int = 0
    success_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    rate_limited_count: int = 0
    errors: list[JobExecutionError] = field(default_factory=list)
    fatal_error: str | None = None

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "total_jobs_inspected": self.total_jobs_inspected,
            "jobs_executed": self.jobs_executed,
            "jobs_skipped": self.jobs_skipped,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "rate_limited_count": self.rate_limited_count,
            "errors": [error.safe_log_dict() for error in self.errors],
            "fatal_error": self.fatal_error,
        }


async def execute_audit_jobs(
    session: AsyncSession,
    audit_id: int,
    *,
    pilot_config: RealProviderPilotConfig | None = None,
    provider_factory: ProviderFactory | None = None,
) -> AuditJobExecutionSummary:
    """Execute pending jobs for a single audit and return safe counts."""
    config = pilot_config or load_real_provider_pilot_config()
    audit = await session.get(Audit, audit_id)
    if audit is None:
        return AuditJobExecutionSummary(
            audit_id=audit_id,
            fatal_error=f"Audit with id={audit_id} was not found.",
        )

    try:
        await _validate_audit_policy(session=session, audit=audit, config=config)
    except (PilotConfigError, PilotPolicyError) as exc:
        return AuditJobExecutionSummary(audit_id=audit_id, fatal_error=str(exc))

    factory = provider_factory or (
        lambda provider_code: build_provider_adapter(
            provider_code,
            pilot_config=config,
        )
    )
    jobs = list(
        (
            await session.execute(
                select(Job).where(Job.audit_id == audit_id).order_by(Job.id)
            )
        ).scalars().all()
    )

    jobs_executed = 0
    jobs_skipped = 0
    errors: list[JobExecutionError] = []
    for job in jobs:
        if job.status != JobStatus.PENDING:
            jobs_skipped += 1
            continue

        job_start = perf_start()
        try:
            adapter = factory(job.provider)
            await execute_job(session, job.id, adapter)
            jobs_executed += 1
        except Exception as exc:
            log_event(
                logger,
                "audit_job_execution_error",
                log_level=logging.WARNING,
                audit_id=audit_id,
                query_id=job.query_id,
                execution_provider=job.provider,
                status="error",
                duration_ms=duration_ms(job_start),
                error_code="job_execution_error",
            )
            errors.append(
                JobExecutionError(
                    job_id=job.id,
                    code="job_execution_error",
                    message=f"Job execution failed: {exc.__class__.__name__}.",
                )
            )

    run_counts = await _run_status_counts(session, audit_id)
    return AuditJobExecutionSummary(
        audit_id=audit_id,
        total_jobs_inspected=len(jobs),
        jobs_executed=jobs_executed,
        jobs_skipped=jobs_skipped,
        success_count=run_counts.get(RunStatus.SUCCESS, 0),
        error_count=run_counts.get(RunStatus.ERROR, 0),
        timeout_count=run_counts.get(RunStatus.TIMEOUT, 0),
        rate_limited_count=run_counts.get(RunStatus.RATE_LIMITED, 0),
        errors=errors,
    )


async def _validate_audit_policy(
    *,
    session: AsyncSession,
    audit: Audit,
    config: RealProviderPilotConfig,
) -> None:
    providers = [provider.strip().lower() for provider in audit.providers or []]
    scdl_level = audit.scdl_level.value if hasattr(audit.scdl_level, "value") else str(
        audit.scdl_level
    )
    validate_audit_against_pilot_config(
        providers=providers,
        query_count=await _effective_query_count(session, audit),
        runs_per_query=audit.runs_per_query,
        scdl_level=scdl_level,
        config=config,
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
    rows = (
        await session.execute(
            select(Run.status, func.count()).where(Run.audit_id == audit_id).group_by(Run.status)
        )
    ).all()
    return {status: count for status, count in rows}
