from __future__ import annotations

import unittest

from libs.execution.openai_config import (
    DEFAULT_OPENAI_L1_MODEL,
    DEFAULT_OPENAI_L2_MODEL,
    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_TIMEOUT_SECONDS,
    OpenAIConfigError,
    load_openai_provider_config,
    validate_openai_config_for_pilot,
)
from libs.execution.pilot_config import load_real_provider_pilot_config


class OpenAIProviderConfigTests(unittest.TestCase):
    def test_openai_api_key_can_be_loaded_from_environment(self) -> None:
        config = load_openai_provider_config(env={"OPENAI_API_KEY": "sk-test-secret"})

        self.assertEqual(config.api_key, "sk-test-secret")

    def test_missing_openai_api_key_fails_safely_when_openai_mode_is_enabled(self) -> None:
        pilot_config = load_real_provider_pilot_config(
            env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
        )

        with self.assertRaisesRegex(OpenAIConfigError, "OPENAI_API_KEY"):
            validate_openai_config_for_pilot(pilot_config, env={})

    def test_missing_openai_api_key_does_not_affect_mock_provider_mode(self) -> None:
        pilot_config = load_real_provider_pilot_config(env={})

        config = validate_openai_config_for_pilot(pilot_config, env={})

        self.assertIsNone(config.api_key)

    def test_openai_model_config_is_loaded(self) -> None:
        config = load_openai_provider_config(
            env={
                "OPENAI_L1_MODEL": "l1-test-model",
                "OPENAI_L2_MODEL": "l2-test-model",
            }
        )

        self.assertEqual(config.model_l1, "l1-test-model")
        self.assertEqual(config.model_l2, "l2-test-model")
        self.assertEqual(config.model_for_scdl_level("L1"), "l1-test-model")
        self.assertEqual(config.model_for_scdl_level("L2"), "l2-test-model")

    def test_timeout_and_response_limit_config_load_or_default_safely(self) -> None:
        defaults = load_openai_provider_config(env={})
        configured = load_openai_provider_config(
            env={
                "OPENAI_REQUEST_TIMEOUT_SECONDS": "12.5",
                "OPENAI_MAX_OUTPUT_TOKENS": "512",
            }
        )

        self.assertEqual(defaults.timeout_seconds, DEFAULT_OPENAI_TIMEOUT_SECONDS)
        self.assertEqual(defaults.max_output_tokens, DEFAULT_OPENAI_MAX_OUTPUT_TOKENS)
        self.assertEqual(defaults.model_l1, DEFAULT_OPENAI_L1_MODEL)
        self.assertEqual(defaults.model_l2, DEFAULT_OPENAI_L2_MODEL)
        self.assertEqual(configured.timeout_seconds, 12.5)
        self.assertEqual(configured.max_output_tokens, 512)

    def test_invalid_required_openai_config_fails_safely(self) -> None:
        with self.assertRaisesRegex(OpenAIConfigError, "OPENAI_REQUEST_TIMEOUT_SECONDS"):
            load_openai_provider_config(env={"OPENAI_REQUEST_TIMEOUT_SECONDS": "0"})

        with self.assertRaisesRegex(OpenAIConfigError, "OPENAI_MAX_OUTPUT_TOKENS"):
            load_openai_provider_config(env={"OPENAI_MAX_OUTPUT_TOKENS": "invalid"})

    def test_secret_is_masked_in_repr_and_safe_log_dict(self) -> None:
        secret = "sk-test-secret"
        config = load_openai_provider_config(env={"OPENAI_API_KEY": secret})

        self.assertNotIn(secret, repr(config))
        self.assertIn("***", repr(config))
        self.assertNotIn(secret, str(config.safe_log_dict()))
        self.assertEqual(config.safe_log_dict()["api_key"], "***")

    def test_task_does_not_configure_real_openai_api_calls(self) -> None:
        config = load_openai_provider_config(env={})

        self.assertIsNone(config.api_key)


if __name__ == "__main__":
    unittest.main()
