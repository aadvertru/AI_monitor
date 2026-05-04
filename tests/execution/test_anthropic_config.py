from __future__ import annotations

import unittest

from libs.execution.anthropic_config import (
    DEFAULT_ANTHROPIC_L1_MODEL,
    DEFAULT_ANTHROPIC_MAX_OUTPUT_TOKENS,
    DEFAULT_ANTHROPIC_TIMEOUT_SECONDS,
    AnthropicConfigError,
    load_anthropic_provider_config,
)


class AnthropicProviderConfigTests(unittest.TestCase):
    def test_anthropic_api_key_can_be_loaded_from_environment(self) -> None:
        config = load_anthropic_provider_config(
            env={"ANTHROPIC_API_KEY": "sk-ant-test-secret"}
        )

        self.assertEqual(config.api_key, "sk-ant-test-secret")

    def test_missing_anthropic_api_key_fails_safely_when_required(self) -> None:
        with self.assertRaisesRegex(AnthropicConfigError, "ANTHROPIC_API_KEY"):
            load_anthropic_provider_config(env={}, require_api_key=True)

    def test_anthropic_model_and_limits_load_or_default_safely(self) -> None:
        defaults = load_anthropic_provider_config(env={})
        configured = load_anthropic_provider_config(
            env={
                "ANTHROPIC_L1_MODEL": "claude-test-model",
                "ANTHROPIC_REQUEST_TIMEOUT_SECONDS": "12.5",
                "ANTHROPIC_MAX_OUTPUT_TOKENS": "512",
            }
        )

        self.assertEqual(defaults.model_l1, DEFAULT_ANTHROPIC_L1_MODEL)
        self.assertEqual(defaults.timeout_seconds, DEFAULT_ANTHROPIC_TIMEOUT_SECONDS)
        self.assertEqual(defaults.max_output_tokens, DEFAULT_ANTHROPIC_MAX_OUTPUT_TOKENS)
        self.assertEqual(configured.model_l1, "claude-test-model")
        self.assertEqual(configured.model_for_scdl_level("L1"), "claude-test-model")
        self.assertEqual(configured.timeout_seconds, 12.5)
        self.assertEqual(configured.max_output_tokens, 512)

    def test_anthropic_model_selection_rejects_l2_until_l2_phase(self) -> None:
        config = load_anthropic_provider_config(env={})

        with self.assertRaisesRegex(AnthropicConfigError, "SCDL L1"):
            config.model_for_scdl_level("L2")

    def test_invalid_anthropic_config_fails_safely(self) -> None:
        with self.assertRaisesRegex(AnthropicConfigError, "ANTHROPIC_REQUEST_TIMEOUT_SECONDS"):
            load_anthropic_provider_config(env={"ANTHROPIC_REQUEST_TIMEOUT_SECONDS": "0"})

        with self.assertRaisesRegex(AnthropicConfigError, "ANTHROPIC_MAX_OUTPUT_TOKENS"):
            load_anthropic_provider_config(env={"ANTHROPIC_MAX_OUTPUT_TOKENS": "invalid"})

    def test_secret_is_masked_in_repr_and_safe_log_dict(self) -> None:
        secret = "sk-ant-test-secret"
        config = load_anthropic_provider_config(env={"ANTHROPIC_API_KEY": secret})

        self.assertNotIn(secret, repr(config))
        self.assertIn("***", repr(config))
        self.assertNotIn(secret, str(config.safe_log_dict()))
        self.assertEqual(config.safe_log_dict()["api_key"], "***")


if __name__ == "__main__":
    unittest.main()
