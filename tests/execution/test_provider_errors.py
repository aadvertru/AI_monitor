from __future__ import annotations

import unittest

from libs.execution.provider_errors import (
    ProviderErrorCode,
    no_api_key_error,
    normalize_provider_error_dict,
    rate_limit_error,
    timeout_error,
    unknown_provider_error,
)


class ProviderErrorsTests(unittest.TestCase):
    def test_error_helpers_return_whitelisted_public_shape(self) -> None:
        error = no_api_key_error("openai", model="gpt-test", level="L1").to_error_dict()

        self.assertEqual(
            set(error),
            {
                "code",
                "message",
                "provider",
                "model",
                "level",
                "retryable",
                "details",
            },
        )
        self.assertEqual(error["code"], "NO_API_KEY")
        self.assertEqual(error["provider"], "openai")
        self.assertEqual(error["model"], "gpt-test")
        self.assertEqual(error["level"], "L1")

    def test_retryable_errors_are_marked_retryable(self) -> None:
        self.assertTrue(timeout_error("openai").to_error_dict()["retryable"])
        self.assertTrue(rate_limit_error("openai").to_error_dict()["retryable"])

    def test_legacy_error_codes_are_normalized_without_raw_message(self) -> None:
        secret = "sk-secret"

        error = normalize_provider_error_dict(
            {"code": "provider_error", "message": f"failed with {secret}"},
            provider="openai",
            model="gpt-test",
            level="L2",
        )

        self.assertEqual(error["code"], "PROVIDER_REQUEST_FAILED")
        self.assertEqual(error["provider"], "openai")
        self.assertEqual(error["model"], "gpt-test")
        self.assertEqual(error["level"], "L2")
        self.assertNotIn(secret, error["message"])

    def test_unknown_provider_error_does_not_include_exception_text(self) -> None:
        secret = "sk-hidden"

        error = unknown_provider_error("openai").to_error_dict()

        self.assertEqual(error["code"], ProviderErrorCode.UNKNOWN_PROVIDER_ERROR.value)
        self.assertNotIn(secret, error["message"])


if __name__ == "__main__":
    unittest.main()
