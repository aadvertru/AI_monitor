"""Worker execution flow for scheduled jobs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.storage.models import Job, JobStatus, RawResponse, Run, RunStatus


def _map_provider_status_to_run_status(provider_status: str) -> RunStatus:
    if provider_status == "success":
        return RunStatus.SUCCESS
    if provider_status == "timeout":
        return RunStatus.TIMEOUT
    if provider_status == "rate_limited":
        return RunStatus.RATE_LIMITED
    return RunStatus.ERROR


async def execute_job(session: Session, job_id: int, provider: BaseProviderAdapter) -> Run:
    """Execute a scheduled job, persist Run + RawResponse, and update statuses."""
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job with id={job_id} was not found.")

    query_text = job.query.text
    job.status = JobStatus.RUNNING
    session.flush()

    run_stmt = select(Run).where(
        Run.audit_id == job.audit_id,
        Run.query_id == job.query_id,
        Run.provider == job.provider,
        Run.run_number == job.run_number,
    )
    run = session.execute(run_stmt).scalar_one_or_none()
    if run is None:
        run = Run(
            audit_id=job.audit_id,
            query_id=job.query_id,
            provider=job.provider,
            run_number=job.run_number,
            status=RunStatus.PENDING,
        )
        session.add(run)
        session.flush()

    try:
        response = await provider.query(query_text)
    except Exception as exc:
        response = ProviderResponse(
            status="error",
            raw_answer=None,
            citations=None,
            response_time=None,
            error={"code": "provider_exception", "message": str(exc)},
            provider_metadata={"provider": job.provider},
        )

    run.status = _map_provider_status_to_run_status(response.status)
    job.status = JobStatus.COMPLETED if response.status == "success" else JobStatus.FAILED

    raw_response = run.raw_response
    if raw_response is None:
        raw_response = RawResponse(
            run_id=run.id,
            request_snapshot={
                "query": query_text,
                "provider": job.provider,
                "run_number": job.run_number,
            },
            raw_answer=response.raw_answer,
            citations=response.citations,
            provider_metadata=response.provider_metadata,
            provider_status=response.status,
            response_time=response.response_time,
            error_object=response.error,
        )
        session.add(raw_response)
    else:
        raw_response.raw_answer = response.raw_answer
        raw_response.citations = response.citations
        raw_response.provider_metadata = response.provider_metadata
        raw_response.provider_status = response.status
        raw_response.response_time = response.response_time
        raw_response.error_object = response.error

    session.commit()
    session.refresh(run)
    return run

