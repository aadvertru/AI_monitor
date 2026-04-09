"""OpenAI provider adapter that maps API responses to ProviderResponse."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse

try:
    from openai import APITimeoutError as OpenAIAPITimeoutError
    from openai import AsyncOpenAI
    from openai import RateLimitError as OpenAIRateLimitError
except Exception:  # pragma: no cover - runtime fallback when SDK is unavailable.
    AsyncOpenAI = None

    class OpenAIAPITimeoutError(Exception):
        """Fallback timeout class used when openai SDK is unavailable."""

    class OpenAIRateLimitError(Exception):
        """Fallback rate-limit class used when openai SDK is unavailable."""


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


class OpenAIProviderAdapter(BaseProviderAdapter):
    """Real OpenAI provider adapter with normalized contract output."""

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error={
                    "code": "missing_api_key",
                    "message": "OPENAI_API_KEY is not configured.",
                },
                provider_metadata={"provider": "openai"},
            )

        if AsyncOpenAI is None:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error={
                    "code": "sdk_not_installed",
                    "message": "openai package is required for OpenAIProviderAdapter.",
                },
                provider_metadata={"provider": "openai"},
            )

        client = AsyncOpenAI(api_key=api_key, timeout=self.timeout_seconds)
        model = kwargs.get("model", self.model)
        start = time.perf_counter()

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": query}],
            )
            elapsed = time.perf_counter() - start

            raw_answer = self._extract_raw_answer(response)
            citations = self._extract_citations(response)
            provider_metadata = self._extract_provider_metadata(response, model=model)

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
                error=self._normalize_error(exc, status=status),
                provider_metadata={"provider": "openai", "model": model},
            )

    def _map_error_status(self, exc: Exception) -> str:
        if isinstance(exc, (asyncio.TimeoutError, OpenAIAPITimeoutError)):
            return "timeout"

        if isinstance(exc, OpenAIRateLimitError):
            return "rate_limited"

        status_code = getattr(exc, "status_code", None)
        if status_code == 429:
            return "rate_limited"

        return "error"

    def _normalize_error(self, exc: Exception, status: str) -> dict[str, str]:
        if status == "timeout":
            return {"code": "timeout", "message": str(exc) or "Request timed out."}
        if status == "rate_limited":
            return {"code": "rate_limited", "message": str(exc) or "Rate limit exceeded."}
        return {"code": "provider_error", "message": str(exc) or "OpenAI request failed."}

    def _extract_raw_answer(self, response: Any) -> str | None:
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
            metadata["usage"] = usage
        return metadata

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

