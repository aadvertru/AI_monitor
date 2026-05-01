"""Real-provider pilot safety policy.

The OpenAI pilot is intentionally opt-in. Defaults keep local development and
automated tests on mock execution only.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

ProviderMode = Literal["mock", "openai"]

DEFAULT_PROVIDER_MODE: ProviderMode = "mock"
DEFAULT_REAL_PROVIDER_ENABLED = False
DEFAULT_REAL_PROVIDER_MAX_PROVIDERS = 1
DEFAULT_REAL_PROVIDER_MAX_QUERIES = 5
DEFAULT_REAL_PROVIDER_MAX_RUNS_PER_QUERY = 1
DEFAULT_REAL_PROVIDER_MAX_TOTAL_RUNS = 5
OPENAI_PILOT_API_FAMILY = "responses_api"

MOCK_PROVIDER = "mock"
OPENAI_PROVIDER = "openai"
ALLOWED_PROVIDER_MODES = frozenset({MOCK_PROVIDER, OPENAI_PROVIDER})


class PilotConfigError(ValueError):
    """Raised when real-provider pilot configuration is invalid."""


class PilotPolicyError(ValueError):
    """Raised when an audit violates real-provider pilot policy."""


@dataclass(frozen=True)
class RealProviderPilotConfig:
    real_provider_enabled: bool = DEFAULT_REAL_PROVIDER_ENABLED
    provider_mode: ProviderMode = DEFAULT_PROVIDER_MODE
    max_providers: int = DEFAULT_REAL_PROVIDER_MAX_PROVIDERS
    max_queries: int = DEFAULT_REAL_PROVIDER_MAX_QUERIES
    max_runs_per_query: int = DEFAULT_REAL_PROVIDER_MAX_RUNS_PER_QUERY
    max_total_runs: int = DEFAULT_REAL_PROVIDER_MAX_TOTAL_RUNS
    openai_api_family: str = OPENAI_PILOT_API_FAMILY


def load_real_provider_pilot_config(
    env: Mapping[str, str] | None = None,
) -> RealProviderPilotConfig:
    source = os.environ if env is None else env
    provider_mode = _load_provider_mode(source)
    return RealProviderPilotConfig(
        real_provider_enabled=_load_bool(
            source,
            "REAL_PROVIDER_ENABLED",
            DEFAULT_REAL_PROVIDER_ENABLED,
        ),
        provider_mode=provider_mode,
        max_providers=_load_positive_int(
            source,
            "REAL_PROVIDER_MAX_PROVIDERS",
            DEFAULT_REAL_PROVIDER_MAX_PROVIDERS,
        ),
        max_queries=_load_positive_int(
            source,
            "REAL_PROVIDER_MAX_QUERIES",
            DEFAULT_REAL_PROVIDER_MAX_QUERIES,
        ),
        max_runs_per_query=_load_positive_int(
            source,
            "REAL_PROVIDER_MAX_RUNS_PER_QUERY",
            DEFAULT_REAL_PROVIDER_MAX_RUNS_PER_QUERY,
        ),
        max_total_runs=_load_positive_int(
            source,
            "REAL_PROVIDER_MAX_TOTAL_RUNS",
            DEFAULT_REAL_PROVIDER_MAX_TOTAL_RUNS,
        ),
    )


def validate_audit_against_pilot_config(
    *,
    providers: list[str],
    query_count: int,
    runs_per_query: int,
    scdl_level: str,
    config: RealProviderPilotConfig | None = None,
) -> None:
    """Validate an audit before scheduling or adapter selection.

    SCDL policy for the OpenAI pilot:
    - L1 is a no-web OpenAI answer.
    - L2 may use OpenAI web search when TASK-130 implements that adapter path.
    """
    resolved_config = config or load_real_provider_pilot_config()
    normalized_providers = [provider.strip().lower() for provider in providers]

    if not normalized_providers:
        raise PilotPolicyError("Audit must include at least one provider.")

    unsupported = sorted(
        {provider for provider in normalized_providers if provider not in ALLOWED_PROVIDER_MODES}
    )
    if unsupported:
        raise PilotPolicyError(
            f"Unsupported real-provider pilot providers: {', '.join(unsupported)}."
        )

    if resolved_config.provider_mode == MOCK_PROVIDER:
        if any(provider != MOCK_PROVIDER for provider in normalized_providers):
            raise PilotPolicyError(
                "Provider mode 'mock' allows mock execution only."
            )
        return

    if any(provider != OPENAI_PROVIDER for provider in normalized_providers):
        raise PilotPolicyError(
            "Provider mode 'openai' allows OpenAI execution only; mixed provider lists "
            "are rejected during the pilot."
        )

    if not resolved_config.real_provider_enabled:
        raise PilotPolicyError(
            "Real provider execution is disabled. Set REAL_PROVIDER_ENABLED=true "
            "to run the OpenAI pilot."
        )

    if scdl_level not in {"L1", "L2"}:
        raise PilotPolicyError("SCDL level must be L1 or L2 for the OpenAI pilot.")

    provider_count = len(set(normalized_providers))
    if provider_count > resolved_config.max_providers:
        raise PilotPolicyError("Real-provider audit exceeds max providers cap.")
    if query_count > resolved_config.max_queries:
        raise PilotPolicyError("Real-provider audit exceeds max queries cap.")
    if runs_per_query > resolved_config.max_runs_per_query:
        raise PilotPolicyError("Real-provider audit exceeds max runs per query cap.")

    total_runs = query_count * provider_count * runs_per_query
    if total_runs > resolved_config.max_total_runs:
        raise PilotPolicyError("Real-provider audit exceeds max total runs cap.")


def _load_provider_mode(source: Mapping[str, str]) -> ProviderMode:
    raw_value = source.get("PROVIDER_MODE", DEFAULT_PROVIDER_MODE)
    value = raw_value.strip().lower()
    if value not in ALLOWED_PROVIDER_MODES:
        raise PilotConfigError(
            "PROVIDER_MODE must be 'mock' or 'openai' for the real-provider pilot."
        )
    return value  # type: ignore[return-value]


def _load_bool(
    source: Mapping[str, str],
    key: str,
    default: bool,
) -> bool:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise PilotConfigError(f"{key} must be a boolean value.")


def _load_positive_int(
    source: Mapping[str, str],
    key: str,
    default: int,
) -> int:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        raise PilotConfigError(f"{key} must be a positive integer.") from exc
    if value <= 0:
        raise PilotConfigError(f"{key} must be a positive integer.")
    return value
