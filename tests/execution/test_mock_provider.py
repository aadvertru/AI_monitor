from __future__ import annotations

import unittest

from libs.execution.mock_provider import MockProviderAdapter


class MockProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_mode_returns_stable_valid_response(self) -> None:
        adapter = MockProviderAdapter(mode="success")

        response = await adapter.query("best ai brand visibility tools")

        self.assertEqual(response.status, "success")
        self.assertIsNotNone(response.raw_answer)
        self.assertIsNone(response.error)
        self.assertIsInstance(response.citations, list)
        self.assertEqual(response.provider_metadata, {"provider": "mock", "mode": "success"})

    async def test_error_mode_returns_normalized_error_response(self) -> None:
        adapter = MockProviderAdapter(mode="error")

        response = await adapter.query("how to improve visibility")

        self.assertEqual(response.status, "error")
        self.assertIsNone(response.raw_answer)
        self.assertIsNone(response.citations)
        self.assertEqual(response.error, {"code": "mock_error", "message": "Deterministic mock error."})

    async def test_repeated_calls_with_same_input_are_identical(self) -> None:
        adapter = MockProviderAdapter(mode="success")

        first = await adapter.query("the best monitoring tools")
        second = await adapter.query("the best monitoring tools")

        self.assertEqual(first, second)

    async def test_empty_mode_returns_valid_contract_response(self) -> None:
        adapter = MockProviderAdapter(mode="empty")

        response = await adapter.query("brand visibility benchmark")

        self.assertEqual(response.status, "success")
        self.assertEqual(response.raw_answer, "")
        self.assertEqual(response.citations, [])
        self.assertIsNone(response.error)
        self.assertEqual(response.provider_metadata, {"provider": "mock", "mode": "empty"})


if __name__ == "__main__":
    unittest.main()

