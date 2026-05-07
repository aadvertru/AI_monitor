"""DB-backed background job state helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.storage.models import BackgroundJob, BackgroundJobStatus

SENSITIVE_METADATA_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "headers",
    "jwt",
    "password",
    "prompt",
    "raw_answer",
    "raw_response",
    "request_snapshot",
    "secret",
    "token",
)


async def enqueue_background_job(
    session: AsyncSession,
    *,
    job_type: str,
    audit_id: int | None,
    user_id: int | None,
    progress_metadata: dict[str, Any] | None = None,
) -> BackgroundJob:
    job = BackgroundJob(
        job_type=_safe_code(job_type),
        audit_id=audit_id,
        user_id=user_id,
        status=BackgroundJobStatus.QUEUED,
        progress_metadata=safe_progress_metadata(progress_metadata),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def fetch_next_queued_job(
    session: AsyncSession,
    *,
    job_type: str | None = None,
) -> BackgroundJob | None:
    statement = select(BackgroundJob).where(
        BackgroundJob.status == BackgroundJobStatus.QUEUED
    )
    if job_type is not None:
        statement = statement.where(BackgroundJob.job_type == _safe_code(job_type))
    statement = statement.order_by(BackgroundJob.id).limit(1)
    return (await session.execute(statement)).scalar_one_or_none()


async def find_active_background_job(
    session: AsyncSession,
    *,
    audit_id: int,
    job_type: str,
) -> BackgroundJob | None:
    statement = (
        select(BackgroundJob)
        .where(
            BackgroundJob.audit_id == audit_id,
            BackgroundJob.job_type == _safe_code(job_type),
            BackgroundJob.status.in_(
                {
                    BackgroundJobStatus.QUEUED,
                    BackgroundJobStatus.RUNNING,
                    BackgroundJobStatus.CANCEL_REQUESTED,
                }
            ),
        )
        .order_by(BackgroundJob.id)
        .limit(1)
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def mark_background_job_running(
    session: AsyncSession,
    job_id: int,
    *,
    progress_metadata: dict[str, Any] | None = None,
) -> BackgroundJob:
    job = await _load_job(session, job_id)
    job.status = BackgroundJobStatus.RUNNING
    job.started_at = _utc_now()
    _merge_progress_metadata(job, progress_metadata)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_background_job_completed(
    session: AsyncSession,
    job_id: int,
    *,
    progress_metadata: dict[str, Any] | None = None,
) -> BackgroundJob:
    job = await _load_job(session, job_id)
    job.status = BackgroundJobStatus.COMPLETED
    job.finished_at = _utc_now()
    _merge_progress_metadata(job, progress_metadata)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_background_job_failed(
    session: AsyncSession,
    job_id: int,
    *,
    error_code: str,
    error_message: str | None = None,
    progress_metadata: dict[str, Any] | None = None,
) -> BackgroundJob:
    job = await _load_job(session, job_id)
    job.status = BackgroundJobStatus.FAILED
    job.finished_at = _utc_now()
    job.error_code = _safe_code(error_code)
    job.error_message_safe = _safe_error_message(error_message)
    _merge_progress_metadata(job, progress_metadata)
    await session.commit()
    await session.refresh(job)
    return job


async def request_background_job_cancel(
    session: AsyncSession,
    job_id: int,
    *,
    progress_metadata: dict[str, Any] | None = None,
) -> BackgroundJob:
    job = await _load_job(session, job_id)
    job.status = BackgroundJobStatus.CANCEL_REQUESTED
    job.cancel_requested_at = _utc_now()
    _merge_progress_metadata(job, progress_metadata)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_background_job_cancelled(
    session: AsyncSession,
    job_id: int,
    *,
    progress_metadata: dict[str, Any] | None = None,
) -> BackgroundJob:
    job = await _load_job(session, job_id)
    job.status = BackgroundJobStatus.CANCELLED
    job.finished_at = _utc_now()
    _merge_progress_metadata(job, progress_metadata)
    await session.commit()
    await session.refresh(job)
    return job


def safe_progress_metadata(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for key, item in value.items():
        safe_key = _safe_metadata_key(key)
        if safe_key is None:
            continue
        safe_value = _safe_json_value(item)
        if safe_value is not None:
            result[safe_key] = safe_value
    return result


async def _load_job(session: AsyncSession, job_id: int) -> BackgroundJob:
    job = await session.get(BackgroundJob, job_id)
    if job is None:
        raise ValueError("background job was not found")
    return job


def _merge_progress_metadata(
    job: BackgroundJob,
    progress_metadata: dict[str, Any] | None,
) -> None:
    safe_metadata = safe_progress_metadata(progress_metadata)
    if safe_metadata:
        job.progress_metadata = {**(job.progress_metadata or {}), **safe_metadata}


def _safe_metadata_key(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    lowered = normalized.lower()
    if any(marker in lowered for marker in SENSITIVE_METADATA_MARKERS):
        return None
    return normalized


def _safe_json_value(value: Any) -> Any:
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, list):
        safe_items = [_safe_json_value(item) for item in value]
        return [item for item in safe_items if item is not None]
    if isinstance(value, dict):
        return safe_progress_metadata(value)
    return None


def _safe_code(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("background job code must not be empty")
    return normalized[:64]


def _safe_error_message(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_METADATA_MARKERS) or "sk-" in lowered:
        return "Background job failed."
    return value.strip()[:500] or None


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)
