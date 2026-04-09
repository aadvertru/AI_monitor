from __future__ import annotations

import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from libs.execution.openai_provider import OpenAIProviderAdapter


class _FakeCompletions:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    async def create(self, **kwargs):
        if self.error is not None:
            raise self.error
        return self.result


class _FakeClient:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions(result=result, error=error))


class OpenAIProviderAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_response_is_normalized(self) -> None:
        response = SimpleNamespace(
            id="resp_123",
            usage={"prompt_tokens": 3, "completion_tokens": 5},
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Acme AI appears in the result.",
                        citations=[{"url": "https://example.com", "title": "Example"}],
                    ),
                    finish_reason="stop",
                )
            ],
        )
        fake_client = _FakeClient(result=response)

        with patch("libs.execution.openai_provider.AsyncOpenAI", return_value=fake_client):
            adapter = OpenAIProviderAdapter(api_key="test-key")
            result = await adapter.query("best ai brand monitoring tools")

        self.assertEqual(result.status, "success")
        self.assertEqual(result.raw_answer, "Acme AI appears in the result.")
        self.assertEqual(result.citations, [{"url": "https://example.com", "title": "Example"}])
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.response_time)
        assert result.provider_metadata is not None
        self.assertEqual(result.provider_metadata["provider"], "openai")

    async def test_api_error_returns_normalized_error_response(self) -> None:
        fake_client = _FakeClient(error=Exception("API failed"))

        with patch("libs.execution.openai_provider.AsyncOpenAI", return_value=fake_client):
            adapter = OpenAIProviderAdapter(api_key="test-key")
            result = await adapter.query("how to improve visibility")

        self.assertEqual(result.status, "error")
        self.assertIsNone(result.raw_answer)
        self.assertIsNone(result.citations)
        assert result.error is not None
        self.assertEqual(result.error["code"], "provider_error")
        self.assertIn("API failed", result.error["message"])

    async def test_malformed_citations_are_normalized_or_skipped(self) -> None:
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Result with mixed citations.",
                        citations=[
                            {"url": "https://good-1.com", "title": "Good 1"},
                            {"title": "Missing URL"},
                            {"url": 123, "title": "Invalid URL type"},
                            {"url": "https://good-2.com"},
                        ],
                        annotations=[
                            {"url_citation": {"url": "https://good-3.com", "title": "Good 3"}},
                            {"url_citation": {"title": "No URL"}},
                        ],
                    ),
                    finish_reason="stop",
                )
            ],
        )
        fake_client = _FakeClient(result=response)

        with patch("libs.execution.openai_provider.AsyncOpenAI", return_value=fake_client):
            adapter = OpenAIProviderAdapter(api_key="test-key")
            result = await adapter.query("query with citations")

        self.assertEqual(
            result.citations,
            [
                {"url": "https://good-1.com", "title": "Good 1"},
                {"url": "https://good-2.com", "title": None},
                {"url": "https://good-3.com", "title": "Good 3"},
            ],
        )

    async def test_timeout_is_mapped_to_timeout_status(self) -> None:
        fake_client = _FakeClient(error=asyncio.TimeoutError("timed out"))

        with patch("libs.execution.openai_provider.AsyncOpenAI", return_value=fake_client):
            adapter = OpenAIProviderAdapter(api_key="test-key")
            result = await adapter.query("timeout scenario")

        self.assertEqual(result.status, "timeout")
        assert result.error is not None
        self.assertEqual(result.error["code"], "timeout")

    async def test_missing_api_key_returns_error_response(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch("libs.execution.openai_provider.AsyncOpenAI") as mocked_client:
                adapter = OpenAIProviderAdapter(api_key=None)
                result = await adapter.query("query without key")

        self.assertEqual(result.status, "error")
        self.assertIsNone(result.raw_answer)
        assert result.error is not None
        self.assertEqual(result.error["code"], "missing_api_key")
        mocked_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()

