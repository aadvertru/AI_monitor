"""Provider adapter selection for execution paths."""

from __future__ import annotations

from libs.execution.anthropic_client import AnthropicClientWrapper
from libs.execution.anthropic_config import validate_anthropic_config_for_pilot
from libs.execution.anthropic_provider import AnthropicProviderAdapter
from libs.execution.mock_provider import MockProviderAdapter
from libs.execution.openai_config import validate_openai_config_for_pilot
from libs.execution.openai_provider import OpenAIProviderAdapter, OpenAIResponsesClient
from libs.execution.openrouter_client import OpenRouterClientWrapper
from libs.execution.openrouter_config import validate_openrouter_config_for_pilot
from libs.execution.openrouter_provider import OpenRouterProviderAdapter
from libs.execution.pilot_config import (
    PilotPolicyError,
    RealProviderPilotConfig,
    load_real_provider_pilot_config,
)
from libs.execution.provider_adapter import BaseProviderAdapter


def build_provider_adapter(
    provider_code: str,
    *,
    pilot_config: RealProviderPilotConfig | None = None,
    openai_client: OpenAIResponsesClient | None = None,
    anthropic_client: AnthropicClientWrapper | None = None,
    openrouter_client: OpenRouterClientWrapper | None = None,
) -> BaseProviderAdapter:
    normalized_provider = provider_code.strip().lower()
    config = pilot_config or load_real_provider_pilot_config()

    if normalized_provider == "mock":
        return MockProviderAdapter()

    if config.provider_mode == "openrouter" and normalized_provider in {
        "openrouter",
        "openai",
        "anthropic",
        "gemini",
    }:
        if not config.real_provider_enabled:
            raise PilotPolicyError(
                "OpenRouter adapter can only be selected when real provider mode is enabled."
            )
        openrouter_config = validate_openrouter_config_for_pilot(config)
        return OpenRouterProviderAdapter(config=openrouter_config, client=openrouter_client)

    if normalized_provider == "openrouter":
        raise PilotPolicyError(
            "OpenRouter adapter can only be selected when real provider mode is enabled."
        )

    if normalized_provider == "openai":
        if config.provider_mode != "openai" or not config.real_provider_enabled:
            raise PilotPolicyError(
                "OpenAI adapter can only be selected when real provider mode is enabled."
            )
        openai_config = validate_openai_config_for_pilot(config)
        return OpenAIProviderAdapter(config=openai_config, client=openai_client)

    if normalized_provider == "anthropic":
        if config.provider_mode != "anthropic" or not config.real_provider_enabled:
            raise PilotPolicyError(
                "Anthropic adapter can only be selected when real provider mode is enabled."
            )
        anthropic_config = validate_anthropic_config_for_pilot(config)
        return AnthropicProviderAdapter(config=anthropic_config, client=anthropic_client)

    raise PilotPolicyError(f"Unsupported provider adapter: {normalized_provider}.")
