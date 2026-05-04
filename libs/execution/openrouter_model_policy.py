"""OpenRouter gateway model routing policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from libs.execution.openrouter_config import OpenRouterProviderConfig
from libs.execution.provider_errors import ProviderErrorCode


class OpenRouterModelPolicyError(ValueError):
    """Raised when an OpenRouter model selection violates backend policy."""

    def __init__(self, code: ProviderErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OpenRouterModelSelection:
    model_id: str
    model_provider: str
    level: Literal["L1", "L2"]

    def gateway_metadata(self) -> dict[str, object]:
        return {
            "execution_provider": "openrouter",
            "model_id": self.model_id,
            "model_provider": self.model_provider,
            "gateway": True,
            "gateway_l2_experimental": self.level == "L2",
            "level": self.level,
        }


def derive_openrouter_model_provider(model_id: str) -> str:
    normalized = model_id.strip()
    if "/" not in normalized:
        raise OpenRouterModelPolicyError(
            ProviderErrorCode.INVALID_MODEL,
            "Selected OpenRouter model is invalid.",
        )
    provider, model = normalized.split("/", 1)
    if not provider.strip() or not model.strip():
        raise OpenRouterModelPolicyError(
            ProviderErrorCode.INVALID_MODEL,
            "Selected OpenRouter model is invalid.",
        )
    return provider.strip()


def validate_openrouter_model_id(model_id: str, allowed_models: set[str]) -> str:
    normalized = model_id.strip()
    if not allowed_models:
        raise OpenRouterModelPolicyError(
            ProviderErrorCode.CONFIGURATION_ERROR,
            "OpenRouter allowed models are not configured.",
        )
    derive_openrouter_model_provider(normalized)
    if normalized not in allowed_models:
        raise OpenRouterModelPolicyError(
            ProviderErrorCode.INVALID_MODEL,
            "Selected OpenRouter model is not allowed.",
        )
    return normalized


def select_openrouter_model(
    level: Literal["L1", "L2"],
    config: OpenRouterProviderConfig,
    *,
    requested_model_id: str | None = None,
) -> OpenRouterModelSelection:
    configured_model = requested_model_id or config.model_for_scdl_level(level)
    if not configured_model:
        raise OpenRouterModelPolicyError(
            ProviderErrorCode.CONFIGURATION_ERROR,
            f"OpenRouter {level} model is not configured.",
        )

    model_id = validate_openrouter_model_id(
        configured_model,
        set(config.allowed_models),
    )
    return OpenRouterModelSelection(
        model_id=model_id,
        model_provider=derive_openrouter_model_provider(model_id),
        level=level,
    )
