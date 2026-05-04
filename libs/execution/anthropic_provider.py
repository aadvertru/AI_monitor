"""Anthropic Claude Messages API provider adapter."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from libs.execution.anthropic_client import AnthropicClientError, AnthropicClientWrapper
from libs.execution.anthropic_config import (
    DEFAULT_ANTHROPIC_L1_MODEL,
    AnthropicConfigError,
    AnthropicProviderConfig,
    load_anthropic_provider_config,
)
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.provider_errors import (
    configuration_error,
    empty_response_error,
    invalid_api_key_error,
    invalid_model_error,
    invalid_response_error,
    no_api_key_error,
    provider_request_failed_error,
    rate_limit_error,
    timeout_error,
    unknown_provider_error,
    unsupported_l2_error,
)

try:
    from anthropic import APIStatusError as AnthropicAPIStatusError
    from anthropic import APITimeoutError as AnthropicAPITimeoutError
    from anthropic import RateLimitError as AnthropicRateLimitError
except Exception:  # pragma: no cover - runtime fallback when SDK is unavailable.

    class AnthropicAPIStatusError(Exception):
        """Fallback API status error class used when Anthropic SDK is unavailable."""

    class AnthropicAPITimeoutError(Exception):
        """Fallback timeout class used when Anthropic SDK is unavailable."""

    class AnthropicRateLimitError(Exception):
        """Fallback rate-limit class used when Anthropic SDK is unavailable."""


DEFAULT_ANTHROPIC_MODEL = DEFAULT_ANTHROPIC_L1_MODEL


class AnthropicProviderAdapter(BaseProviderAdapter):
    """Real Anthropic provider adapter for Claude L1 only."""

    def __init__(
        self,
        model: str = DEFAULT_ANTHROPIC_MODEL,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        config: AnthropicProviderConfig | None = None,
        client: AnthropicClientWrapper | None = None,
    ) -> None:
        self.config = config or load_anthropic_provider_config()
        self.model = model or self.config.model_l1
        self.api_key = api_key if api_key is not None else self.config.api_key
        self.timeout_seconds = timeout_seconds or self.config.timeout_seconds
        self.client = client

    async def query(self, query: str, **kwargs: Any) -> ProviderResponse:
        scdl_level = kwargs.get("scdl_level", "L1")
        if scdl_level != "L1":
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=unsupported_l2_error("anthropic", self.model).to_error_dict(),
                provider_metadata={"provider": "anthropic", "model": self.model, "level": "L2"},
            )

        api_key = self.api_key
        model = kwargs.get("model") or self.config.model_for_scdl_level("L1")
        if not api_key and self.client is None:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=no_api_key_error("anthropic", model, "L1").to_error_dict(),
                provider_metadata={"provider": "anthropic", "model": model, "level": "L1"},
            )

        payload = self._build_messages_payload(query=query, model=model)
        client = self.client or AnthropicClientWrapper(
            config=AnthropicProviderConfig(
                api_key=api_key,
                model_l1=self.config.model_l1,
                timeout_seconds=self.timeout_seconds,
                max_output_tokens=self.config.max_output_tokens,
            )
        )
        start = time.perf_counter()

        try:
            response = await client.create_message(**payload)
            elapsed = time.perf_counter() - start
            raw_answer = self._extract_raw_answer(response)
            provider_metadata = self._extract_provider_metadata(response, model=model)

            if raw_answer is None:
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=elapsed,
                    error=invalid_response_error("anthropic", model, "L1").to_error_dict(),
                    provider_metadata=provider_metadata,
                )
            if raw_answer.strip() == "":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=elapsed,
                    error=empty_response_error("anthropic", model, "L1").to_error_dict(),
                    provider_metadata=provider_metadata,
                )

            return ProviderResponse(
                status="success",
                raw_answer=raw_answer,
                citations=[],
                response_time=elapsed,
                error=None,
                provider_metadata=provider_metadata,
            )
        except AnthropicClientError as exc:
            elapsed = time.perf_counter() - start
            return ProviderResponse(
                status=self._status_for_error_dict(exc.error),
                raw_answer=None,
                citations=None,
                response_time=elapsed,
                error=exc.error,
                provider_metadata={"provider": "anthropic", "model": model, "level": "L1"},
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start
            status = self._map_error_status(exc)
            return ProviderResponse(
                status=status,
                raw_answer=None,
                citations=None,
                response_time=elapsed,
                error=self._normalize_error(exc, status=status, model=model),
                provider_metadata={"provider": "anthropic", "model": model, "level": "L1"},
            )

    def _build_messages_payload(self, *, query: str, model: str) -> dict[str, Any]:
        return {
            "model": model,
            "max_tokens": self.config.max_output_tokens,
            "messages": [{"role": "user", "content": query}],
        }

    def _map_error_status(self, exc: Exception) -> str:
        if isinstance(exc, (asyncio.TimeoutError, AnthropicAPITimeoutError)):
            return "timeout"
        if isinstance(exc, AnthropicRateLimitError):
            return "rate_limited"
        status_code = getattr(exc, "status_code", None)
        if status_code == 429:
            return "rate_limited"
        return "error"

    def _normalize_error(
        self,
        exc: Exception,
        status: str,
        *,
        model: str | None,
    ) -> dict[str, object]:
        if status == "timeout":
            return timeout_error("anthropic", model, "L1").to_error_dict()
        if status == "rate_limited":
            return rate_limit_error("anthropic", model, "L1").to_error_dict()
        if isinstance(exc, AnthropicConfigError):
            return configuration_error("anthropic", model, "L1").to_error_dict()
        status_code = getattr(exc, "status_code", None)
        if status_code in {401, 403}:
            return invalid_api_key_error("anthropic", model, "L1").to_error_dict()
        if status_code in {400, 404}:
            return invalid_model_error("anthropic", model, "L1").to_error_dict()
        if isinstance(exc, AnthropicAPIStatusError):
            return provider_request_failed_error("anthropic", model, "L1").to_error_dict()
        return unknown_provider_error("anthropic", model, "L1").to_error_dict()

    def _status_for_error_dict(self, error: dict[str, object]) -> str:
        code = str(error.get("code", ""))
        if code == "TIMEOUT":
            return "timeout"
        if code == "RATE_LIMIT":
            return "rate_limited"
        return "error"

    def _extract_raw_answer(self, response: Any) -> str | None:
        output_text = self._get_attr_or_key(response, "output_text")
        if isinstance(output_text, str):
            return output_text

        content = self._get_attr_or_key(response, "content")
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return None

        text_parts: list[str] = []
        for block in content:
            block_type = self._get_attr_or_key(block, "type")
            text = self._get_attr_or_key(block, "text")
            if block_type in {None, "text"} and isinstance(text, str):
                text_parts.append(text)
        if not text_parts:
            return None
        return "\n".join(text_parts)

    def _extract_provider_metadata(self, response: Any, model: str) -> dict[str, Any]:
        response_id = self._get_attr_or_key(response, "id")
        stop_reason = self._get_attr_or_key(response, "stop_reason")
        usage = self._get_attr_or_key(response, "usage")

        metadata: dict[str, Any] = {"provider": "anthropic", "model": model, "level": "L1"}
        if isinstance(response_id, str):
            metadata["response_id"] = response_id
        if isinstance(stop_reason, str):
            metadata["stop_reason"] = stop_reason
        if usage is not None:
            metadata["usage"] = self._usage_metadata(usage)
        return metadata

    def _usage_metadata(self, usage: Any) -> dict[str, Any]:
        safe_usage = self._json_safe(usage)
        if not isinstance(safe_usage, dict):
            return {"raw_usage": safe_usage}
        input_tokens = safe_usage.get("input_tokens")
        output_tokens = safe_usage.get("output_tokens")
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            safe_usage["total_tokens"] = input_tokens + output_tokens
        return safe_usage

    def _get_attr_or_key(self, value: Any, key: str) -> Any:
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get(key)
        return getattr(value, key, None)

    def _json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, list | tuple):
            return [self._json_safe(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return self._json_safe(dumped)
        if hasattr(value, "__dict__"):
            return self._json_safe(vars(value))
        return str(value)
