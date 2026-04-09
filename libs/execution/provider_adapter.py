"""Provider adapter interface and normalized response DTO."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

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

        if self.status == "error" and self.error is None:
            raise ValueError("error status requires a normalized error object.")

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
