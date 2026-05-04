"""Thin Anthropic Messages API client wrapper."""

from __future__ import annotations

import asyncio
from typing import Any

from libs.execution.anthropic_config import AnthropicConfigError, AnthropicProviderConfig
from libs.execution.provider_errors import no_api_key_error, timeout_error

try:
    from anthropic import APITimeoutError as AnthropicAPITimeoutError
    from anthropic import AsyncAnthropic
except Exception:  # pragma: no cover - runtime fallback when SDK is unavailable.
    AsyncAnthropic = None

    class AnthropicAPITimeoutError(Exception):
        """Fallback timeout class used when Anthropic SDK is unavailable."""


class AnthropicClientError(Exception):
    """Safe wrapper error carrying a normalized provider error dict."""

    def __init__(self, error: dict[str, object]) -> None:
        super().__init__(str(error.get("message", "Anthropic client request failed.")))
        self.error = error


class AnthropicClientWrapper:
    """Small wrapper around the Anthropic SDK Messages API.

    Tests mock this wrapper instead of the external SDK/network.
    """

    def __init__(
        self,
        *,
        config: AnthropicProviderConfig,
        client: Any | None = None,
    ) -> None:
        self.config = config
        self._client = client

    async def create_message(self, **payload: Any) -> Any:
        if not self.config.api_key and self._client is None:
            raise AnthropicClientError(
                no_api_key_error(
                    "anthropic",
                    model=str(payload.get("model") or self.config.model_l1),
                    level="L1",
                ).to_error_dict()
            )

        client = self._client or self._build_client()
        try:
            return await client.messages.create(**payload)
        except (asyncio.TimeoutError, AnthropicAPITimeoutError) as exc:
            raise AnthropicClientError(
                timeout_error(
                    "anthropic",
                    model=str(payload.get("model") or self.config.model_l1),
                    level="L1",
                ).to_error_dict()
            ) from exc

    def _build_client(self) -> Any:
        if AsyncAnthropic is None:
            raise AnthropicConfigError(
                "anthropic package is required for Anthropic Messages API execution."
            )
        return AsyncAnthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
        )
