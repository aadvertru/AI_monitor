from __future__ import annotations

import unittest

from libs.execution.openrouter_config import load_openrouter_provider_config
from libs.execution.openrouter_model_policy import (
    OpenRouterModelPolicyError,
    derive_openrouter_model_provider,
    select_openrouter_model,
    validate_openrouter_model_id,
)


class OpenRouterModelPolicyTests(unittest.TestCase):
    def test_comma_separated_allowlist_accepts_l1_and_l2_models(self) -> None:
        config = load_openrouter_provider_config(
            env={
                "OPENROUTER_L1_MODEL": "anthropic/claude-3-5-sonnet",
                "OPENROUTER_L2_MODEL": "google/gemini-2.0-flash",
                "OPENROUTER_ALLOWED_MODELS": (
                    " anthropic/claude-3-5-sonnet, google/gemini-2.0-flash ,, "
                ),
            }
        )

        l1 = select_openrouter_model("L1", config)
        l2 = select_openrouter_model("L2", config)

        self.assertEqual(l1.model_id, "anthropic/claude-3-5-sonnet")
        self.assertEqual(l1.model_provider, "anthropic")
        self.assertFalse(l1.gateway_metadata()["gateway_l2_experimental"])
        self.assertEqual(l2.model_provider, "google")
        self.assertTrue(l2.gateway_metadata()["gateway_l2_experimental"])

    def test_missing_or_empty_allowlist_is_configuration_error(self) -> None:
        config = load_openrouter_provider_config(
            env={"OPENROUTER_L1_MODEL": "anthropic/claude-test"}
        )

        with self.assertRaises(OpenRouterModelPolicyError) as raised:
            select_openrouter_model("L1", config)

        self.assertEqual(raised.exception.code, "CONFIGURATION_ERROR")

    def test_missing_l1_or_l2_model_is_configuration_error(self) -> None:
        config = load_openrouter_provider_config(
            env={"OPENROUTER_ALLOWED_MODELS": "anthropic/claude-test"}
        )

        with self.assertRaises(OpenRouterModelPolicyError) as raised:
            select_openrouter_model("L1", config)

        self.assertEqual(raised.exception.code, "CONFIGURATION_ERROR")

    def test_model_not_in_allowlist_is_invalid_model(self) -> None:
        config = load_openrouter_provider_config(
            env={
                "OPENROUTER_L1_MODEL": "anthropic/claude-test",
                "OPENROUTER_ALLOWED_MODELS": "openai/gpt-test",
            }
        )

        with self.assertRaises(OpenRouterModelPolicyError) as raised:
            select_openrouter_model("L1", config)

        self.assertEqual(raised.exception.code, "INVALID_MODEL")
        self.assertNotIn("openai/gpt-test", str(raised.exception))

    def test_requested_model_must_be_allowlisted(self) -> None:
        config = load_openrouter_provider_config(
            env={
                "OPENROUTER_L1_MODEL": "anthropic/claude-test",
                "OPENROUTER_ALLOWED_MODELS": "anthropic/claude-test,google/gemini-test",
            }
        )

        selected = select_openrouter_model(
            "L1",
            config,
            requested_model_id="google/gemini-test",
        )

        self.assertEqual(selected.model_provider, "google")

        with self.assertRaises(OpenRouterModelPolicyError) as raised:
            select_openrouter_model("L1", config, requested_model_id="xai/grok-test")

        self.assertEqual(raised.exception.code, "INVALID_MODEL")

    def test_model_without_provider_prefix_is_rejected(self) -> None:
        with self.assertRaises(OpenRouterModelPolicyError) as raised:
            derive_openrouter_model_provider("claude-test")

        self.assertEqual(raised.exception.code, "INVALID_MODEL")

        with self.assertRaises(OpenRouterModelPolicyError):
            validate_openrouter_model_id("claude-test", {"claude-test"})


if __name__ == "__main__":
    unittest.main()
