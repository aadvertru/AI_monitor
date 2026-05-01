"""OpenAI provider configuration with secret-safe representation."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from libs.execution.pilot_config import RealProviderPilotConfig

DEFAULT_OPENAI_L1_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_L2_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 30.0
DEFAULT_OPENAI_MAX_OUTPUT_TOKENS = 1200


class OpenAIConfigError(ValueError):
    """Raised when OpenAI provider configuration is invalid or incomplete."""


@dataclass(frozen=True)
class OpenAIProviderConfig:
    api_key: str | None = field(default=None, repr=False)
    model_l1: str = DEFAULT_OPENAI_L1_MODEL
    model_l2: str = DEFAULT_OPENAI_L2_MODEL
    timeout_seconds: float = DEFAULT_OPENAI_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_OPENAI_MAX_OUTPUT_TOKENS

    def __repr__(self) -> str:
        key_status = "***" if self.api_key else None
        return (
            "OpenAIProviderConfig("
            f"api_key={key_status!r}, "
            f"model_l1={self.model_l1!r}, "
            f"model_l2={self.model_l2!r}, "
            f"timeout_seconds={self.timeout_seconds!r}, "
            f"max_output_tokens={self.max_output_tokens!r}"
            ")"
        )

    def model_for_scdl_level(self, scdl_level: str) -> str:
        if scdl_level == "L1":
            return self.model_l1
        if scdl_level == "L2":
            return self.model_l2
        raise OpenAIConfigError("OpenAI model can only be selected for SCDL L1 or L2.")

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "api_key": "***" if self.api_key else None,
            "model_l1": self.model_l1,
            "model_l2": self.model_l2,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
        }


def load_openai_provider_config(
    env: Mapping[str, str] | None = None,
    *,
    require_api_key: bool = False,
) -> OpenAIProviderConfig:
    source = os.environ if env is None else env
    config = OpenAIProviderConfig(
        api_key=_load_optional_text(source, "OPENAI_API_KEY"),
        model_l1=_load_required_text(
            source,
            "OPENAI_L1_MODEL",
            DEFAULT_OPENAI_L1_MODEL,
        ),
        model_l2=_load_required_text(
            source,
            "OPENAI_L2_MODEL",
            DEFAULT_OPENAI_L2_MODEL,
        ),
        timeout_seconds=_load_positive_float(
            source,
            "OPENAI_REQUEST_TIMEOUT_SECONDS",
            DEFAULT_OPENAI_TIMEOUT_SECONDS,
        ),
        max_output_tokens=_load_positive_int(
            source,
            "OPENAI_MAX_OUTPUT_TOKENS",
            DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
        ),
    )

    if require_api_key and not config.api_key:
        raise OpenAIConfigError("OPENAI_API_KEY is required when OpenAI mode is enabled.")
    return config


def validate_openai_config_for_pilot(
    pilot_config: RealProviderPilotConfig,
    env: Mapping[str, str] | None = None,
) -> OpenAIProviderConfig:
    require_api_key = (
        pilot_config.provider_mode == "openai" and pilot_config.real_provider_enabled
    )
    return load_openai_provider_config(env=env, require_api_key=require_api_key)


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
        raise OpenAIConfigError(f"{key} must be a positive number.") from exc
    if value <= 0:
        raise OpenAIConfigError(f"{key} must be a positive number.")
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
        raise OpenAIConfigError(f"{key} must be a positive integer.") from exc
    if value <= 0:
        raise OpenAIConfigError(f"{key} must be a positive integer.")
    return value
