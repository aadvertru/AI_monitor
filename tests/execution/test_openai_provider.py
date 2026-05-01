from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace

from libs.execution.openai_config import OpenAIProviderConfig
from libs.execution.openai_provider import OpenAIProviderAdapter


class _FakeResponsesClient:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict] = []

    async def create_response(self, **payload):
        self.calls.append(payload)
        if self.error is not None:
            raise self.error
        return self.result


class OpenAIProviderAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_l1_response_is_normalized_without_web_search_tools(self) -> None:
        response = SimpleNamespace(
            id="resp_123",
            output_text="Acme AI appears in the result.",
            usage={"input_tokens": 3, "output_tokens": 5},
            output=[
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Acme AI appears in the result.",
                            "annotations": [],
                        }
                    ],
                }
            ],
        )
        fake_client = _FakeResponsesClient(result=response)

        adapter = _adapter(fake_client)
        result = await adapter.query("best ai brand monitoring tools", scdl_level="L1")

        self.assertEqual(result.status, "success")
        self.assertEqual(result.raw_answer, "Acme AI appears in the result.")
        self.assertEqual(result.citations, [])
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.response_time)
        self.assertEqual(fake_client.calls[0]["model"], "l1-model")
        self.assertNotIn("tools", fake_client.calls[0])
        assert result.provider_metadata is not None
        self.assertEqual(result.provider_metadata["provider"], "openai")
        self.assertEqual(result.provider_metadata["model"], "l1-model")

    async def test_successful_l2_response_enables_web_search_tool(self) -> None:
        response = SimpleNamespace(
            id="resp_456",
            output=[
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {"url": "https://source.example", "title": "Source"}
                        ]
                    },
                },
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Web-enabled answer.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url": "https://citation.example",
                                    "title": "Citation",
                                }
                            ],
                        }
                    ],
                },
            ],
        )
        fake_client = _FakeResponsesClient(result=response)

        adapter = _adapter(fake_client)
        result = await adapter.query("latest visibility tools", scdl_level="L2")

        self.assertEqual(result.status, "success")
        self.assertEqual(result.raw_answer, "Web-enabled answer.")
        self.assertEqual(fake_client.calls[0]["model"], "l2-model")
        self.assertEqual(fake_client.calls[0]["tools"], [{"type": "web_search"}])
        self.assertEqual(fake_client.calls[0]["tool_choice"], "auto")
        self.assertEqual(fake_client.calls[0]["include"], ["web_search_call.action.sources"])
        self.assertEqual(
            result.citations,
            [
                {"url": "https://citation.example", "title": "Citation"},
                {"url": "https://source.example", "title": "Source"},
            ],
        )

    async def test_adapter_uses_internal_responses_client_wrapper(self) -> None:
        fake_client = _FakeResponsesClient(result=SimpleNamespace(output_text="ok"))

        adapter = _adapter(fake_client)
        await adapter.query("query", scdl_level="L1")

        self.assertEqual(len(fake_client.calls), 1)
        self.assertEqual(fake_client.calls[0]["input"], "query")

    async def test_malformed_response_returns_safe_empty_answer(self) -> None:
        fake_client = _FakeResponsesClient(result=SimpleNamespace(output=[]))

        adapter = _adapter(fake_client)
        result = await adapter.query("malformed", scdl_level="L1")

        self.assertEqual(result.status, "success")
        self.assertIsNone(result.raw_answer)
        self.assertEqual(result.citations, [])

    async def test_timeout_is_mapped_to_timeout_status_without_secret_leak(self) -> None:
        secret = "sk-test-secret"
        fake_client = _FakeResponsesClient(
            error=asyncio.TimeoutError(f"timed out with {secret}")
        )

        adapter = _adapter(fake_client, api_key=secret)
        result = await adapter.query("timeout scenario", scdl_level="L1")

        self.assertEqual(result.status, "timeout")
        assert result.error is not None
        self.assertEqual(result.error["code"], "timeout")
        self.assertNotIn(secret, result.error["message"])
        self.assertNotIn(secret, str(result.provider_metadata))

    async def test_rate_limit_error_is_mapped_without_raw_exception_message(self) -> None:
        class FakeRateLimitError(Exception):
            status_code = 429

        secret = "sk-test-secret"
        fake_client = _FakeResponsesClient(error=FakeRateLimitError(secret))

        adapter = _adapter(fake_client, api_key=secret)
        result = await adapter.query("rate limit", scdl_level="L1")

        self.assertEqual(result.status, "rate_limited")
        assert result.error is not None
        self.assertEqual(result.error["code"], "rate_limited")
        self.assertNotIn(secret, result.error["message"])

    async def test_missing_api_key_returns_error_response_without_calling_client(self) -> None:
        fake_client = _FakeResponsesClient(result=SimpleNamespace(output_text="unused"))
        adapter = _adapter(fake_client, api_key=None)

        result = await adapter.query("query without key", scdl_level="L1")

        self.assertEqual(result.status, "error")
        self.assertIsNone(result.raw_answer)
        assert result.error is not None
        self.assertEqual(result.error["code"], "missing_api_key")
        self.assertEqual(fake_client.calls, [])

    async def test_unsupported_scdl_level_returns_controlled_error(self) -> None:
        fake_client = _FakeResponsesClient(result=SimpleNamespace(output_text="unused"))

        adapter = _adapter(fake_client)
        result = await adapter.query("query", scdl_level="L3")

        self.assertEqual(result.status, "error")
        assert result.error is not None
        self.assertEqual(result.error["code"], "unsupported_scdl_level")
        self.assertEqual(fake_client.calls, [])


def _adapter(
    client: _FakeResponsesClient,
    *,
    api_key: str | None = "sk-test-key",
) -> OpenAIProviderAdapter:
    return OpenAIProviderAdapter(
        config=OpenAIProviderConfig(
            api_key=api_key,
            model_l1="l1-model",
            model_l2="l2-model",
            timeout_seconds=7,
            max_output_tokens=321,
        ),
        client=client,
    )


if __name__ == "__main__":
    unittest.main()
