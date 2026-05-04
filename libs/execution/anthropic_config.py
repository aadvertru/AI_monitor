"""Anthropic provider configuration with secret-safe representation."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from libs.execution.pilot_config import RealProviderPilotConfig

DEFAULT_ANTHROPIC_L1_MODEL = "claude-3-5-haiku-latest"
DEFAULT_ANTHROPIC_TIMEOUT_SECONDS = 30.0
DEFAULT_ANTHROPIC_MAX_OUTPUT_TOKENS = 1200


class AnthropicConfigError(ValueError):
    """Raised when Anthropic provider configuration is invalid or incomplete."""


@dataclass(frozen=True)
class AnthropicProviderConfig:
    api_key: str | None = field(default=None, repr=False)
    model_l1: str = DEFAULT_ANTHROPIC_L1_MODEL
    timeout_seconds: float = DEFAULT_ANTHROPIC_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_ANTHROPIC_MAX_OUTPUT_TOKENS

    def __repr__(self) -> str:
        key_status = "***" if self.api_key else None
        return (
            "AnthropicProviderConfig("
            f"api_key={key_status!r}, "
            f"model_l1={self.model_l1!r}, "
            f"timeout_seconds={self.timeout_seconds!r}, "
            f"max_output_tokens={self.max_output_tokens!r}"
            ")"
        )

    def model_for_scdl_level(self, scdl_level: str) -> str:
        if scdl_level == "L1":
            return self.model_l1
        raise AnthropicConfigError("Anthropic model can only be selected for SCDL L1.")

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "api_key": "***" if self.api_key else None,
            "model_l1": self.model_l1,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
        }


def load_anthropic_provider_config(
    env: Mapping[str, str] | None = None,
    *,
    require_api_key: bool = False,
) -> AnthropicProviderConfig:
    source = os.environ if env is None else env
    config = AnthropicProviderConfig(
        api_key=_load_optional_text(source, "ANTHROPIC_API_KEY"),
        model_l1=_load_required_text(
            source,
            "ANTHROPIC_L1_MODEL",
            DEFAULT_ANTHROPIC_L1_MODEL,
        ),
        timeout_seconds=_load_positive_float(
            source,
            "ANTHROPIC_REQUEST_TIMEOUT_SECONDS",
            DEFAULT_ANTHROPIC_TIMEOUT_SECONDS,
        ),
        max_output_tokens=_load_positive_int(
            source,
            "ANTHROPIC_MAX_OUTPUT_TOKENS",
            DEFAULT_ANTHROPIC_MAX_OUTPUT_TOKENS,
        ),
    )

    if require_api_key and not config.api_key:
        raise AnthropicConfigError(
            "ANTHROPIC_API_KEY is required when Anthropic mode is enabled."
        )
    return config


def validate_anthropic_config_for_pilot(
    pilot_config: RealProviderPilotConfig,
    env: Mapping[str, str] | None = None,
) -> AnthropicProviderConfig:
    require_api_key = (
        pilot_config.provider_mode == "anthropic" and pilot_config.real_provider_enabled
    )
    return load_anthropic_provider_config(env=env, require_api_key=require_api_key)


def _load_optional_text(source: Mapping[str, str], key: str) -> str | None:
    raw_value = source.get(key)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _load_required_text(
    source: Mapping[str, str],
    key: str,
    default: str,
) -> str:
    value = _load_optional_text(source, key)
    if value is None:
        return default
    return value


def _load_positive_float(
    source: Mapping[str, str],
    key: str,
    default: float,
) -> float:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = float(raw_value.strip())
    except ValueError as exc:
        raise AnthropicConfigError(f"{key} must be a positive number.") from exc
    if value <= 0:
        raise AnthropicConfigError(f"{key} must be a positive number.")
    return value


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
        raise AnthropicConfigError(f"{key} must be a positive integer.") from exc
    if value <= 0:
        raise AnthropicConfigError(f"{key} must be a positive integer.")
    return value
