"""Deterministic mock provider adapter for tests and CI."""

from __future__ import annotations

from typing import Literal

from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse

MockProviderMode = Literal["success", "error", "empty"]
ALLOWED_MOCK_MODES = frozenset({"success", "error", "empty"})


class MockProviderAdapter(BaseProviderAdapter):
    """Provider-contract compliant mock with deterministic modes."""

    def __init__(self, mode: MockProviderMode = "success") -> None:
        self.mode = mode

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        mode = kwargs.get("mode", self.mode)

        try:
            normalized_query = query.strip()

            if mode == "success":
                return ProviderResponse(
                    status="success",
                    raw_answer=f"Mock answer for query: {normalized_query}",
                    citations=[
                        {
                            "url": "https://mock.local/source-1",
                            "title": "Mock Source 1",
                        },
                        {
                            "url": "https://mock.local/source-2",
                            "title": None,
                        },
                    ],
                    response_time=0.111,
                    error=None,
                    provider_metadata={"provider": "mock", "mode": "success"},
                )

            if mode == "empty":
                return ProviderResponse(
                    status="success",
                    raw_answer="",
                    citations=[],
                    response_time=0.111,
                    error=None,
                    provider_metadata={"provider": "mock", "mode": "empty"},
                )

            if mode == "error":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error={"code": "mock_error", "message": "Deterministic mock error."},
                    provider_metadata={"provider": "mock", "mode": "error"},
                )

            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=0.111,
                error={
                    "code": "mock_invalid_mode",
                    "message": f"Unsupported mock mode: {mode}",
                },
                provider_metadata={"provider": "mock", "mode": str(mode)},
            )
        except Exception as exc:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=0.111,
                error={
                    "code": "mock_internal_error",
                    "message": f"Mock provider failed: {exc}",
                },
                provider_metadata={"provider": "mock", "mode": str(mode)},
            )

