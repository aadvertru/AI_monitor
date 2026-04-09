from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from libs.execution.provider_adapter import (
    ALLOWED_PROVIDER_STATUSES,
    ProviderResponse,
)


class ProviderContractTests(unittest.TestCase):
    def test_success_response_contract_shape(self) -> None:
        response = ProviderResponse(
            status="success",
            raw_answer="Acme AI is mentioned.",
            citations=[{"url": "https://example.com", "title": "Example"}],
            response_time=0.42,
            error=None,
            provider_metadata={"model": "x"},
        )

        self.assertEqual(response.status, "success")
        self.assertIsInstance(response.raw_answer, str)
        self.assertIsInstance(response.citations, list)
        self.assertIsNone(response.error)
        self.assertIsInstance(response.provider_metadata, dict)

    def test_error_response_contract_shape(self) -> None:
        response = ProviderResponse(
            status="error",
            raw_answer=None,
            citations=None,
            response_time=None,
            error={"code": "provider_error", "message": "provider failed"},
            provider_metadata={"request_id": "abc"},
        )

        self.assertEqual(response.status, "error")
        self.assertIsNone(response.raw_answer)
        self.assertEqual(response.error["code"], "provider_error")
        self.assertEqual(response.error["message"], "provider failed")

    def test_status_values_are_bounded(self) -> None:
        self.assertEqual(
            ALLOWED_PROVIDER_STATUSES,
            {"success", "error", "timeout", "rate_limited"},
        )

        with self.assertRaises(ValueError):
            ProviderResponse(
                status="unsupported",  # type: ignore[arg-type]
                raw_answer=None,
                citations=None,
                response_time=None,
                error=None,
                provider_metadata=None,
            )

    def test_provider_response_is_immutable(self) -> None:
        response = ProviderResponse(
            status="timeout",
            raw_answer=None,
            citations=None,
            response_time=3.0,
            error=None,
            provider_metadata=None,
        )

        with self.assertRaises(FrozenInstanceError):
            response.status = "success"  # type: ignore[misc]

    def test_citations_shape_matches_contract(self) -> None:
        valid = ProviderResponse(
            status="success",
            raw_answer="ok",
            citations=[
                {"url": "https://example.com/a", "title": "A"},
                {"url": "https://example.com/b", "title": None},
                {"url": "https://example.com/c"},
            ],
            response_time=0.1,
            error=None,
            provider_metadata=None,
        )
        self.assertEqual(len(valid.citations or []), 3)

        with self.assertRaises(ValueError):
            ProviderResponse(
                status="success",
                raw_answer="bad citation",
                citations=[{"title": "missing url"}],
                response_time=0.1,
                error=None,
                provider_metadata=None,
            )


if __name__ == "__main__":
    unittest.main()

