"""Thin OpenRouter chat completions client wrapper."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from libs.execution.openrouter_config import OpenRouterProviderConfig
from libs.execution.provider_errors import (
    invalid_api_key_error,
    invalid_model_error,
    no_api_key_error,
    provider_request_failed_error,
    rate_limit_error,
    timeout_error,
)

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterClientError(Exception):
    """Safe wrapper error carrying a normalized provider error dict."""

    def __init__(self, error: dict[str, object]) -> None:
        super().__init__(str(error.get("message", "OpenRouter client request failed.")))
        self.error = error


class OpenRouterClientWrapper:
    """Small wrapper around OpenRouter's OpenAI-compatible Chat Completions API.

    Tests mock this wrapper instead of the external network.
    """

    def __init__(
        self,
        *,
        config: OpenRouterProviderConfig,
        client: Any | None = None,
        endpoint_url: str = OPENROUTER_CHAT_COMPLETIONS_URL,
    ) -> None:
        self.config = config
        self._client = client
        self.endpoint_url = endpoint_url

    async def create_chat_completion(self, **payload: Any) -> Any:
        model = str(payload.get("model") or "")
        level = str(payload.pop("_scdl_level", "") or "") or None

        if not self.config.api_key and self._client is None:
            raise OpenRouterClientError(
                no_api_key_error("openrouter", model=model or None, level=level).to_error_dict()
            )

        try:
            if self._client is not None:
                return await self._client.create_chat_completion(**payload)
            return await self._post_with_httpx(payload, level=level)
        except OpenRouterClientError:
            raise
        except (asyncio.TimeoutError, httpx.TimeoutException) as exc:
            raise OpenRouterClientError(
                timeout_error("openrouter", model=model or None, level=level).to_error_dict()
            ) from exc
        except httpx.HTTPError as exc:
            raise OpenRouterClientError(
                provider_request_failed_error(
                    "openrouter", model=model or None, level=level
                ).to_error_dict()
            ) from exc

    async def _post_with_httpx(self, payload: dict[str, Any], *, level: str | None) -> Any:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            **self.config.optional_headers(),
        }
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            response = await client.post(self.endpoint_url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise OpenRouterClientError(
                self._error_for_status(response.status_code, payload, level=level)
            )

        return response.json()

    def _error_for_status(
        self,
        status_code: int,
        payload: dict[str, Any],
        *,
        level: str | None,
    ) -> dict[str, object]:
        model = str(payload.get("model") or "") or None
        if status_code in {401, 403}:
            return invalid_api_key_error("openrouter", model, level).to_error_dict()
        if status_code == 429:
            return rate_limit_error("openrouter", model, level).to_error_dict()
        if status_code in {400, 404}:
            return invalid_model_error("openrouter", model, level).to_error_dict()
        return provider_request_failed_error("openrouter", model, level).to_error_dict()
