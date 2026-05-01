"""Full audit pipeline orchestration service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.control.job_scheduler import schedule_jobs_for_audit
from libs.execution.audit_execution import (
    AuditJobExecutionSummary,
    ProviderFactory,
    execute_audit_jobs,
)
from libs.execution.audit_status import AuditFinalStatusInputs, derive_final_audit_status
from libs.execution.pilot_config import RealProviderPilotConfig
from libs.execution.post_processing import (
    AuditPostProcessingSummary,
    process_audit_results,
)
from libs.storage.models import (
    Audit,
    AuditStatus,
    Job,
    ParsedResult,
    Query,
    Run,
    RunStatus,
    Score,
)

PostProcessingService = Callable[[AsyncSession, int], object]


@dataclass(frozen=True)
class AuditSchedulingSummary:
    audit_id: int
    scheduled_jobs: int = 0
    total_jobs: int = 0
    fatal_error: str | None = None

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "scheduled_jobs": self.scheduled_jobs,
            "total_jobs": self.total_jobs,
            "fatal_error": self.fatal_error,
        }


@dataclass(frozen=True)
class AuditPipelineSummary:
    audit_id: int
    scheduling: AuditSchedulingSummary
    execution: AuditJobExecutionSummary | None = None
    post_processing: AuditPostProcessingSummary | None = None
    final_audit_status: str | None = None
    fatal_error: str | None = None

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "scheduling": self.scheduling.safe_log_dict(),
            "execution": (
                self.execution.safe_log_dict() if self.execution is not None else None
            ),
            "post_processing": (
                self.post_processing.safe_log_dict()
                if self.post_processing is not None
                else None
            ),
            "final_audit_status": self.final_audit_status,
            "fatal_error": self.fatal_error,
        }


async def run_audit_pipeline(
    session: AsyncSession,
    audit_id: int,
    *,
    pilot_config: RealProviderPilotConfig | None = None,
    provider_factory: ProviderFactory | None = None,
) -> AuditPipelineSummary:
    """Run schedule -> execute -> post-process for one audit."""
    scheduling = AuditSchedulingSummary(audit_id=audit_id)
    audit = await session.get(Audit, audit_id)
    if audit is None:
        return AuditPipelineSummary(
            audit_id=audit_id,
            scheduling=scheduling,
            final_audit_status=AuditStatus.FAILED.value,
            fatal_error=f"Audit with id={audit_id} was not found.",
        )

    try:
        audit.status = AuditStatus.RUNNING
        scheduled_jobs = await session.run_sync(
            lambda sync_session: len(
                schedule_jobs_for_audit(sync_session, audit_id, commit=False)
            )
        )
        await session.commit()
        scheduling = AuditSchedulingSummary(
            audit_id=audit_id,
            scheduled_jobs=scheduled_jobs,
            total_jobs=await _job_count(session, audit_id),
        )
    except Exception as exc:
        await session.rollback()
        final_status = await _set_audit_status(session, audit_id, AuditStatus.FAILED)
        fatal_error = f"Audit scheduling failed: {exc.__class__.__name__}."
        return AuditPipelineSummary(
            audit_id=audit_id,
            scheduling=AuditSchedulingSummary(
                audit_id=audit_id,
                fatal_error=fatal_error,
            ),
            final_audit_status=final_status,
            fatal_error=fatal_error,
        )

    execution = await execute_audit_jobs(
        session,
        audit_id,
        pilot_config=pilot_config,
        provider_factory=provider_factory,
    )
    if execution.fatal_error is not None:
        final_status = await _set_audit_status(session, audit_id, AuditStatus.FAILED)
        return AuditPipelineSummary(
            audit_id=audit_id,
            scheduling=scheduling,
            execution=execution,
            final_audit_status=final_status,
            fatal_error=execution.fatal_error,
        )

    post_processing = await process_audit_results(session, audit_id)
    if post_processing.fatal_error is not None:
        final_status = await _set_audit_status(session, audit_id, AuditStatus.FAILED)
        return AuditPipelineSummary(
            audit_id=audit_id,
            scheduling=scheduling,
            execution=execution,
            post_processing=post_processing,
            final_audit_status=final_status,
            fatal_error=post_processing.fatal_error,
        )

    final_status = await _derive_and_persist_final_status(
        session=session,
        audit_id=audit_id,
        execution=execution,
        post_processing=post_processing,
    )
    return AuditPipelineSummary(
        audit_id=audit_id,
        scheduling=scheduling,
        execution=execution,
        post_processing=post_processing,
        final_audit_status=final_status,
    )


async def _derive_and_persist_final_status(
    *,
    session: AsyncSession,
    audit_id: int,
    execution: AuditJobExecutionSummary,
    post_processing: AuditPostProcessingSummary,
) -> str:
    audit = await session.get(Audit, audit_id)
    if audit is None:
        return AuditStatus.FAILED.value

    expected_runs = await _expected_run_count(session, audit)
    terminal_runs = await _terminal_run_count(session, audit_id)
    usable_scores = await _usable_score_count(session, audit_id)
    terminal_failures = (
        execution.error_count + execution.timeout_count + execution.rate_limited_count
    )
    audit.status = derive_final_audit_status(
        AuditFinalStatusInputs(
            expected_runs=expected_runs,
            terminal_runs=terminal_runs,
            usable_score_count=usable_scores,
            terminal_failure_count=terminal_failures,
            execution_error_count=len(execution.errors),
            processing_error_count=len(post_processing.errors),
            missing_raw_count=post_processing.skipped_missing_raw_response,
        )
    )

    await session.commit()
    await session.refresh(audit)
    return _status_value(audit.status)


async def _set_audit_status(
    session: AsyncSession,
    audit_id: int,
    status: AuditStatus,
) -> str:
    audit = await session.get(Audit, audit_id)
    if audit is None:
        return status.value
    audit.status = status
    await session.commit()
    await session.refresh(audit)
    return _status_value(audit.status)


async def _job_count(session: AsyncSession, audit_id: int) -> int:
    return (
        await session.execute(select(func.count()).select_from(Job).where(Job.audit_id == audit_id))
    ).scalar_one()


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


async def _terminal_run_count(session: AsyncSession, audit_id: int) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .where(
                Run.audit_id == audit_id,
                Run.status.in_(
                    {
                        RunStatus.SUCCESS,
                        RunStatus.ERROR,
                        RunStatus.TIMEOUT,
                        RunStatus.RATE_LIMITED,
                    }
                ),
            )
        )
    ).scalar_one()


async def _usable_score_count(session: AsyncSession, audit_id: int) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(Run)
            .join(ParsedResult, ParsedResult.run_id == Run.id)
            .join(Score, Score.run_id == Run.id)
            .where(Run.audit_id == audit_id, Run.status == RunStatus.SUCCESS)
        )
    ).scalar_one()


def _status_value(status: object) -> str:
    return status.value if hasattr(status, "value") else str(status)
