"""Worker execution flow for scheduled jobs."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.execution.openrouter_provider import OpenRouterProviderAdapter
from libs.execution.provider_adapter import (
    BaseProviderAdapter,
    ProviderResponse,
    normalize_provider_response,
)
from libs.execution.provider_errors import unknown_provider_error
from libs.execution.safe_logging import (
    duration_ms,
    error_log_fields,
    log_event,
    perf_start,
    provider_log_fields,
)
from libs.storage.models import (
    Audit,
    AuditTarget,
    Job,
    JobStatus,
    Query,
    RawResponse,
    Run,
    RunStatus,
)

logger = logging.getLogger(__name__)


def _map_provider_status_to_run_status(provider_status: str) -> RunStatus:
    if provider_status == "success":
        return RunStatus.SUCCESS
    if provider_status == "timeout":
        return RunStatus.TIMEOUT
    if provider_status == "rate_limited":
        return RunStatus.RATE_LIMITED
    return RunStatus.ERROR


async def execute_job(
    session: AsyncSession,
    job_id: int,
    provider: BaseProviderAdapter,
) -> Run:
    """Execute a scheduled job, persist Run + RawResponse, and update statuses."""
    job_start = perf_start()
    job: Job | None = None
    run: Run | None = None
    scdl_level_value: str | None = None
    audit_id_value: int | None = None
    query_id_value: int | None = None
    provider_value: str | None = None
    try:
        job = await session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job with id={job_id} was not found.")
        audit_id_value = job.audit_id
        query_id_value = job.query_id
        provider_value = job.provider

        query_text = (
            await session.execute(select(Query.text).where(Query.id == job.query_id))
        ).scalar_one_or_none()
        if query_text is None:
            raise ValueError(f"Query with id={job.query_id} was not found.")

        audit_target = await _load_audit_target(session, job)
        scdl_level_value = await _job_scdl_level(session, job, audit_target)

        job.status = JobStatus.RUNNING
        await session.flush()

        run_stmt = select(Run).where(
            Run.audit_id == job.audit_id,
            Run.query_id == job.query_id,
            Run.provider == job.provider,
            Run.run_number == job.run_number,
            Run.audit_target_id == job.audit_target_id,
        )
        run = (await session.execute(run_stmt)).scalar_one_or_none()
        if run is None:
            run = Run(
                audit_id=job.audit_id,
                query_id=job.query_id,
                audit_target_id=job.audit_target_id,
                provider=job.provider,
                run_number=job.run_number,
                status=RunStatus.PENDING,
            )
            session.add(run)
            await session.flush()

        log_event(
            logger,
            "audit_job_started",
            audit_id=job.audit_id,
            run_id=run.id,
            query_id=job.query_id,
            execution_provider=job.provider,
            level=scdl_level_value,
            status=_enum_value(job.status),
        )
        provider_start = perf_start()
        log_event(
            logger,
            "provider_call_started",
            audit_id=job.audit_id,
            run_id=run.id,
            query_id=job.query_id,
            **provider_log_fields(
                job.provider,
                metadata=_adapter_metadata(provider, scdl_level_value, audit_target),
                scdl_level=scdl_level_value,
            ),
        )

        try:
            response = await provider.query(
                query_text,
                scdl_level=scdl_level_value,
                audit_id=job.audit_id,
                query_id=job.query_id,
                run_number=job.run_number,
                provider=job.provider,
                audit_target_id=job.audit_target_id,
                model_id=audit_target.model_id if audit_target is not None else None,
                model_provider=(
                    audit_target.model_provider if audit_target is not None else None
                ),
                execution_provider=(
                    audit_target.execution_provider if audit_target is not None else None
                ),
                gateway=audit_target.gateway if audit_target is not None else None,
                gateway_l2_experimental=(
                    audit_target.gateway_l2_experimental
                    if audit_target is not None
                    else None
                ),
            )
        except Exception:
            response = ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=unknown_provider_error(
                    job.provider,
                    level=scdl_level_value,
                ).to_error_dict(),
                provider_metadata={"provider": job.provider},
            )
        else:
            response = normalize_provider_response(
                response,
                provider=job.provider,
                model=_metadata_model(response.provider_metadata),
                level=scdl_level_value,
            )

        provider_fields = provider_log_fields(
            job.provider,
            metadata=response.provider_metadata,
            scdl_level=scdl_level_value,
            citations=response.citations,
        )
        provider_duration = (
            int(round(response.response_time * 1000))
            if response.response_time is not None
            else duration_ms(provider_start)
        )
        if response.status == "success":
            log_event(
                logger,
                "provider_call_completed",
                audit_id=job.audit_id,
                run_id=run.id,
                query_id=job.query_id,
                status=response.status,
                duration_ms=provider_duration,
                **provider_fields,
            )
        else:
            log_event(
                logger,
                "provider_call_failed",
                audit_id=job.audit_id,
                run_id=run.id,
                query_id=job.query_id,
                status=response.status,
                duration_ms=provider_duration,
                **provider_fields,
                **error_log_fields(response.error),
            )

        run.status = _map_provider_status_to_run_status(response.status)
        job.status = (
            JobStatus.COMPLETED if response.status == "success" else JobStatus.FAILED
        )

        raw_response = (
            await session.execute(select(RawResponse).where(RawResponse.run_id == run.id))
        ).scalar_one_or_none()
        if raw_response is None:
            raw_response = RawResponse(
                run_id=run.id,
                request_snapshot={
                    "query": query_text,
                    "provider": job.provider,
                    "run_number": job.run_number,
                    "audit_target_id": job.audit_target_id,
                    "model_id": audit_target.model_id if audit_target is not None else None,
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

        await session.commit()
        await session.refresh(run)
        log_event(
            logger,
            "audit_job_completed",
            audit_id=job.audit_id,
            run_id=run.id,
            query_id=job.query_id,
            execution_provider=job.provider,
            level=scdl_level_value,
            status=_enum_value(run.status),
            duration_ms=duration_ms(job_start),
        )
        return run
    except Exception as exc:
        await session.rollback()
        log_event(
            logger,
            "audit_job_failed",
            log_level=logging.WARNING,
            audit_id=audit_id_value,
            run_id=run.id if run is not None else None,
            query_id=query_id_value,
            execution_provider=provider_value,
            level=scdl_level_value,
            status="error",
            duration_ms=duration_ms(job_start),
            error_code=exc.__class__.__name__,
        )
        raise


def _metadata_model(provider_metadata: dict | None) -> str | None:
    if provider_metadata is None:
        return None
    model = provider_metadata.get("model")
    return model if isinstance(model, str) else None


async def _load_audit_target(
    session: AsyncSession, job: Job
) -> AuditTarget | None:
    if job.audit_target_id is None:
        return None
    target = await session.get(AuditTarget, job.audit_target_id)
    if target is None:
        raise ValueError(f"Audit target with id={job.audit_target_id} was not found.")
    return target


async def _job_scdl_level(
    session: AsyncSession,
    job: Job,
    audit_target: AuditTarget | None,
) -> str:
    if audit_target is not None:
        return _enum_value(audit_target.level)
    scdl_level = (
        await session.execute(select(Audit.scdl_level).where(Audit.id == job.audit_id))
    ).scalar_one_or_none()
    if scdl_level is None:
        raise ValueError(f"Audit with id={job.audit_id} was not found.")
    return _enum_value(scdl_level)


def _adapter_metadata(
    provider: BaseProviderAdapter,
    scdl_level: str | None,
    audit_target: AuditTarget | None = None,
) -> dict[str, object]:
    if audit_target is not None:
        return {
            "provider": audit_target.execution_provider,
            "execution_provider": audit_target.execution_provider,
            "model_id": audit_target.model_id,
            "model_provider": audit_target.model_provider,
            "gateway": audit_target.gateway,
            "gateway_l2_experimental": audit_target.gateway_l2_experimental,
            "level": scdl_level,
        }
    if isinstance(provider, OpenRouterProviderAdapter):
        config = provider.config
        model_id = _openrouter_model_for_level(config, scdl_level)
        return {
            "provider": "openrouter",
            "execution_provider": "openrouter",
            "model_id": model_id,
            "model_provider": _model_provider(model_id),
            "gateway": True,
            "gateway_l2_experimental": scdl_level == "L2",
            "level": scdl_level,
        }
    return {}


def _openrouter_model_for_level(config: object, scdl_level: str | None) -> str | None:
    if scdl_level == "L2":
        model_id = getattr(config, "model_l2", None)
    else:
        model_id = getattr(config, "model_l1", None)
    return model_id if isinstance(model_id, str) else None


def _model_provider(model_id: str | None) -> str | None:
    if not isinstance(model_id, str) or "/" not in model_id:
        return None
    provider_name = model_id.split("/", 1)[0].strip()
    return provider_name or None


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)
