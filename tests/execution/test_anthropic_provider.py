from __future__ import annotations

import asyncio
import unittest
from dataclasses import dataclass
from typing import Any

from libs.execution.anthropic_config import load_anthropic_provider_config
from libs.execution.anthropic_provider import AnthropicProviderAdapter


@dataclass
class _Usage:
    input_tokens: int
    output_tokens: int


class _FakeAnthropicClient:
    def __init__(self, response: object | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, Any]] = []

    async def create_message(self, **payload: Any) -> object:
        self.calls.append(payload)
        if self.exc is not None:
            raise self.exc
        return self.response or {
            "id": "msg_test",
            "content": [{"type": "text", "text": "Claude answer"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn",
        }


class _StatusError(Exception):
    def __init__(self, status_code: int, message: str = "provider failed with sk-ant") -> None:
        super().__init__(message)
        self.status_code = status_code


class AnthropicProviderAdapterTests(unittest.IsolatedAsyncioTestCase):
    def _adapter(
        self,
        client: _FakeAnthropicClient,
        *,
        api_key: str | None = "sk-ant-test-secret",
    ) -> AnthropicProviderAdapter:
        return AnthropicProviderAdapter(
            config=load_anthropic_provider_config(
                env={"ANTHROPIC_API_KEY": api_key or ""}
            ),
            client=client,
        )

    async def test_claude_l1_success_returns_normalized_provider_response(self) -> None:
        response = {
            "id": "msg_ok",
            "content": [
                {"type": "text", "text": "First block."},
                {"type": "text", "text": "Second block."},
                {"type": "tool_use", "text": "ignored"},
            ],
            "usage": _Usage(input_tokens=12, output_tokens=8),
            "stop_reason": "end_turn",
        }
        client = _FakeAnthropicClient(response=response)
        adapter = self._adapter(client)

        result = await adapter.query("audit query", scdl_level="L1")

        self.assertEqual(result.status, "success")
        self.assertEqual(result.raw_answer, "First block.\nSecond block.")
        self.assertEqual(result.citations, [])
        self.assertIsNotNone(result.response_time)
        self.assertEqual(client.calls[0]["model"], "claude-3-5-haiku-latest")
        self.assertEqual(client.calls[0]["max_tokens"], 1200)
        self.assertNotIn("tools", client.calls[0])
        assert result.provider_metadata is not None
        self.assertEqual(result.provider_metadata["provider"], "anthropic")
        self.assertEqual(result.provider_metadata["usage"]["total_tokens"], 20)

    async def test_claude_l2_returns_unsupported_without_client_call(self) -> None:
        client = _FakeAnthropicClient()
        adapter = self._adapter(client)

        result = await adapter.query("audit query", scdl_level="L2")

        self.assertEqual(result.status, "error")
        self.assertEqual(result.error["code"], "UNSUPPORTED_L2")
        self.assertEqual(client.calls, [])

    async def test_missing_key_returns_safe_no_api_key_error(self) -> None:
        adapter = AnthropicProviderAdapter(config=load_anthropic_provider_config(env={}))

        result = await adapter.query("audit query", scdl_level="L1")

        self.assertEqual(result.status, "error")
        self.assertEqual(result.error["code"], "NO_API_KEY")
        self.assertNotIn("ANTHROPIC_API_KEY", str(result.error))

    async def test_empty_text_maps_to_empty_response(self) -> None:
        adapter = self._adapter(
            _FakeAnthropicClient(response={"content": [{"type": "text", "text": "  "}]})
        )

        result = await adapter.query("audit query", scdl_level="L1")

        self.assertEqual(result.status, "error")
        self.assertEqual(result.error["code"], "EMPTY_RESPONSE")

    async def test_invalid_response_shape_maps_to_invalid_response(self) -> None:
        adapter = self._adapter(_FakeAnthropicClient(response={"content": []}))

        result = await adapter.query("audit query", scdl_level="L1")

        self.assertEqual(result.status, "error")
        self.assertEqual(result.error["code"], "INVALID_RESPONSE")

    async def test_timeout_and_rate_limit_are_normalized(self) -> None:
        timeout_result = await self._adapter(
            _FakeAnthropicClient(exc=asyncio.TimeoutError("sk-ant-hidden"))
        ).query("audit query", scdl_level="L1")
        rate_limit_result = await self._adapter(
            _FakeAnthropicClient(exc=_StatusError(429))
        ).query("audit query", scdl_level="L1")

        self.assertEqual(timeout_result.status, "timeout")
        self.assertEqual(timeout_result.error["code"], "TIMEOUT")
        self.assertEqual(rate_limit_result.status, "rate_limited")
        self.assertEqual(rate_limit_result.error["code"], "RATE_LIMIT")

    async def test_auth_model_and_generic_errors_are_normalized_safely(self) -> None:
        invalid_key = await self._adapter(_FakeAnthropicClient(exc=_StatusError(401))).query(
            "audit query",
            scdl_level="L1",
        )
        invalid_model = await self._adapter(_FakeAnthropicClient(exc=_StatusError(400))).query(
            "audit query",
            scdl_level="L1",
        )
        unknown = await self._adapter(
            _FakeAnthropicClient(exc=RuntimeError("provider exploded with sk-ant-hidden"))
        ).query("audit query", scdl_level="L1")

        self.assertEqual(invalid_key.error["code"], "INVALID_API_KEY")
        self.assertEqual(invalid_model.error["code"], "INVALID_MODEL")
        self.assertEqual(unknown.error["code"], "UNKNOWN_PROVIDER_ERROR")
        serialized = f"{invalid_key.error} {invalid_model.error} {unknown.error}"
        self.assertNotIn("sk-ant-hidden", serialized)
        self.assertNotIn("headers", serialized.lower())
        self.assertNotIn("traceback", serialized.lower())


if __name__ == "__main__":
    unittest.main()
