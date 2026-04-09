"""RawResponse storage helpers with write-once behavior."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from libs.execution.provider_adapter import ProviderResponse
from libs.storage.models import RawResponse, Run


class RawResponseAlreadyExistsError(RuntimeError):
    """Raised when attempting to overwrite an existing RawResponse."""


def store_raw_response_for_run(
    session: Session,
    *,
    run_id: int,
    provider_response: ProviderResponse,
    request_snapshot: dict[str, Any] | None,
) -> RawResponse:
    """Persist RawResponse for a run exactly once (immutable after write)."""
    run = session.get(Run, run_id)
    if run is None:
        raise ValueError(f"Run with id={run_id} was not found.")

    if run.raw_response is not None:
        raise RawResponseAlreadyExistsError(
            f"RawResponse already exists for run_id={run_id}; overwrite is not allowed."
        )

    snapshot = dict(request_snapshot) if isinstance(request_snapshot, dict) else None
    raw_response = RawResponse(
        run_id=run_id,
        request_snapshot=snapshot,
        raw_answer=provider_response.raw_answer,
        citations=provider_response.citations,
        provider_metadata=provider_response.provider_metadata,
        provider_status=provider_response.status,
        response_time=provider_response.response_time,
        error_object=provider_response.error,
    )
    session.add(raw_response)
    session.flush()
    return raw_response

