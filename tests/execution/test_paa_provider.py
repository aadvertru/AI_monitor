from __future__ import annotations

import unittest

from libs.execution.paa_config import PaaConfigError, load_paa_provider_config
from libs.execution.paa_provider import (
    DisabledPaaProvider,
    MockPaaProvider,
    build_paa_provider,
)


class PaaConfigTests(unittest.TestCase):
    def test_paa_config_loads_defaults_and_safe_repr(self) -> None:
        config = load_paa_provider_config({})

        self.assertFalse(config.enabled)
        self.assertEqual(config.provider, "mock")
        self.assertEqual(config.max_results, 10)
        self.assertEqual(config.request_timeout_seconds, 15.0)
        self.assertIn("serpapi_api_key=None", repr(config))
        self.assertNotIn("SERPAPI_API_KEY", str(config.safe_log_dict()))

    def test_paa_config_loads_env_values_without_leaking_key(self) -> None:
        config = load_paa_provider_config(
            {
                "PAA_ENABLED": "true",
                "PAA_PROVIDER": "mock",
                "PAA_MAX_RESULTS": "7",
                "PAA_REQUEST_TIMEOUT_SECONDS": "2.5",
                "SERPAPI_API_KEY": "secret-serpapi-key",
                "SERPAPI_DEFAULT_COUNTRY": "UA",
                "SERPAPI_DEFAULT_LANGUAGE": "UK",
            }
        )

        self.assertTrue(config.enabled)
        self.assertEqual(config.max_results, 7)
        self.assertEqual(config.request_timeout_seconds, 2.5)
        self.assertEqual(config.serpapi_default_country, "ua")
        self.assertEqual(config.serpapi_default_language, "uk")
        self.assertNotIn("secret-serpapi-key", repr(config))
        self.assertEqual(config.safe_log_dict()["serpapi_api_key"], "***")

    def test_paa_config_rejects_unknown_provider(self) -> None:
        with self.assertRaises(PaaConfigError):
            load_paa_provider_config({"PAA_PROVIDER": "unknown"})


class PaaProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_provider_returns_safe_empty_result(self) -> None:
        provider = DisabledPaaProvider()

        result = await provider.get_questions("Nike", "en", "us", 10)

        self.assertEqual(result.questions, [])
        self.assertEqual(
            result.warnings,
            ["People Also Ask enrichment is currently disabled."],
        )
        self.assertIsNotNone(result.diagnostic)
        self.assertEqual(result.diagnostic["code"], "PROVIDER_DISABLED")

    async def test_mock_provider_returns_deterministic_questions_with_metadata(self) -> None:
        provider = MockPaaProvider()

        result = await provider.get_questions("Nike", "en", "us", 2)

        self.assertEqual(len(result.questions), 2)
        self.assertEqual(result.questions[0].text, "What is Nike known for?")
        self.assertEqual(result.questions[0].source, "paa")
        self.assertEqual(result.questions[0].provider, "mock")
        self.assertEqual(result.questions[0].metadata["language"], "en")
        self.assertEqual(result.questions[0].metadata["country"], "us")
        self.assertEqual(result.warnings, [])

    async def test_provider_factory_uses_disabled_and_mock_providers(self) -> None:
        disabled = build_paa_provider(load_paa_provider_config({}))
        enabled = build_paa_provider(
            load_paa_provider_config({"PAA_ENABLED": "1", "PAA_PROVIDER": "mock"})
        )

        self.assertIsInstance(disabled, DisabledPaaProvider)
        self.assertIsInstance(enabled, MockPaaProvider)

    async def test_serpapi_runtime_provider_without_key_is_safe(self) -> None:
        config = load_paa_provider_config({"PAA_ENABLED": "1", "PAA_PROVIDER": "mock"})
        unsafe_config = type(
            "UnsafeConfig",
            (),
            {**config.__dict__, "provider": "serpapi"},
        )()
        provider = build_paa_provider(unsafe_config)

        result = await provider.get_questions("Nike", "en", "us", 10)

        self.assertEqual(result.questions, [])
        self.assertIn("API key is not configured", result.warnings[0])
        self.assertNotIn("secret", str(result.public_dict()).lower())
