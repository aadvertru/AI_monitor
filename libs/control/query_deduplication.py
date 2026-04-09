"""Query deduplication helpers."""

from __future__ import annotations

from collections.abc import Sequence


def _query_equality_key(query: str) -> str:
    # Collapse internal whitespace and compare case-insensitively.
    return " ".join(query.split()).casefold()


def deduplicate_queries(queries: Sequence[str]) -> list[str]:
    """Remove duplicates while preserving order of first occurrence."""
    deduplicated: list[str] = []
    seen: set[str] = set()

    for query in queries:
        key = _query_equality_key(query)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(query)

    return deduplicated

