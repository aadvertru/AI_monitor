from __future__ import annotations

import unittest
from unittest.mock import patch

from libs.execution.mock_provider import MockProviderAdapter
from libs.execution.openai_provider import OpenAIProviderAdapter
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

    def test_unsupported_adapter_returns_controlled_error(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "Unsupported provider adapter"):
            build_provider_adapter("anthropic")


if __name__ == "__main__":
    unittest.main()
