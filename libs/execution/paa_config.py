"""People Also Ask provider configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

DEFAULT_PAA_ENABLED = False
DEFAULT_PAA_PROVIDER = "mock"
DEFAULT_PAA_MAX_RESULTS = 10
DEFAULT_PAA_REQUEST_TIMEOUT_SECONDS = 15.0
DEFAULT_SERPAPI_DEFAULT_COUNTRY = "us"
DEFAULT_SERPAPI_DEFAULT_LANGUAGE = "en"
SUPPORTED_PAA_PROVIDERS = frozenset({"mock", "serpapi"})


class PaaConfigError(ValueError):
    """Raised when PAA configuration is invalid."""


@dataclass(frozen=True)
class PaaProviderConfig:
    enabled: bool = DEFAULT_PAA_ENABLED
    provider: str = DEFAULT_PAA_PROVIDER
    max_results: int = DEFAULT_PAA_MAX_RESULTS
    request_timeout_seconds: float = DEFAULT_PAA_REQUEST_TIMEOUT_SECONDS
    serpapi_api_key: str | None = field(default=None, repr=False)
    serpapi_default_country: str = DEFAULT_SERPAPI_DEFAULT_COUNTRY
    serpapi_default_language: str = DEFAULT_SERPAPI_DEFAULT_LANGUAGE

    def __repr__(self) -> str:
        key_status = "***" if self.serpapi_api_key else None
        return (
            "PaaProviderConfig("
            f"enabled={self.enabled!r}, "
            f"provider={self.provider!r}, "
            f"max_results={self.max_results!r}, "
            f"request_timeout_seconds={self.request_timeout_seconds!r}, "
            f"serpapi_api_key={key_status!r}, "
            f"serpapi_default_country={self.serpapi_default_country!r}, "
            f"serpapi_default_language={self.serpapi_default_language!r}"
            ")"
        )

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "max_results": self.max_results,
            "request_timeout_seconds": self.request_timeout_seconds,
            "serpapi_api_key": "***" if self.serpapi_api_key else None,
            "serpapi_default_country": self.serpapi_default_country,
            "serpapi_default_language": self.serpapi_default_language,
        }


def load_paa_provider_config(
    env: Mapping[str, str] | None = None,
) -> PaaProviderConfig:
    source = os.environ if env is None else env
    provider = _load_required_text(source, "PAA_PROVIDER", DEFAULT_PAA_PROVIDER).lower()
    if provider not in SUPPORTED_PAA_PROVIDERS:
        raise PaaConfigError("PAA_PROVIDER is not supported.")
    return PaaProviderConfig(
        enabled=_load_bool(source, "PAA_ENABLED", DEFAULT_PAA_ENABLED),
        provider=provider,
        max_results=_load_positive_int(source, "PAA_MAX_RESULTS", DEFAULT_PAA_MAX_RESULTS),
        request_timeout_seconds=_load_positive_float(
            source,
            "PAA_REQUEST_TIMEOUT_SECONDS",
            DEFAULT_PAA_REQUEST_TIMEOUT_SECONDS,
        ),
        serpapi_api_key=_load_optional_text(source, "SERPAPI_API_KEY"),
        serpapi_default_country=_load_required_text(
            source,
            "SERPAPI_DEFAULT_COUNTRY",
            DEFAULT_SERPAPI_DEFAULT_COUNTRY,
        ).lower(),
        serpapi_default_language=_load_required_text(
            source,
            "SERPAPI_DEFAULT_LANGUAGE",
            DEFAULT_SERPAPI_DEFAULT_LANGUAGE,
        ).lower(),
    )


def _load_optional_text(source: Mapping[str, str], key: str) -> str | None:
    raw_value = source.get(key)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _load_required_text(source: Mapping[str, str], key: str, default: str) -> str:
    return _load_optional_text(source, key) or default


def _load_bool(source: Mapping[str, str], key: str, default: bool) -> bool:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise PaaConfigError(f"{key} must be a boolean value.")


def _load_positive_int(source: Mapping[str, str], key: str, default: int) -> int:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        raise PaaConfigError(f"{key} must be a positive integer.") from exc
    if value <= 0:
        raise PaaConfigError(f"{key} must be a positive integer.")
    return value


def _load_positive_float(source: Mapping[str, str], key: str, default: float) -> float:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = float(raw_value.strip())
    except ValueError as exc:
        raise PaaConfigError(f"{key} must be a positive number.") from exc
    if value <= 0:
        raise PaaConfigError(f"{key} must be a positive number.")
    return value
