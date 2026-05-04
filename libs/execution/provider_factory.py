"""Provider adapter selection for execution paths."""

from __future__ import annotations

from libs.execution.mock_provider import MockProviderAdapter
from libs.execution.openai_config import validate_openai_config_for_pilot
from libs.execution.openai_provider import OpenAIProviderAdapter, OpenAIResponsesClient
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
) -> BaseProviderAdapter:
    normalized_provider = provider_code.strip().lower()
    config = pilot_config or load_real_provider_pilot_config()

    if normalized_provider == "mock":
        return MockProviderAdapter()

    if normalized_provider == "openai":
        if config.provider_mode != "openai" or not config.real_provider_enabled:
            raise PilotPolicyError(
                "OpenAI adapter can only be selected when real provider mode is enabled."
            )
        openai_config = validate_openai_config_for_pilot(config)
        return OpenAIProviderAdapter(config=openai_config, client=openai_client)

    raise PilotPolicyError(f"Unsupported provider adapter: {normalized_provider}.")
