from __future__ import annotations

import asyncio
import unittest

import httpx

from libs.execution.paa_config import PaaProviderConfig
from libs.execution.paa_provider import SerpApiPaaProvider, build_paa_provider


class _FakeSerpApiClient:
    def __init__(self, payload: object = None, exception: Exception | None = None) -> None:
        self.payload = payload if payload is not None else {"related_questions": []}
        self.exception = exception
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def get_json(self, endpoint_url: str, *, params: dict[str, str]) -> object:
        self.calls.append((endpoint_url, params))
        if self.exception is not None:
            raise self.exception
        return self.payload


def _config(api_key: str | None = "serp-secret") -> PaaProviderConfig:
    return PaaProviderConfig(
        enabled=True,
        provider="serpapi",
        serpapi_api_key=api_key,
        max_results=10,
        request_timeout_seconds=1.0,
    )


def _status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://serpapi.example/search")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("safe test error", request=request, response=response)


class SerpApiPaaProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_paa_extraction_with_limit_and_locale(self) -> None:
        client = _FakeSerpApiClient(
            {
                "related_questions": [
                    {"question": "What is Nike known for?", "answer": "unsafe raw"},
                    {"question": "Is Nike better than Adidas?"},
                    {"question": "Where can I buy Nike shoes?"},
                ]
            }
        )
        provider = SerpApiPaaProvider(config=_config(), client=client)

        result = await provider.get_questions("Nike", "en", "us", 2)

        self.assertEqual([question.text for question in result.questions], [
            "What is Nike known for?",
            "Is Nike better than Adidas?",
        ])
        self.assertEqual(result.questions[0].source, "paa")
        self.assertEqual(result.questions[0].provider, "serpapi")
        self.assertEqual(result.questions[0].metadata["language"], "en")
        self.assertEqual(result.questions[0].metadata["country"], "us")
        self.assertEqual(client.calls[0][1]["q"], "Nike")
        self.assertEqual(client.calls[0][1]["hl"], "en")
        self.assertEqual(client.calls[0][1]["gl"], "us")
        self.assertNotIn("unsafe raw", str(result.public_dict()))

    async def test_empty_paa_result_is_successful_empty_list(self) -> None:
        provider = SerpApiPaaProvider(
            config=_config(),
            client=_FakeSerpApiClient({"related_questions": []}),
        )

        result = await provider.get_questions("Nike", None, None, 10)

        self.assertEqual(result.questions, [])
        self.assertEqual(result.warnings, [])

    async def test_missing_api_key_returns_safe_diagnostic(self) -> None:
        provider = SerpApiPaaProvider(config=_config(api_key=None), client=_FakeSerpApiClient())

        result = await provider.get_questions("Nike", "en", "us", 10)

        self.assertEqual(result.questions, [])
        self.assertEqual(result.diagnostic["code"], "NO_API_KEY")
        self.assertNotIn("serp-secret", str(result.public_dict()))

    async def test_timeout_rate_limit_unavailable_and_request_failures_are_safe(self) -> None:
        cases = [
            (asyncio.TimeoutError(), "TIMEOUT"),
            (_status_error(429), "RATE_LIMIT"),
            (_status_error(503), "PROVIDER_UNAVAILABLE"),
            (httpx.ConnectError("network failed"), "PROVIDER_REQUEST_FAILED"),
        ]

        for exception, expected_code in cases:
            provider = SerpApiPaaProvider(
                config=_config(),
                client=_FakeSerpApiClient(exception=exception),
            )
            result = await provider.get_questions("Nike", "en", "us", 10)

            self.assertEqual(result.questions, [])
            self.assertEqual(result.diagnostic["code"], expected_code)
            self.assertIn("unavailable", result.warnings[0])
            self.assertNotIn("network failed", str(result.public_dict()))

    async def test_invalid_response_shape_and_unknown_exception_are_safe(self) -> None:
        invalid = SerpApiPaaProvider(
            config=_config(),
            client=_FakeSerpApiClient({"related_questions": {"question": "bad"}}),
        )
        invalid_result = await invalid.get_questions("Nike", "en", "us", 10)
        self.assertEqual(invalid_result.diagnostic["code"], "INVALID_RESPONSE")

        unknown = SerpApiPaaProvider(
            config=_config(),
            client=_FakeSerpApiClient(exception=RuntimeError("serp-secret leaked")),
        )
        unknown_result = await unknown.get_questions("Nike", "en", "us", 10)
        self.assertEqual(unknown_result.diagnostic["code"], "UNKNOWN_PROVIDER_ERROR")
        self.assertNotIn("serp-secret", str(unknown_result.public_dict()))

    async def test_provider_factory_builds_serpapi_provider(self) -> None:
        provider = build_paa_provider(_config())

        self.assertIsInstance(provider, SerpApiPaaProvider)
