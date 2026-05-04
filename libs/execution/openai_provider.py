"""OpenAI Responses API provider adapter."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from libs.execution.openai_config import (
    DEFAULT_OPENAI_L1_MODEL,
    OpenAIConfigError,
    OpenAIProviderConfig,
    load_openai_provider_config,
)
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.provider_errors import (
    configuration_error,
    empty_response_error,
    invalid_response_error,
    no_api_key_error,
    provider_request_failed_error,
    rate_limit_error,
    timeout_error,
    unknown_provider_error,
    unsupported_l2_error,
)

try:
    from openai import APIError as OpenAIAPIError
    from openai import APITimeoutError as OpenAIAPITimeoutError
    from openai import AsyncOpenAI
    from openai import RateLimitError as OpenAIRateLimitError
except Exception:  # pragma: no cover - runtime fallback when SDK is unavailable.
    AsyncOpenAI = None

    class OpenAIAPIError(Exception):
        """Fallback API error class used when openai SDK is unavailable."""

    class OpenAIAPITimeoutError(Exception):
        """Fallback timeout class used when openai SDK is unavailable."""

    class OpenAIRateLimitError(Exception):
        """Fallback rate-limit class used when openai SDK is unavailable."""


DEFAULT_OPENAI_MODEL = DEFAULT_OPENAI_L1_MODEL
WEB_SEARCH_TOOL = {"type": "web_search"}


class OpenAIResponsesClient:
    """Small wrapper around the OpenAI SDK Responses API.

    Tests mock this wrapper instead of the external SDK/network.
    """

    def __init__(self, *, api_key: str, timeout_seconds: float) -> None:
        if AsyncOpenAI is None:
            raise OpenAIConfigError(
                "openai package is required for OpenAI Responses API execution."
            )
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)

    async def create_response(self, **payload: Any) -> Any:
        return await self._client.responses.create(**payload)


class OpenAIProviderAdapter(BaseProviderAdapter):
    """Real OpenAI provider adapter with normalized contract output."""

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        config: OpenAIProviderConfig | None = None,
        client: OpenAIResponsesClient | None = None,
    ) -> None:
        self.config = config or load_openai_provider_config()
        self.model = model or self.config.model_l1
        self.api_key = api_key if api_key is not None else self.config.api_key
        self.timeout_seconds = timeout_seconds or self.config.timeout_seconds
        self.client = client

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        api_key = self.api_key
        if not api_key:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=no_api_key_error("openai").to_error_dict(),
                provider_metadata={"provider": "openai"},
            )

        if self.client is None and AsyncOpenAI is None:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=configuration_error("openai").to_error_dict(),
                provider_metadata={"provider": "openai"},
            )

        scdl_level = kwargs.get("scdl_level", "L1")
        if scdl_level not in {"L1", "L2"}:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=unsupported_l2_error("openai").to_error_dict(),
                provider_metadata={"provider": "openai"},
            )

        model = kwargs.get("model") or self.config.model_for_scdl_level(scdl_level)
        client = self.client or OpenAIResponsesClient(
            api_key=api_key,
            timeout_seconds=self.timeout_seconds,
        )
        payload = self._build_responses_payload(
            query=query,
            model=model,
            scdl_level=scdl_level,
        )
        start = time.perf_counter()

        try:
            response = await client.create_response(**payload)
            elapsed = time.perf_counter() - start

            raw_answer = self._extract_raw_answer(response)
            citations = self._extract_citations(response)
            provider_metadata = self._extract_provider_metadata(response, model=model)

            if raw_answer is None:
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=elapsed,
                    error=invalid_response_error(
                        "openai",
                        model,
                        scdl_level,
                    ).to_error_dict(),
                    provider_metadata=provider_metadata,
                )

            if raw_answer.strip() == "":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=elapsed,
                    error=empty_response_error("openai", model, scdl_level).to_error_dict(),
                    provider_metadata=provider_metadata,
                )

            return ProviderResponse(
                status="success",
                raw_answer=raw_answer,
                citations=citations,
                response_time=elapsed,
                error=None,
                provider_metadata=provider_metadata,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start
            status = self._map_error_status(exc)
            return ProviderResponse(
                status=status,
                raw_answer=None,
                citations=None,
                response_time=elapsed,
                error=self._normalize_error(exc, status=status, model=model, level=scdl_level),
                provider_metadata={"provider": "openai", "model": model},
            )

    def _build_responses_payload(
        self,
        *,
        query: str,
        model: str,
        scdl_level: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "input": query,
            "max_output_tokens": self.config.max_output_tokens,
        }
        if scdl_level == "L2":
            payload["tools"] = [WEB_SEARCH_TOOL]
            payload["tool_choice"] = "auto"
            payload["include"] = ["web_search_call.action.sources"]
        return payload

    def _map_error_status(self, exc: Exception) -> str:
        if isinstance(exc, (asyncio.TimeoutError, OpenAIAPITimeoutError)):
            return "timeout"

        if isinstance(exc, OpenAIRateLimitError):
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
        level: str | None,
    ) -> dict[str, object]:
        if status == "timeout":
            return timeout_error("openai", model, level).to_error_dict()
        if status == "rate_limited":
            return rate_limit_error("openai", model, level).to_error_dict()
        if isinstance(exc, OpenAIAPIError):
            return provider_request_failed_error("openai", model, level).to_error_dict()
        return unknown_provider_error("openai", model, level).to_error_dict()

    def _extract_raw_answer(self, response: Any) -> str | None:
        output_text = self._get_attr_or_key(response, "output_text")
        if isinstance(output_text, str):
            return output_text

        for content_item in self._iter_message_content_items(response):
            text = self._get_attr_or_key(content_item, "text")
            if isinstance(text, str):
                return text

        choice = self._first_choice(response)
        if choice is None:
            return None

        message = self._get_attr_or_key(choice, "message")
        content = self._get_attr_or_key(message, "content")
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                text = self._get_attr_or_key(part, "text")
                if isinstance(text, str):
                    text_parts.append(text)
            if text_parts:
                return "".join(text_parts)

        return None

    def _extract_citations(self, response: Any) -> list[dict]:
        candidates: list[Any] = []
        for content_item in self._iter_message_content_items(response):
            annotations = self._get_attr_or_key(content_item, "annotations")
            if isinstance(annotations, list):
                candidates.extend(annotations)

        response_sources = self._get_attr_or_key(response, "sources")
        if isinstance(response_sources, list):
            candidates.extend(response_sources)

        output = self._get_attr_or_key(response, "output")
        if isinstance(output, list):
            for item in output:
                action = self._get_attr_or_key(item, "action")
                sources = self._get_attr_or_key(action, "sources")
                if isinstance(sources, list):
                    candidates.extend(sources)

        choice = self._first_choice(response)
        message = self._get_attr_or_key(choice, "message")

        message_citations = self._get_attr_or_key(message, "citations")
        if isinstance(message_citations, list):
            candidates.extend(message_citations)

        annotations = self._get_attr_or_key(message, "annotations")
        if isinstance(annotations, list):
            candidates.extend(annotations)

        response_citations = self._get_attr_or_key(response, "citations")
        if isinstance(response_citations, list):
            candidates.extend(response_citations)

        normalized: list[dict] = []
        for candidate in candidates:
            citation = self._normalize_citation(candidate)
            if citation is not None:
                normalized.append(citation)
        return normalized

    def _normalize_citation(self, candidate: Any) -> dict[str, str | None] | None:
        if not isinstance(candidate, dict):
            candidate = self._to_dict(candidate)

        nested = candidate.get("url_citation")
        if isinstance(nested, dict):
            candidate = nested

        url = candidate.get("url")
        if not isinstance(url, str) or not url:
            return None

        title = candidate.get("title")
        if not isinstance(title, str):
            title = None

        return {"url": url, "title": title}

    def _extract_provider_metadata(self, response: Any, model: str) -> dict[str, Any]:
        choice = self._first_choice(response)
        finish_reason = self._get_attr_or_key(choice, "finish_reason")
        response_id = self._get_attr_or_key(response, "id")
        usage = self._get_attr_or_key(response, "usage")

        metadata: dict[str, Any] = {"provider": "openai", "model": model}
        if isinstance(response_id, str):
            metadata["response_id"] = response_id
        if isinstance(finish_reason, str):
            metadata["finish_reason"] = finish_reason
        if usage is not None:
            metadata["usage"] = self._json_safe(usage)
        return metadata

    def _iter_message_content_items(self, response: Any) -> list[Any]:
        output = self._get_attr_or_key(response, "output")
        if not isinstance(output, list):
            return []

        content_items: list[Any] = []
        for item in output:
            item_type = self._get_attr_or_key(item, "type")
            if item_type != "message":
                continue
            content = self._get_attr_or_key(item, "content")
            if isinstance(content, list):
                content_items.extend(content)
        return content_items

    def _first_choice(self, response: Any) -> Any | None:
        choices = self._get_attr_or_key(response, "choices")
        if isinstance(choices, list) and choices:
            return choices[0]
        return None

    def _to_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return dumped
        if hasattr(value, "__dict__"):
            raw = vars(value)
            if isinstance(raw, dict):
                return raw
        return {}

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

