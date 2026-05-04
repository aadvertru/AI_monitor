"""Normalized provider error model and helpers."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderErrorCode(str, Enum):
    PROVIDER_DISABLED = "PROVIDER_DISABLED"
    NO_API_KEY = "NO_API_KEY"
    INVALID_API_KEY = "INVALID_API_KEY"
    INVALID_MODEL = "INVALID_MODEL"
    UNSUPPORTED_L2 = "UNSUPPORTED_L2"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_REQUEST_FAILED = "PROVIDER_REQUEST_FAILED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN_PROVIDER_ERROR = "UNKNOWN_PROVIDER_ERROR"


class NormalizedProviderError(BaseModel):
    code: ProviderErrorCode
    message: str
    provider: str
    model: str | None = None
    level: Literal["L1", "L2"] | None = None
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)

    def to_error_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def provider_disabled_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.PROVIDER_DISABLED,
        "Provider execution is disabled.",
        provider,
        model,
        level,
    )


def no_api_key_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.NO_API_KEY,
        f"{provider_label(provider)} API key is not configured.",
        provider,
        model,
        level,
    )


def invalid_api_key_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.INVALID_API_KEY,
        f"{provider_label(provider)} API key is invalid.",
        provider,
        model,
        level,
    )


def invalid_model_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.INVALID_MODEL,
        f"{provider_label(provider)} model configuration is invalid.",
        provider,
        model,
        level,
    )


def unsupported_l2_error(
    provider: str,
    model: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.UNSUPPORTED_L2,
        f"{provider_label(provider)} does not support SCDL L2 for this run.",
        provider,
        model,
        "L2",
    )


def timeout_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.TIMEOUT,
        f"{provider_label(provider)} request timed out.",
        provider,
        model,
        level,
        retryable=True,
    )


def rate_limit_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.RATE_LIMIT,
        f"{provider_label(provider)} rate limit exceeded.",
        provider,
        model,
        level,
        retryable=True,
    )


def empty_response_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.EMPTY_RESPONSE,
        f"{provider_label(provider)} returned an empty response.",
        provider,
        model,
        level,
    )


def invalid_response_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.INVALID_RESPONSE,
        f"{provider_label(provider)} returned an invalid response.",
        provider,
        model,
        level,
    )


def provider_request_failed_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.PROVIDER_REQUEST_FAILED,
        f"{provider_label(provider)} request failed.",
        provider,
        model,
        level,
        retryable=True,
    )


def configuration_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.CONFIGURATION_ERROR,
        f"{provider_label(provider)} provider configuration is invalid.",
        provider,
        model,
        level,
    )


def unknown_provider_error(
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> NormalizedProviderError:
    return _error(
        ProviderErrorCode.UNKNOWN_PROVIDER_ERROR,
        f"{provider_label(provider)} provider failed unexpectedly.",
        provider,
        model,
        level,
    )


def normalize_provider_error_dict(
    error: dict[str, Any] | None,
    *,
    provider: str,
    model: str | None = None,
    level: str | None = None,
    fallback_code: ProviderErrorCode = ProviderErrorCode.PROVIDER_REQUEST_FAILED,
) -> dict[str, Any]:
    if error is None:
        return provider_request_failed_error(provider, model, level).to_error_dict()

    raw_code = str(error.get("code", "")).strip()
    mapped_code = _map_error_code(raw_code) or fallback_code
    return _error_for_code(mapped_code, provider=provider, model=model, level=level).to_error_dict()


def provider_label(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "OpenAI"
    if normalized == "mock":
        return "Mock provider"
    if normalized == "anthropic":
        return "Anthropic"
    if normalized == "openrouter":
        return "OpenRouter"
    return provider.strip() or "Provider"


def _error(
    code: ProviderErrorCode,
    message: str,
    provider: str,
    model: str | None,
    level: str | None,
    *,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> NormalizedProviderError:
    normalized_level: Literal["L1", "L2"] | None = level if level in {"L1", "L2"} else None
    return NormalizedProviderError(
        code=code,
        message=message,
        provider=provider.strip().lower() or "unknown",
        model=model,
        level=normalized_level,
        retryable=retryable,
        details=details or {},
    )


def _map_error_code(raw_code: str) -> ProviderErrorCode | None:
    normalized = raw_code.strip().upper()
    if not normalized:
        return None
    if normalized in ProviderErrorCode.__members__:
        return ProviderErrorCode[normalized]

    legacy_map = {
        "MISSING_API_KEY": ProviderErrorCode.NO_API_KEY,
        "NO_API_KEY": ProviderErrorCode.NO_API_KEY,
        "UNSUPPORTED_SCDL_LEVEL": ProviderErrorCode.UNSUPPORTED_L2,
        "TIMEOUT": ProviderErrorCode.TIMEOUT,
        "RATE_LIMITED": ProviderErrorCode.RATE_LIMIT,
        "RATE_LIMIT": ProviderErrorCode.RATE_LIMIT,
        "SDK_NOT_INSTALLED": ProviderErrorCode.CONFIGURATION_ERROR,
        "MOCK_INVALID_MODE": ProviderErrorCode.CONFIGURATION_ERROR,
        "MOCK_INTERNAL_ERROR": ProviderErrorCode.UNKNOWN_PROVIDER_ERROR,
        "PROVIDER_EXCEPTION": ProviderErrorCode.UNKNOWN_PROVIDER_ERROR,
        "PROVIDER_ERROR": ProviderErrorCode.PROVIDER_REQUEST_FAILED,
        "MOCK_ERROR": ProviderErrorCode.PROVIDER_REQUEST_FAILED,
    }
    return legacy_map.get(normalized)


def _error_for_code(
    code: ProviderErrorCode,
    *,
    provider: str,
    model: str | None,
    level: str | None,
) -> NormalizedProviderError:
    if code == ProviderErrorCode.PROVIDER_DISABLED:
        return provider_disabled_error(provider, model, level)
    if code == ProviderErrorCode.NO_API_KEY:
        return no_api_key_error(provider, model, level)
    if code == ProviderErrorCode.INVALID_API_KEY:
        return invalid_api_key_error(provider, model, level)
    if code == ProviderErrorCode.INVALID_MODEL:
        return invalid_model_error(provider, model, level)
    if code == ProviderErrorCode.UNSUPPORTED_L2:
        return unsupported_l2_error(provider, model)
    if code == ProviderErrorCode.TIMEOUT:
        return timeout_error(provider, model, level)
    if code == ProviderErrorCode.RATE_LIMIT:
        return rate_limit_error(provider, model, level)
    if code == ProviderErrorCode.EMPTY_RESPONSE:
        return empty_response_error(provider, model, level)
    if code == ProviderErrorCode.INVALID_RESPONSE:
        return invalid_response_error(provider, model, level)
    if code == ProviderErrorCode.PROVIDER_UNAVAILABLE:
        return _error(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            f"{provider_label(provider)} is currently unavailable.",
            provider,
            model,
            level,
            retryable=True,
        )
    if code == ProviderErrorCode.CONFIGURATION_ERROR:
        return configuration_error(provider, model, level)
    if code == ProviderErrorCode.UNKNOWN_PROVIDER_ERROR:
        return unknown_provider_error(provider, model, level)
    return provider_request_failed_error(provider, model, level)
