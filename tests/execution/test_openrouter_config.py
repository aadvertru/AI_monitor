from __future__ import annotations

import unittest

from libs.execution.openrouter_config import (
    DEFAULT_OPENROUTER_APP_NAME,
    DEFAULT_OPENROUTER_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENROUTER_TIMEOUT_SECONDS,
    DEFAULT_OPENROUTER_WEB_SEARCH_TOOL,
    OpenRouterConfigError,
    load_openrouter_provider_config,
)


class OpenRouterProviderConfigTests(unittest.TestCase):
    def test_openrouter_api_key_can_be_loaded_from_environment(self) -> None:
        config = load_openrouter_provider_config(
            env={"OPENROUTER_API_KEY": "sk-or-test-secret"}
        )

        self.assertEqual(config.api_key, "sk-or-test-secret")

    def test_missing_openrouter_api_key_fails_safely_when_required(self) -> None:
        with self.assertRaisesRegex(OpenRouterConfigError, "OPENROUTER_API_KEY"):
            load_openrouter_provider_config(env={}, require_api_key=True)

    def test_openrouter_models_and_limits_load_or_default_safely(self) -> None:
        defaults = load_openrouter_provider_config(env={})
        configured = load_openrouter_provider_config(
            env={
                "OPENROUTER_L1_MODEL": "anthropic/claude-test",
                "OPENROUTER_L2_MODEL": "openai/gpt-test",
                "OPENROUTER_ALLOWED_MODELS": " anthropic/claude-test, openai/gpt-test ",
                "OPENROUTER_REQUEST_TIMEOUT_SECONDS": "12.5",
                "OPENROUTER_MAX_OUTPUT_TOKENS": "512",
            }
        )

        self.assertIsNone(defaults.model_l1)
        self.assertIsNone(defaults.model_l2)
        self.assertEqual(defaults.timeout_seconds, DEFAULT_OPENROUTER_TIMEOUT_SECONDS)
        self.assertEqual(defaults.max_output_tokens, DEFAULT_OPENROUTER_MAX_OUTPUT_TOKENS)
        self.assertEqual(configured.model_for_scdl_level("L1"), "anthropic/claude-test")
        self.assertEqual(configured.model_for_scdl_level("L2"), "openai/gpt-test")
        self.assertEqual(
            configured.allowed_models,
            ("anthropic/claude-test", "openai/gpt-test"),
        )
        self.assertEqual(configured.timeout_seconds, 12.5)
        self.assertEqual(configured.max_output_tokens, 512)

    def test_web_search_and_optional_headers_load_safely(self) -> None:
        config = load_openrouter_provider_config(
            env={
                "OPENROUTER_WEB_SEARCH_ENABLED": "true",
                "OPENROUTER_WEB_SEARCH_TOOL": "openrouter:web_search",
                "OPENROUTER_SITE_URL": "https://example.com",
                "OPENROUTER_APP_NAME": "Test App",
            }
        )

        self.assertTrue(config.web_search_enabled)
        self.assertEqual(config.web_search_tool, DEFAULT_OPENROUTER_WEB_SEARCH_TOOL)
        self.assertEqual(config.optional_headers()["HTTP-Referer"], "https://example.com")
        self.assertEqual(config.optional_headers()["X-OpenRouter-Title"], "Test App")

    def test_default_optional_headers_do_not_break_wrapper(self) -> None:
        config = load_openrouter_provider_config(env={})

        self.assertEqual(config.app_name, DEFAULT_OPENROUTER_APP_NAME)
        self.assertNotIn("HTTP-Referer", config.optional_headers())
        self.assertEqual(
            config.optional_headers()["X-OpenRouter-Title"],
            DEFAULT_OPENROUTER_APP_NAME,
        )

    def test_invalid_openrouter_config_fails_safely(self) -> None:
        with self.assertRaisesRegex(OpenRouterConfigError, "OPENROUTER_REQUEST_TIMEOUT"):
            load_openrouter_provider_config(env={"OPENROUTER_REQUEST_TIMEOUT_SECONDS": "0"})

        with self.assertRaisesRegex(OpenRouterConfigError, "OPENROUTER_MAX_OUTPUT"):
            load_openrouter_provider_config(env={"OPENROUTER_MAX_OUTPUT_TOKENS": "invalid"})

        with self.assertRaisesRegex(OpenRouterConfigError, "OPENROUTER_WEB_SEARCH_ENABLED"):
            load_openrouter_provider_config(env={"OPENROUTER_WEB_SEARCH_ENABLED": "maybe"})

    def test_secret_is_masked_in_repr_and_safe_log_dict(self) -> None:
        secret = "sk-or-test-secret"
        config = load_openrouter_provider_config(env={"OPENROUTER_API_KEY": secret})

        self.assertNotIn(secret, repr(config))
        self.assertIn("***", repr(config))
        self.assertNotIn(secret, str(config.safe_log_dict()))
        self.assertEqual(config.safe_log_dict()["api_key"], "***")


if __name__ == "__main__":
    unittest.main()
