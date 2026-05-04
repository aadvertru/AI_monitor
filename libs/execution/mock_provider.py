"""Deterministic mock provider adapter for tests and CI."""

from __future__ import annotations

from typing import Literal

from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.execution.provider_errors import (
    configuration_error,
    empty_response_error,
    invalid_response_error,
    provider_request_failed_error,
    rate_limit_error,
    timeout_error,
    unknown_provider_error,
    unsupported_l2_error,
)

MockProviderMode = Literal[
    "success",
    "error",
    "empty",
    "invalid_response",
    "timeout",
    "rate_limited",
    "unsupported_l2",
]
ALLOWED_MOCK_MODES = frozenset(
    {
        "success",
        "error",
        "empty",
        "invalid_response",
        "timeout",
        "rate_limited",
        "unsupported_l2",
    }
)


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
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error=empty_response_error("mock").to_error_dict(),
                    provider_metadata={"provider": "mock", "mode": "empty"},
                )

            if mode == "error":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error=provider_request_failed_error("mock").to_error_dict(),
                    provider_metadata={"provider": "mock", "mode": "error"},
                )

            if mode == "invalid_response":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error=invalid_response_error("mock").to_error_dict(),
                    provider_metadata={"provider": "mock", "mode": "invalid_response"},
                )

            if mode == "timeout":
                return ProviderResponse(
                    status="timeout",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error=timeout_error("mock").to_error_dict(),
                    provider_metadata={"provider": "mock", "mode": "timeout"},
                )

            if mode == "rate_limited":
                return ProviderResponse(
                    status="rate_limited",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error=rate_limit_error("mock").to_error_dict(),
                    provider_metadata={"provider": "mock", "mode": "rate_limited"},
                )

            if mode == "unsupported_l2":
                return ProviderResponse(
                    status="error",
                    raw_answer=None,
                    citations=None,
                    response_time=0.111,
                    error=unsupported_l2_error("mock").to_error_dict(),
                    provider_metadata={"provider": "mock", "mode": "unsupported_l2"},
                )

            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=0.111,
                error=configuration_error("mock").to_error_dict(),
                provider_metadata={"provider": "mock", "mode": str(mode)},
            )
        except Exception:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=0.111,
                error=unknown_provider_error("mock").to_error_dict(),
                provider_metadata={"provider": "mock", "mode": str(mode)},
            )

