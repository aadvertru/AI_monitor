"""Provider adapter interface and normalized response DTO."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from libs.execution.provider_errors import (
    ProviderErrorCode,
    empty_response_error,
    invalid_response_error,
    normalize_provider_error_dict,
    rate_limit_error,
    timeout_error,
)

ProviderStatus = Literal["success", "error", "timeout", "rate_limited"]
ALLOWED_PROVIDER_STATUSES = frozenset({"success", "error", "timeout", "rate_limited"})


@dataclass(frozen=True)
class ProviderResponse:
    status: ProviderStatus
    raw_answer: str | None
    citations: list[dict] | None
    response_time: float | None
    error: dict | None
    provider_metadata: dict | None

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_PROVIDER_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. Allowed: {sorted(ALLOWED_PROVIDER_STATUSES)}"
            )

        if self.response_time is not None and self.response_time < 0:
            raise ValueError("response_time must be >= 0 when provided.")

        if self.error is not None:
            if not isinstance(self.error, dict):
                raise ValueError("error must be a dict when provided.")
            if "code" not in self.error or "message" not in self.error:
                raise ValueError("error must contain 'code' and 'message'.")
            if not isinstance(self.error["code"], str) or not isinstance(
                self.error["message"], str
            ):
                raise ValueError("error.code and error.message must be strings.")

        if self.status != "success" and self.error is None:
            raise ValueError("non-success status requires a normalized error object.")

        if self.status == "success" and self.error is not None:
            raise ValueError("success status must not include an error object.")

        if self.provider_metadata is not None and not isinstance(self.provider_metadata, dict):
            raise ValueError("provider_metadata must be a dict when provided.")

        if self.citations is not None:
            if not isinstance(self.citations, list):
                raise ValueError("citations must be a list when provided.")
            for citation in self.citations:
                if not isinstance(citation, dict):
                    raise ValueError("Each citation must be a dict.")
                if "url" not in citation or not isinstance(citation["url"], str):
                    raise ValueError("Each citation must contain a string 'url'.")
                if "title" in citation and citation["title"] is not None and not isinstance(
                    citation["title"], str
                ):
                    raise ValueError("citation.title must be string or None.")


class BaseProviderAdapter(ABC):
    """Provider adapters must normalize all outcomes into ProviderResponse."""

    @abstractmethod
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        """Execute provider query and return normalized ProviderResponse.

        Implementations must never raise exceptions outward. Failures must be
        mapped to ProviderResponse with status in ALLOWED_PROVIDER_STATUSES.
        """


def normalize_provider_response(
    response: ProviderResponse,
    *,
    provider: str,
    model: str | None = None,
    level: str | None = None,
) -> ProviderResponse:
    """Return a ProviderResponse with normalized provider error payloads."""
    if response.status == "success":
        if response.raw_answer is None:
            return _with_error_response(
                response,
                invalid_response_error(provider, model, level).to_error_dict(),
            )
        if response.raw_answer.strip() == "":
            return _with_error_response(
                response,
                empty_response_error(provider, model, level).to_error_dict(),
            )
        return response

    if response.status == "timeout":
        return _with_error_response(
            response,
            timeout_error(provider, model, level).to_error_dict(),
            status="timeout",
        )

    if response.status == "rate_limited":
        return _with_error_response(
            response,
            rate_limit_error(provider, model, level).to_error_dict(),
            status="rate_limited",
        )

    return _with_error_response(
        response,
        normalize_provider_error_dict(
            response.error,
            provider=provider,
            model=model,
            level=level,
            fallback_code=ProviderErrorCode.PROVIDER_REQUEST_FAILED,
        ),
    )


def _with_error_response(
    response: ProviderResponse,
    error: dict,
    *,
    status: ProviderStatus = "error",
) -> ProviderResponse:
    return ProviderResponse(
        status=status,
        raw_answer=None,
        citations=response.citations if status == "success" else None,
        response_time=response.response_time,
        error=error,
        provider_metadata=response.provider_metadata,
    )
