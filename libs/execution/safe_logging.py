"""Safe structured logging helpers for execution flows."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

SAFE_LOG_FIELDS = frozenset(
    {
        "event",
        "audit_id",
        "run_id",
        "query_id",
        "user_id",
        "execution_provider",
        "model_id",
        "model_provider",
        "level",
        "gateway",
        "gateway_l2_experimental",
        "status",
        "duration_ms",
        "error_code",
        "retryable",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cached_tokens",
        "reasoning_tokens",
        "web_search_requests",
        "source_count",
        "from_status",
        "to_status",
        "reason",
        "scheduled_jobs",
        "total_jobs",
        "jobs_executed",
        "jobs_skipped",
        "runs_processed",
        "raw_response_id",
        "parsed_result_id",
        "score_id",
        "exception_type",
    }
)

USAGE_KEYS = frozenset(
    {
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cached_tokens",
        "reasoning_tokens",
        "web_search_requests",
    }
)


def perf_start() -> float:
    return time.perf_counter()


def duration_ms(start: float) -> int:
    return int(round((time.perf_counter() - start) * 1000))


def log_event(
    logger: logging.Logger,
    event: str,
    /,
    *,
    log_level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Log one structured event with an allowlisted safe field set."""
    extra = {"event": event}
    for key, value in fields.items():
        if key not in SAFE_LOG_FIELDS or value is None:
            continue
        safe_value = _safe_scalar(value)
        if safe_value is not None:
            extra[key] = safe_value

    logger.log(log_level, event, extra=extra)


def provider_log_fields(
    provider_code: str,
    *,
    metadata: Mapping[str, Any] | None = None,
    scdl_level: str | None = None,
    citations: list[dict] | None = None,
) -> dict[str, Any]:
    metadata = metadata or {}
    execution_provider = _str_or_none(
        metadata.get("execution_provider") or metadata.get("provider") or provider_code
    )
    model_id = _str_or_none(metadata.get("model_id") or metadata.get("model"))
    model_provider = _str_or_none(metadata.get("model_provider") or execution_provider)
    level = _str_or_none(metadata.get("level") or scdl_level)
    gateway = bool(metadata.get("gateway")) if "gateway" in metadata else False
    gateway_l2_experimental = (
        bool(metadata.get("gateway_l2_experimental"))
        if "gateway_l2_experimental" in metadata
        else False
    )

    fields: dict[str, Any] = {
        "execution_provider": execution_provider,
        "model_id": model_id,
        "model_provider": model_provider,
        "level": level,
        "gateway": gateway,
        "gateway_l2_experimental": gateway_l2_experimental,
        "source_count": len(citations or []),
    }
    fields.update(usage_log_fields(metadata))
    return fields


def error_log_fields(error: Mapping[str, Any] | None) -> dict[str, Any]:
    if not error:
        return {}
    return {
        "error_code": _str_or_none(error.get("code")),
        "retryable": bool(error.get("retryable")) if "retryable" in error else None,
    }


def usage_log_fields(metadata: Mapping[str, Any] | None) -> dict[str, int]:
    if not metadata:
        return {}
    usage = metadata.get("usage")
    if not isinstance(usage, Mapping):
        return {}

    result: dict[str, int] = {}
    for key in USAGE_KEYS:
        value = usage.get(key)
        if isinstance(value, int | float):
            result[key] = int(value)
    return result


def _safe_scalar(value: Any) -> str | int | float | bool | None:
    if hasattr(value, "value"):
        value = value.value
    if isinstance(value, str | int | float | bool):
        return value
    return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        value = value.value
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None
