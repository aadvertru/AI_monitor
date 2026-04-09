"""Query list capping helpers."""

from __future__ import annotations

from collections.abc import Sequence

DEFAULT_MAX_QUERIES = 50


def cap_queries(queries: Sequence[str], max_queries: int | None = None) -> list[str]:
    """Return a deterministic first-N slice using explicit or default cap."""
    limit = max_queries if max_queries is not None else DEFAULT_MAX_QUERIES
    return list(queries[:limit])

