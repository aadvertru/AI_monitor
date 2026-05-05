"""OpenRouter gateway provider adapter."""

from __future__ import annotations

import logging
import time
from typing import Any

from libs.execution.openrouter_client import OpenRouterClientError, OpenRouterClientWrapper
from libs.execution.openrouter_config import (
    OpenRouterProviderConfig,
    load_openrouter_provider_config,
)
from libs.execution.openrouter_model_policy import (
    OpenRouterModelPolicyError,
    OpenRouterModelSelection,
    select_openrouter_model,
)
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.provider_errors import (
    ProviderErrorCode,
    configuration_error,
    empty_response_error,
    invalid_model_error,
    invalid_response_error,
    no_api_key_error,
    unknown_provider_error,
)
from libs.execution.safe_logging import log_event

logger = logging.getLogger(__name__)


class OpenRouterProviderAdapter(BaseProviderAdapter):
    """OpenRouter gateway adapter with normalized contract output."""

    def __init__(
        self,
        *,
        config: OpenRouterProviderConfig | None = None,
        client: OpenRouterClientWrapper | None = None,
    ) -> None:
        self.config = config or load_openrouter_provider_config()
        self.client = client

    async def query(self, query: str, **kwargs: Any) -> ProviderResponse:
        scdl_level = str(kwargs.get("scdl_level", "L1"))
        if scdl_level not in {"L1", "L2"}:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=configuration_error("openrouter").to_error_dict(),
                provider_metadata={"provider": "openrouter", "level": scdl_level},
            )

        level = scdl_level
        if level == "L2" and not self.config.web_search_enabled:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=configuration_error("openrouter", level="L2").to_error_dict(),
                provider_metadata={
                    "provider": "openrouter",
                    "execution_provider": "openrouter",
                    "gateway": True,
                    "gateway_l2_experimental": True,
                    "level": "L2",
                },
            )

        try:
            requested_model_id = kwargs.get("model_id")
            selection = select_openrouter_model(
                level,
                self.config,
                requested_model_id=(
                    requested_model_id if isinstance(requested_model_id, str) else None
                ),
            )
        except OpenRouterModelPolicyError as exc:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=self._policy_error_to_dict(exc, level),
                provider_metadata={"provider": "openrouter", "level": level},
            )

        if not self.config.api_key and self.client is None:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=None,
                error=no_api_key_error("openrouter", selection.model_id, level).to_error_dict(),
                provider_metadata=self._metadata(selection),
            )

        client = self.client or OpenRouterClientWrapper(config=self.config)
        payload = self._build_payload(query=query, selection=selection)
        start = time.perf_counter()

        try:
            response = await client.create_chat_completion(**payload, _scdl_level=level)
            elapsed = time.perf_counter() - start
            raw_answer = self._extract_answer_text(response)
            sources = self._extract_sources(response) if level == "L2" else []
            metadata = self._metadata(selection, response=response, sources=sources)

            if raw_answer is None:
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=elapsed,
                    error=invalid_response_error(
                        "openrouter", selection.model_id, level
                    ).to_error_dict(),
                    provider_metadata=metadata,
                )
            if raw_answer.strip() == "":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=elapsed,
                    error=empty_response_error(
                        "openrouter", selection.model_id, level
                    ).to_error_dict(),
                    provider_metadata=metadata,
                )

            return ProviderResponse(
                status="success",
                raw_answer=raw_answer.strip(),
                citations=sources,
                response_time=elapsed,
                error=None,
                provider_metadata=metadata,
            )
        except OpenRouterClientError as exc:
            elapsed = time.perf_counter() - start
            error = exc.error
            status = self._status_for_error(error)
            return ProviderResponse(
                status=status,
                raw_answer=None,
                citations=None,
                response_time=elapsed,
                error=error,
                provider_metadata=self._metadata(selection),
            )
        except Exception:
            elapsed = time.perf_counter() - start
            log_event(
                logger,
                "openrouter_query_unexpected_error",
                log_level=logging.WARNING,
                execution_provider="openrouter",
                model_id=selection.model_id,
                model_provider=selection.model_provider,
                level=level,
                gateway=True,
                gateway_l2_experimental=level == "L2",
                exception_type="unexpected_provider_exception",
            )
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=elapsed,
                error=unknown_provider_error(
                    "openrouter", selection.model_id, level
                ).to_error_dict(),
                provider_metadata=self._metadata(selection),
            )

    def _build_payload(
        self,
        *,
        query: str,
        selection: OpenRouterModelSelection,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": selection.model_id,
            "max_tokens": self.config.max_output_tokens,
            "messages": [{"role": "user", "content": query}],
        }
        if selection.level == "L2":
            payload["tools"] = [{"type": self.config.web_search_tool}]
        return payload

    def _metadata(
        self,
        selection: OpenRouterModelSelection,
        *,
        response: Any | None = None,
        sources: list[dict] | None = None,
    ) -> dict[str, object]:
        metadata = {
            "provider": "openrouter",
            **selection.gateway_metadata(),
        }
        if selection.level == "L2":
            metadata["web_search_tool"] = self.config.web_search_tool
            metadata["gateway_l2_sources_missing"] = not bool(sources)
        usage = self._extract_usage(response)
        if usage:
            metadata["usage"] = usage
        return metadata

    def _extract_answer_text(self, response: Any) -> str | None:
        choice = self._first_choice(response)
        if choice is None:
            return None
        message = self._get_attr_or_key(choice, "message")
        content = self._get_attr_or_key(message, "content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                item_type = self._get_attr_or_key(item, "type")
                text = self._get_attr_or_key(item, "text")
                if isinstance(text, str) and (item_type in {None, "text", "output_text"}):
                    parts.append(text)
            return "\n".join(parts)
        return None

    def _extract_usage(self, response: Any | None) -> dict[str, int] | None:
        if response is None:
            return None
        usage = self._get_attr_or_key(response, "usage")
        if usage is None:
            return None

        result: dict[str, int] = {}
        for source_key, target_key in (
            ("prompt_tokens", "input_tokens"),
            ("completion_tokens", "output_tokens"),
            ("total_tokens", "total_tokens"),
        ):
            value = self._get_attr_or_key(usage, source_key)
            if isinstance(value, int):
                result[target_key] = value
        return result or None

    def _extract_sources(self, response: Any) -> list[dict]:
        candidates: list[Any] = []
        choice = self._first_choice(response)
        message = self._get_attr_or_key(choice, "message")

        for key in ("annotations", "citations", "sources"):
            value = self._get_attr_or_key(message, key)
            if isinstance(value, list):
                candidates.extend(value)

        for key in ("annotations", "citations", "sources"):
            value = self._get_attr_or_key(response, key)
            if isinstance(value, list):
                candidates.extend(value)

        sources: list[dict] = []
        seen: set[str] = set()
        for candidate in candidates:
            source = self._normalize_source(candidate)
            if source is None:
                continue
            dedupe_key = source.get("url") or f"{source.get('title')}|{source.get('snippet')}"
            if str(dedupe_key) in seen:
                continue
            seen.add(str(dedupe_key))
            sources.append(source)
        return sources

    def _normalize_source(self, candidate: Any) -> dict | None:
        raw = self._get_attr_or_key(candidate, "url_citation") or candidate
        url = self._get_attr_or_key(raw, "url")
        if not isinstance(url, str) or not url.strip():
            return None

        title = self._get_attr_or_key(raw, "title")
        snippet = (
            self._get_attr_or_key(raw, "snippet")
            or self._get_attr_or_key(raw, "content")
            or self._get_attr_or_key(raw, "cited_text")
        )
        return {
            "url": url.strip(),
            "title": title if isinstance(title, str) else None,
            "domain": self._domain_from_url(url),
            "snippet": snippet if isinstance(snippet, str) else None,
            "source_type": "web",
            "provider_source_id": self._source_id(raw),
        }

    def _domain_from_url(self, url: str) -> str | None:
        without_scheme = url.split("://", 1)[-1]
        domain = without_scheme.split("/", 1)[0].strip().lower()
        return domain or None

    def _source_id(self, raw: Any) -> str | None:
        for key in ("id", "source_id", "provider_source_id"):
            value = self._get_attr_or_key(raw, key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _first_choice(self, response: Any) -> Any | None:
        choices = self._get_attr_or_key(response, "choices")
        if isinstance(choices, list) and choices:
            return choices[0]
        return None

    def _policy_error_to_dict(
        self,
        exc: OpenRouterModelPolicyError,
        level: str,
    ) -> dict[str, object]:
        if exc.code == ProviderErrorCode.INVALID_MODEL:
            return invalid_model_error("openrouter", level=level).to_error_dict()
        return configuration_error("openrouter", level=level).to_error_dict()

    def _status_for_error(self, error: dict[str, object]) -> str:
        code = error.get("code")
        if code == "TIMEOUT":
            return "timeout"
        if code == "RATE_LIMIT":
            return "rate_limited"
        return "error"

    def _get_attr_or_key(self, value: Any, key: str) -> Any:
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get(key)
        return getattr(value, key, None)
