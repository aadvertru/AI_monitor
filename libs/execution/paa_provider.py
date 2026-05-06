"""People Also Ask provider abstraction and deterministic mock provider."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from libs.execution.paa_config import PaaProviderConfig
from libs.execution.provider_errors import (
    ProviderErrorCode,
    invalid_response_error,
    no_api_key_error,
    normalize_provider_error_dict,
    provider_disabled_error,
    provider_request_failed_error,
    rate_limit_error,
    timeout_error,
    unknown_provider_error,
)

PAA_SOURCE = "paa"
SERPAPI_SEARCH_ENDPOINT = "https://serpapi.com/search.json"


@dataclass(frozen=True)
class PeopleAlsoAskQuestion:
    text: str
    source: str = PAA_SOURCE
    provider: str = "mock"
    metadata: dict[str, object] = field(default_factory=dict)

    def public_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "source": self.source,
            "provider": self.provider,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PeopleAlsoAskResult:
    questions: list[PeopleAlsoAskQuestion] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    diagnostic: dict[str, object] | None = None

    def public_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "questions": [question.public_dict() for question in self.questions],
            "warnings": list(self.warnings),
        }
        if self.diagnostic is not None:
            payload["diagnostic"] = self.diagnostic
        return payload


class PeopleAlsoAskProvider(Protocol):
    async def get_questions(
        self,
        query: str,
        language: str | None,
        country: str | None,
        limit: int,
    ) -> PeopleAlsoAskResult:
        """Return normalized People Also Ask questions."""


class DisabledPaaProvider:
    provider = "disabled"

    async def get_questions(
        self,
        query: str,
        language: str | None,
        country: str | None,
        limit: int,
    ) -> PeopleAlsoAskResult:
        diagnostic = provider_disabled_error("paa").to_error_dict()
        return PeopleAlsoAskResult(
            warnings=["People Also Ask enrichment is currently disabled."],
            diagnostic=diagnostic,
        )


class MockPaaProvider:
    provider = "mock"

    async def get_questions(
        self,
        query: str,
        language: str | None,
        country: str | None,
        limit: int,
    ) -> PeopleAlsoAskResult:
        normalized_query = query.strip() or "this brand"
        questions = [
            PeopleAlsoAskQuestion(
                text=f"What is {normalized_query} known for?",
                provider=self.provider,
                metadata=_metadata(language=language, country=country),
            ),
            PeopleAlsoAskQuestion(
                text=f"How does {normalized_query} compare with alternatives?",
                provider=self.provider,
                metadata=_metadata(language=language, country=country),
            ),
            PeopleAlsoAskQuestion(
                text=f"What are common questions about {normalized_query}?",
                provider=self.provider,
                metadata=_metadata(language=language, country=country),
            ),
        ]
        return PeopleAlsoAskResult(questions=questions[: max(limit, 0)])


def build_paa_provider(config: PaaProviderConfig) -> PeopleAlsoAskProvider:
    if not config.enabled:
        return DisabledPaaProvider()
    if config.provider == "mock":
        return MockPaaProvider()
    if config.provider == "serpapi":
        return SerpApiPaaProvider(config=config)
    return UnknownPaaProvider(config.provider)


class UnknownPaaProvider:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    async def get_questions(
        self,
        query: str,
        language: str | None,
        country: str | None,
        limit: int,
    ) -> PeopleAlsoAskResult:
        diagnostic = normalize_provider_error_dict(
            {"code": ProviderErrorCode.CONFIGURATION_ERROR.value},
            provider=self.provider,
            fallback_code=ProviderErrorCode.CONFIGURATION_ERROR,
        )
        return PeopleAlsoAskResult(
            warnings=["People Also Ask provider is not configured."],
            diagnostic=diagnostic,
        )


def _metadata(language: str | None, country: str | None) -> dict[str, object]:
    metadata: dict[str, object] = {"paa_provider": "mock"}
    if language:
        metadata["language"] = language
    if country:
        metadata["country"] = country
    return metadata


class SerpApiPaaProvider:
    provider = "serpapi"

    def __init__(
        self,
        *,
        config: PaaProviderConfig,
        client: object | None = None,
        endpoint_url: str = SERPAPI_SEARCH_ENDPOINT,
    ) -> None:
        self.config = config
        self._client = client
        self.endpoint_url = endpoint_url

    async def get_questions(
        self,
        query: str,
        language: str | None,
        country: str | None,
        limit: int,
    ) -> PeopleAlsoAskResult:
        if not self.config.serpapi_api_key:
            return PeopleAlsoAskResult(
                warnings=["People Also Ask provider API key is not configured."],
                diagnostic=no_api_key_error(self.provider).to_error_dict(),
            )

        language_value = (language or self.config.serpapi_default_language).lower()
        country_value = (country or self.config.serpapi_default_country).lower()
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.config.serpapi_api_key,
            "hl": language_value,
            "gl": country_value,
        }

        try:
            payload = await self._get_json(params)
        except (asyncio.TimeoutError, httpx.TimeoutException):
            return _error_result(timeout_error(self.provider).to_error_dict())
        except httpx.HTTPStatusError as exc:
            return _error_result(_error_for_http_status(exc.response.status_code))
        except httpx.HTTPError:
            return _error_result(provider_request_failed_error(self.provider).to_error_dict())
        except Exception:
            return _error_result(unknown_provider_error(self.provider).to_error_dict())

        if not isinstance(payload, dict):
            return _error_result(invalid_response_error(self.provider).to_error_dict())

        raw_questions = payload.get("related_questions") or payload.get("people_also_ask")
        if raw_questions is None:
            raw_questions = []
        if not isinstance(raw_questions, list):
            return _error_result(invalid_response_error(self.provider).to_error_dict())

        questions: list[PeopleAlsoAskQuestion] = []
        for item in raw_questions:
            text = _question_text(item)
            if not text:
                continue
            questions.append(
                PeopleAlsoAskQuestion(
                    text=text,
                    provider=self.provider,
                    metadata={
                        "paa_provider": self.provider,
                        "language": language_value,
                        "country": country_value,
                    },
                )
            )
            if len(questions) >= max(limit, 0):
                break
        return PeopleAlsoAskResult(questions=questions)

    async def _get_json(self, params: dict[str, str]) -> object:
        if self._client is not None:
            return await self._client.get_json(self.endpoint_url, params=params)
        async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
            response = await client.get(self.endpoint_url, params=params)
            response.raise_for_status()
            return response.json()


def _question_text(item: object) -> str | None:
    if isinstance(item, str):
        value = item
    elif isinstance(item, dict):
        value = str(item.get("question") or item.get("title") or "").strip()
    else:
        return None
    text = value.strip()
    return text or None


def _error_for_http_status(status_code: int) -> dict[str, object]:
    if status_code == 429:
        return rate_limit_error("serpapi").to_error_dict()
    if status_code in {401, 403}:
        return no_api_key_error("serpapi").to_error_dict()
    if status_code >= 500:
        return normalize_provider_error_dict(
            {"code": ProviderErrorCode.PROVIDER_UNAVAILABLE.value},
            provider="serpapi",
            fallback_code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
        )
    return provider_request_failed_error("serpapi").to_error_dict()


def _error_result(error: dict[str, object]) -> PeopleAlsoAskResult:
    normalized = normalize_provider_error_dict(error, provider="serpapi")
    return PeopleAlsoAskResult(
        warnings=["People Also Ask enrichment is currently unavailable."],
        diagnostic=normalized,
    )
