"""OpenRouter gateway provider configuration with secret-safe representation."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from libs.execution.pilot_config import RealProviderPilotConfig

DEFAULT_OPENROUTER_TIMEOUT_SECONDS = 30.0
DEFAULT_OPENROUTER_MAX_OUTPUT_TOKENS = 1200
DEFAULT_OPENROUTER_WEB_SEARCH_ENABLED = False
DEFAULT_OPENROUTER_WEB_SEARCH_TOOL = "openrouter:web_search"
DEFAULT_OPENROUTER_APP_NAME = "AI Brand Visibility Monitor"


class OpenRouterConfigError(ValueError):
    """Raised when OpenRouter configuration is invalid or incomplete."""


@dataclass(frozen=True)
class OpenRouterProviderConfig:
    api_key: str | None = field(default=None, repr=False)
    model_l1: str | None = None
    model_l2: str | None = None
    timeout_seconds: float = DEFAULT_OPENROUTER_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_OPENROUTER_MAX_OUTPUT_TOKENS
    web_search_enabled: bool = DEFAULT_OPENROUTER_WEB_SEARCH_ENABLED
    web_search_tool: str = DEFAULT_OPENROUTER_WEB_SEARCH_TOOL
    site_url: str | None = None
    app_name: str = DEFAULT_OPENROUTER_APP_NAME
    allowed_models: tuple[str, ...] = ()

    def __repr__(self) -> str:
        key_status = "***" if self.api_key else None
        return (
            "OpenRouterProviderConfig("
            f"api_key={key_status!r}, "
            f"model_l1={self.model_l1!r}, "
            f"model_l2={self.model_l2!r}, "
            f"timeout_seconds={self.timeout_seconds!r}, "
            f"max_output_tokens={self.max_output_tokens!r}, "
            f"web_search_enabled={self.web_search_enabled!r}, "
            f"web_search_tool={self.web_search_tool!r}, "
            f"site_url={self.site_url!r}, "
            f"app_name={self.app_name!r}, "
            f"allowed_models={self.allowed_models!r}"
            ")"
        )

    def model_for_scdl_level(self, scdl_level: str) -> str | None:
        if scdl_level == "L1":
            return self.model_l1
        if scdl_level == "L2":
            return self.model_l2
        raise OpenRouterConfigError(
            "OpenRouter model can only be selected for SCDL L1 or L2."
        )

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "api_key": "***" if self.api_key else None,
            "model_l1": self.model_l1,
            "model_l2": self.model_l2,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
            "web_search_enabled": self.web_search_enabled,
            "web_search_tool": self.web_search_tool,
            "site_url": self.site_url,
            "app_name": self.app_name,
            "allowed_models": list(self.allowed_models),
        }

    def optional_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-OpenRouter-Title"] = self.app_name
        return headers


def load_openrouter_provider_config(
    env: Mapping[str, str] | None = None,
    *,
    require_api_key: bool = False,
) -> OpenRouterProviderConfig:
    source = os.environ if env is None else env
    config = OpenRouterProviderConfig(
        api_key=_load_optional_text(source, "OPENROUTER_API_KEY"),
        model_l1=_load_optional_text(source, "OPENROUTER_L1_MODEL"),
        model_l2=_load_optional_text(source, "OPENROUTER_L2_MODEL"),
        timeout_seconds=_load_positive_float(
            source,
            "OPENROUTER_REQUEST_TIMEOUT_SECONDS",
            DEFAULT_OPENROUTER_TIMEOUT_SECONDS,
        ),
        max_output_tokens=_load_positive_int(
            source,
            "OPENROUTER_MAX_OUTPUT_TOKENS",
            DEFAULT_OPENROUTER_MAX_OUTPUT_TOKENS,
        ),
        web_search_enabled=_load_bool(
            source,
            "OPENROUTER_WEB_SEARCH_ENABLED",
            DEFAULT_OPENROUTER_WEB_SEARCH_ENABLED,
        ),
        web_search_tool=_load_required_text(
            source,
            "OPENROUTER_WEB_SEARCH_TOOL",
            DEFAULT_OPENROUTER_WEB_SEARCH_TOOL,
        ),
        site_url=_load_optional_text(source, "OPENROUTER_SITE_URL"),
        app_name=_load_required_text(
            source,
            "OPENROUTER_APP_NAME",
            DEFAULT_OPENROUTER_APP_NAME,
        ),
        allowed_models=_load_csv_tuple(source, "OPENROUTER_ALLOWED_MODELS"),
    )

    if require_api_key and not config.api_key:
        raise OpenRouterConfigError(
            "OPENROUTER_API_KEY is required when OpenRouter mode is enabled."
        )
    return config


def validate_openrouter_config_for_pilot(
    pilot_config: RealProviderPilotConfig,
    env: Mapping[str, str] | None = None,
) -> OpenRouterProviderConfig:
    require_api_key = (
        pilot_config.provider_mode == "openrouter" and pilot_config.real_provider_enabled
    )
    return load_openrouter_provider_config(env=env, require_api_key=require_api_key)


def _load_optional_text(source: Mapping[str, str], key: str) -> str | None:
    raw_value = source.get(key)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _load_required_text(source: Mapping[str, str], key: str, default: str) -> str:
    value = _load_optional_text(source, key)
    if value is None:
        return default
    return value


def _load_positive_float(source: Mapping[str, str], key: str, default: float) -> float:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = float(raw_value.strip())
    except ValueError as exc:
        raise OpenRouterConfigError(f"{key} must be a positive number.") from exc
    if value <= 0:
        raise OpenRouterConfigError(f"{key} must be a positive number.")
    return value


def _load_positive_int(source: Mapping[str, str], key: str, default: int) -> int:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        raise OpenRouterConfigError(f"{key} must be a positive integer.") from exc
    if value <= 0:
        raise OpenRouterConfigError(f"{key} must be a positive integer.")
    return value


def _load_bool(source: Mapping[str, str], key: str, default: bool) -> bool:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise OpenRouterConfigError(f"{key} must be a boolean value.")


def _load_csv_tuple(source: Mapping[str, str], key: str) -> tuple[str, ...]:
    raw_value = source.get(key)
    if raw_value is None:
        return ()
    values = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    return values
