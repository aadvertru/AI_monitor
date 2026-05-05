from __future__ import annotations

import unittest

from libs.execution.openrouter_config import load_openrouter_provider_config
from libs.execution.openrouter_provider import OpenRouterProviderAdapter


class _FakeOpenRouterClient:
    def __init__(self, response: object | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, object]] = []

    async def create_chat_completion(self, **payload: object) -> object:
        self.calls.append(payload)
        if self.exc is not None:
            raise self.exc
        return self.response


def _config(extra: dict[str, str] | None = None):
    env = {
        "OPENROUTER_API_KEY": "sk-or-test-secret",
        "OPENROUTER_L1_MODEL": "anthropic/claude-test",
        "OPENROUTER_ALLOWED_MODELS": "anthropic/claude-test",
    }
    if extra:
        env.update(extra)
    return load_openrouter_provider_config(env=env)


class OpenRouterProviderAdapterL1Tests(unittest.IsolatedAsyncioTestCase):
    async def test_l1_success_normalizes_answer_usage_and_gateway_metadata(self) -> None:
        client = _FakeOpenRouterClient(
            response={
                "choices": [{"message": {"content": "  answer text  "}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            }
        )
        adapter = OpenRouterProviderAdapter(config=_config(), client=client)

        response = await adapter.query("Who recommends Nike?", scdl_level="L1")

        self.assertEqual(response.status, "success")
        self.assertEqual(response.raw_answer, "answer text")
        self.assertEqual(response.citations, [])
        assert response.provider_metadata is not None
        self.assertEqual(response.provider_metadata["execution_provider"], "openrouter")
        self.assertEqual(response.provider_metadata["model_id"], "anthropic/claude-test")
        self.assertEqual(response.provider_metadata["model_provider"], "anthropic")
        self.assertTrue(response.provider_metadata["gateway"])
        self.assertFalse(response.provider_metadata["gateway_l2_experimental"])
        self.assertEqual(response.provider_metadata["level"], "L1")
        self.assertEqual(response.provider_metadata["usage"]["input_tokens"], 10)

    async def test_l1_request_does_not_include_web_search_or_tools(self) -> None:
        client = _FakeOpenRouterClient(
            response={"choices": [{"message": {"content": "answer"}}]}
        )
        adapter = OpenRouterProviderAdapter(config=_config(), client=client)

        await adapter.query("query", scdl_level="L1")

        payload = client.calls[0]
        self.assertEqual(payload["model"], "anthropic/claude-test")
        self.assertEqual(payload["max_tokens"], 1200)
        self.assertNotIn("tools", payload)
        self.assertNotIn("tool_choice", payload)
        self.assertNotIn("plugins", payload)
        self.assertNotIn(":online", str(payload))

    async def test_unknown_scdl_level_returns_configuration_error_and_does_not_call_client(
        self,
    ) -> None:
        client = _FakeOpenRouterClient()
        adapter = OpenRouterProviderAdapter(config=_config(), client=client)

        response = await adapter.query("query", scdl_level="L3")

        self.assertEqual(response.status, "error")
        assert response.error is not None
        self.assertEqual(response.error["code"], "CONFIGURATION_ERROR")
        self.assertEqual(client.calls, [])

    async def test_l2_success_uses_web_search_tool_and_normalizes_sources(self) -> None:
        client = _FakeOpenRouterClient(
            response={
                "choices": [
                    {
                        "message": {
                            "content": "answer with sources",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url_citation": {
                                        "url": "https://example.com/page",
                                        "title": "Example",
                                        "content": "snippet",
                                    },
                                },
                                {
                                    "url": "https://example.com/page",
                                    "title": "Duplicate",
                                },
                            ],
                        }
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            }
        )
        adapter = OpenRouterProviderAdapter(
            config=_config(
                {
                    "OPENROUTER_L2_MODEL": "anthropic/claude-test",
                    "OPENROUTER_WEB_SEARCH_ENABLED": "true",
                }
            ),
            client=client,
        )

        response = await adapter.query("latest Nike visibility", scdl_level="L2")

        self.assertEqual(response.status, "success")
        self.assertEqual(response.raw_answer, "answer with sources")
        self.assertEqual(len(response.citations or []), 1)
        self.assertEqual(response.citations[0]["domain"], "example.com")
        payload = client.calls[0]
        self.assertEqual(payload["tools"], [{"type": "openrouter:web_search"}])
        self.assertNotIn(":online", str(payload))
        self.assertNotIn("plugins", payload)
        assert response.provider_metadata is not None
        self.assertTrue(response.provider_metadata["gateway_l2_experimental"])
        self.assertEqual(response.provider_metadata["web_search_tool"], "openrouter:web_search")
        self.assertFalse(response.provider_metadata["gateway_l2_sources_missing"])

    async def test_l2_success_without_sources_is_allowed_and_marked(self) -> None:
        client = _FakeOpenRouterClient(
            response={"choices": [{"message": {"content": "answer without sources"}}]}
        )
        adapter = OpenRouterProviderAdapter(
            config=_config(
                {
                    "OPENROUTER_L2_MODEL": "anthropic/claude-test",
                    "OPENROUTER_WEB_SEARCH_ENABLED": "true",
                }
            ),
            client=client,
        )

        response = await adapter.query("query", scdl_level="L2")

        self.assertEqual(response.status, "success")
        self.assertEqual(response.citations, [])
        assert response.provider_metadata is not None
        self.assertTrue(response.provider_metadata["gateway_l2_sources_missing"])

    async def test_l2_web_search_disabled_or_missing_model_prevents_client_call(self) -> None:
        disabled_client = _FakeOpenRouterClient()
        disabled = OpenRouterProviderAdapter(
            config=_config({"OPENROUTER_L2_MODEL": "anthropic/claude-test"}),
            client=disabled_client,
        )
        missing_model_client = _FakeOpenRouterClient()
        missing_model = OpenRouterProviderAdapter(
            config=_config({"OPENROUTER_WEB_SEARCH_ENABLED": "true"}),
            client=missing_model_client,
        )

        disabled_response = await disabled.query("query", scdl_level="L2")
        missing_model_response = await missing_model.query("query", scdl_level="L2")

        assert disabled_response.error is not None
        assert missing_model_response.error is not None
        self.assertEqual(disabled_response.error["code"], "CONFIGURATION_ERROR")
        self.assertEqual(missing_model_response.error["code"], "CONFIGURATION_ERROR")
        self.assertEqual(disabled_client.calls, [])
        self.assertEqual(missing_model_client.calls, [])

    async def test_missing_key_and_missing_model_are_safe_errors(self) -> None:
        missing_key = OpenRouterProviderAdapter(
            config=_config({"OPENROUTER_API_KEY": ""}),
            client=None,
        )

        response = await missing_key.query("query", scdl_level="L1")

        assert response.error is not None
        self.assertEqual(response.error["code"], "NO_API_KEY")
        self.assertNotIn("sk-or", str(response.error))

        missing_model = OpenRouterProviderAdapter(
            config=load_openrouter_provider_config(
                env={
                    "OPENROUTER_API_KEY": "sk-or-test-secret",
                    "OPENROUTER_ALLOWED_MODELS": "anthropic/claude-test",
                }
            ),
            client=_FakeOpenRouterClient(),
        )

        response = await missing_model.query("query", scdl_level="L1")

        assert response.error is not None
        self.assertEqual(response.error["code"], "CONFIGURATION_ERROR")

    async def test_not_allowlisted_model_prevents_client_call(self) -> None:
        client = _FakeOpenRouterClient()
        adapter = OpenRouterProviderAdapter(
            config=_config({"OPENROUTER_ALLOWED_MODELS": "openai/gpt-test"}),
            client=client,
        )

        response = await adapter.query("query", scdl_level="L1")

        assert response.error is not None
        self.assertEqual(response.error["code"], "INVALID_MODEL")
        self.assertEqual(client.calls, [])

    async def test_empty_and_invalid_responses_are_normalized(self) -> None:
        empty = OpenRouterProviderAdapter(
            config=_config(),
            client=_FakeOpenRouterClient(
                response={"choices": [{"message": {"content": "   "}}]}
            ),
        )
        invalid = OpenRouterProviderAdapter(
            config=_config(),
            client=_FakeOpenRouterClient(response={"choices": []}),
        )

        empty_response = await empty.query("query", scdl_level="L1")
        invalid_response = await invalid.query("query", scdl_level="L1")

        assert empty_response.error is not None
        assert invalid_response.error is not None
        self.assertEqual(empty_response.error["code"], "EMPTY_RESPONSE")
        self.assertEqual(invalid_response.error["code"], "INVALID_RESPONSE")

    async def test_client_errors_and_unknown_exceptions_are_normalized_safely(self) -> None:
        from libs.execution.openrouter_client import OpenRouterClientError
        from libs.execution.provider_errors import rate_limit_error

        rate_limited = OpenRouterProviderAdapter(
            config=_config(),
            client=_FakeOpenRouterClient(
                exc=OpenRouterClientError(
                    rate_limit_error(
                        "openrouter",
                        "anthropic/claude-test",
                        "L1",
                    ).to_error_dict()
                )
            ),
        )
        unknown = OpenRouterProviderAdapter(
            config=_config(),
            client=_FakeOpenRouterClient(exc=RuntimeError("sk-or-hidden")),
        )

        rate_response = await rate_limited.query("query", scdl_level="L1")
        with self.assertLogs("libs.execution.openrouter_provider", level="WARNING") as logs:
            unknown_response = await unknown.query("query", scdl_level="L1")

        self.assertEqual(rate_response.status, "rate_limited")
        assert rate_response.error is not None
        self.assertEqual(rate_response.error["code"], "RATE_LIMIT")
        assert unknown_response.error is not None
        self.assertEqual(unknown_response.error["code"], "UNKNOWN_PROVIDER_ERROR")
        self.assertIn("openrouter_query_unexpected_error", "\n".join(logs.output))
        self.assertNotIn("sk-or-hidden", "\n".join(logs.output))
        serialized = f"{rate_response.error} {unknown_response.error}"
        self.assertNotIn("sk-or-hidden", serialized)
        self.assertNotIn("authorization", serialized.lower())
        self.assertNotIn("headers", serialized.lower())
        self.assertNotIn("traceback", serialized.lower())


if __name__ == "__main__":
    unittest.main()
