"""Background execution hook for audit pipeline jobs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from libs.control.background_jobs import (
    mark_background_job_completed,
    mark_background_job_failed,
    mark_background_job_running,
)
from libs.execution.pipeline import AuditPipelineSummary, run_audit_pipeline
from libs.storage.models import BackgroundJob

AUDIT_PIPELINE_JOB_TYPE = "audit_pipeline"

PipelineRunner = Callable[[AsyncSession, int], Awaitable[AuditPipelineSummary]]


async def execute_audit_pipeline_background_job(
    session: AsyncSession,
    background_job_id: int,
    *,
    pipeline_runner: PipelineRunner = run_audit_pipeline,
) -> BackgroundJob:
    job = await mark_background_job_running(
        session,
        background_job_id,
        progress_metadata={"stage": "running"},
    )
    if job.audit_id is None:
        return await mark_background_job_failed(
            session,
            background_job_id,
            error_code="missing_audit_id",
            error_message="Background audit pipeline job is missing audit_id.",
        )

    try:
        summary = await pipeline_runner(session, job.audit_id)
    except Exception as exc:
        return await mark_background_job_failed(
            session,
            background_job_id,
            error_code="audit_pipeline_exception",
            error_message=f"Audit pipeline failed: {exc.__class__.__name__}.",
        )

    progress_metadata = {
        "stage": "finished",
        "final_audit_status": summary.final_audit_status,
    }
    if summary.fatal_error is not None:
        return await mark_background_job_failed(
            session,
            background_job_id,
            error_code="audit_pipeline_failed",
            error_message=summary.fatal_error,
            progress_metadata=progress_metadata,
        )

    return await mark_background_job_completed(
        session,
        background_job_id,
        progress_metadata=progress_metadata,
    )
