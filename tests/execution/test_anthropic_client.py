from __future__ import annotations

import asyncio
import unittest

from libs.execution.anthropic_client import AnthropicClientError, AnthropicClientWrapper
from libs.execution.anthropic_config import load_anthropic_provider_config


class _FakeMessages:
    def __init__(self, response: object | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, object]] = []

    async def create(self, **payload: object) -> object:
        self.calls.append(payload)
        if self.exc is not None:
            raise self.exc
        return self.response or {"id": "msg_test"}


class _FakeClient:
    def __init__(self, messages: _FakeMessages) -> None:
        self.messages = messages


class AnthropicClientWrapperTests(unittest.IsolatedAsyncioTestCase):
    async def test_wrapper_calls_injected_client_with_payload(self) -> None:
        messages = _FakeMessages(response={"id": "msg_ok"})
        wrapper = AnthropicClientWrapper(
            config=load_anthropic_provider_config(env={}),
            client=_FakeClient(messages),
        )

        result = await wrapper.create_message(
            model="claude-test",
            max_tokens=64,
            messages=[{"role": "user", "content": "hello"}],
        )

        self.assertEqual(result, {"id": "msg_ok"})
        self.assertEqual(messages.calls[0]["model"], "claude-test")
        self.assertEqual(messages.calls[0]["max_tokens"], 64)

    async def test_missing_api_key_maps_to_safe_no_api_key_error(self) -> None:
        wrapper = AnthropicClientWrapper(config=load_anthropic_provider_config(env={}))

        with self.assertRaises(AnthropicClientError) as raised:
            await wrapper.create_message(model="claude-test", max_tokens=64, messages=[])

        error = raised.exception.error
        self.assertEqual(error["code"], "NO_API_KEY")
        self.assertEqual(error["provider"], "anthropic")
        self.assertNotIn("sk-ant", str(error))
        self.assertNotIn("ANTHROPIC_API_KEY", str(error))

    async def test_timeout_maps_to_safe_timeout_error(self) -> None:
        messages = _FakeMessages(exc=asyncio.TimeoutError("sk-ant-hidden"))
        wrapper = AnthropicClientWrapper(
            config=load_anthropic_provider_config(
                env={"ANTHROPIC_API_KEY": "sk-ant-test-secret"}
            ),
            client=_FakeClient(messages),
        )

        with self.assertRaises(AnthropicClientError) as raised:
            await wrapper.create_message(model="claude-test", max_tokens=64, messages=[])

        error = raised.exception.error
        self.assertEqual(error["code"], "TIMEOUT")
        self.assertEqual(error["provider"], "anthropic")
        serialized = str(error)
        self.assertNotIn("sk-ant-hidden", serialized)
        self.assertNotIn("authorization", serialized.lower())
        self.assertNotIn("headers", serialized.lower())
        self.assertNotIn("traceback", serialized.lower())


if __name__ == "__main__":
    unittest.main()
