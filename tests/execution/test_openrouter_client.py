from __future__ import annotations

import asyncio
import unittest

import httpx

from libs.execution.openrouter_client import OpenRouterClientError, OpenRouterClientWrapper
from libs.execution.openrouter_config import load_openrouter_provider_config


class _FakeOpenRouterClient:
    def __init__(self, response: object | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, object]] = []

    async def create_chat_completion(self, **payload: object) -> object:
        self.calls.append(payload)
        if self.exc is not None:
            raise self.exc
        return self.response or {"id": "chatcmpl_test"}


class OpenRouterClientWrapperTests(unittest.IsolatedAsyncioTestCase):
    async def test_wrapper_calls_injected_client_with_payload_without_api_key(self) -> None:
        client = _FakeOpenRouterClient(response={"id": "chatcmpl_ok"})
        wrapper = OpenRouterClientWrapper(
            config=load_openrouter_provider_config(env={}),
            client=client,
        )

        result = await wrapper.create_chat_completion(
            model="anthropic/claude-test",
            max_tokens=64,
            messages=[{"role": "user", "content": "hello"}],
            _scdl_level="L1",
        )

        self.assertEqual(result, {"id": "chatcmpl_ok"})
        self.assertEqual(client.calls[0]["model"], "anthropic/claude-test")
        self.assertEqual(client.calls[0]["max_tokens"], 64)
        self.assertNotIn("_scdl_level", client.calls[0])

    async def test_missing_api_key_maps_to_safe_no_api_key_error(self) -> None:
        wrapper = OpenRouterClientWrapper(config=load_openrouter_provider_config(env={}))

        with self.assertRaises(OpenRouterClientError) as raised:
            await wrapper.create_chat_completion(
                model="anthropic/claude-test",
                max_tokens=64,
                messages=[],
                _scdl_level="L1",
            )

        error = raised.exception.error
        self.assertEqual(error["code"], "NO_API_KEY")
        self.assertEqual(error["provider"], "openrouter")
        self.assertNotIn("sk-or", str(error))
        self.assertNotIn("OPENROUTER_API_KEY", str(error))

    async def test_timeout_maps_to_safe_timeout_error(self) -> None:
        client = _FakeOpenRouterClient(exc=asyncio.TimeoutError("sk-or-hidden"))
        wrapper = OpenRouterClientWrapper(
            config=load_openrouter_provider_config(
                env={"OPENROUTER_API_KEY": "sk-or-test-secret"}
            ),
            client=client,
        )

        with self.assertRaises(OpenRouterClientError) as raised:
            await wrapper.create_chat_completion(
                model="anthropic/claude-test",
                max_tokens=64,
                messages=[],
                _scdl_level="L1",
            )

        error = raised.exception.error
        self.assertEqual(error["code"], "TIMEOUT")
        self.assertEqual(error["provider"], "openrouter")
        serialized = str(error)
        self.assertNotIn("sk-or-hidden", serialized)
        self.assertNotIn("authorization", serialized.lower())
        self.assertNotIn("headers", serialized.lower())
        self.assertNotIn("traceback", serialized.lower())

    async def test_network_error_maps_to_provider_request_failed(self) -> None:
        client = _FakeOpenRouterClient(exc=httpx.ConnectError("sk-or-hidden"))
        wrapper = OpenRouterClientWrapper(
            config=load_openrouter_provider_config(
                env={"OPENROUTER_API_KEY": "sk-or-test-secret"}
            ),
            client=client,
        )

        with self.assertRaises(OpenRouterClientError) as raised:
            await wrapper.create_chat_completion(
                model="anthropic/claude-test",
                max_tokens=64,
                messages=[],
                _scdl_level="L2",
            )

        error = raised.exception.error
        self.assertEqual(error["code"], "PROVIDER_REQUEST_FAILED")
        self.assertEqual(error["level"], "L2")
        self.assertNotIn("sk-or-hidden", str(error))

    def test_http_status_errors_preserve_scdl_level(self) -> None:
        wrapper = OpenRouterClientWrapper(
            config=load_openrouter_provider_config(
                env={"OPENROUTER_API_KEY": "sk-or-test-secret"}
            )
        )

        error = wrapper._error_for_status(
            401,
            {"model": "anthropic/claude-test"},
            level="L2",
        )

        self.assertEqual(error["code"], "INVALID_API_KEY")
        self.assertEqual(error["level"], "L2")


if __name__ == "__main__":
    unittest.main()
