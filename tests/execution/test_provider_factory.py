from __future__ import annotations

import unittest
from unittest.mock import patch

from libs.execution.anthropic_provider import AnthropicProviderAdapter
from libs.execution.mock_provider import MockProviderAdapter
from libs.execution.openai_provider import OpenAIProviderAdapter
from libs.execution.openrouter_provider import OpenRouterProviderAdapter
from libs.execution.pilot_config import PilotPolicyError, RealProviderPilotConfig
from libs.execution.provider_factory import build_provider_adapter


class ProviderFactoryTests(unittest.TestCase):
    def test_mock_adapter_is_selected_in_default_mock_mode(self) -> None:
        adapter = build_provider_adapter("mock")

        self.assertIsInstance(adapter, MockProviderAdapter)

    def test_mock_adapter_is_selected_in_openai_provider_mode(self) -> None:
        adapter = build_provider_adapter(
            "mock",
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="openai",
            ),
        )

        self.assertIsInstance(adapter, MockProviderAdapter)

    def test_openai_adapter_requires_real_provider_mode_enabled(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "real provider mode is enabled"):
            build_provider_adapter("openai")

    def test_openai_adapter_is_selected_only_when_constraints_allow_it(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            adapter = build_provider_adapter(
                "openai",
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openai",
                ),
            )

        self.assertIsInstance(adapter, OpenAIProviderAdapter)

    def test_anthropic_adapter_requires_real_provider_mode_enabled(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "real provider mode is enabled"):
            build_provider_adapter("anthropic")

    def test_anthropic_adapter_is_selected_only_when_constraints_allow_it(self) -> None:
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True):
            adapter = build_provider_adapter(
                "anthropic",
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="anthropic",
                ),
            )

        self.assertIsInstance(adapter, AnthropicProviderAdapter)

    def test_openrouter_adapter_requires_real_provider_mode_enabled(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "real provider mode is enabled"):
            build_provider_adapter("openrouter")

    def test_openrouter_adapter_is_selected_only_when_constraints_allow_it(self) -> None:
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-or-test"}, clear=True):
            adapter = build_provider_adapter(
                "openrouter",
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openrouter",
                ),
            )

        self.assertIsInstance(adapter, OpenRouterProviderAdapter)

    def test_provider_mode_mismatch_blocks_real_providers(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "Anthropic adapter"):
            build_provider_adapter(
                "anthropic",
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openai",
                ),
            )

        with self.assertRaisesRegex(PilotPolicyError, "OpenAI adapter"):
            build_provider_adapter(
                "openai",
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="anthropic",
                ),
            )

        with self.assertRaisesRegex(PilotPolicyError, "OpenRouter adapter"):
            build_provider_adapter(
                "openrouter",
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openai",
                ),
            )

    def test_unsupported_adapter_returns_controlled_error(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "Unsupported provider adapter"):
            build_provider_adapter("gemini")


if __name__ == "__main__":
    unittest.main()
