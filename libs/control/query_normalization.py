"""Query normalization helpers."""

from __future__ import annotations

from collections.abc import Sequence


def normalize_seed_queries(seed_queries: Sequence[str] | None) -> list[str]:
    """Trim, lowercase, and remove empty seed queries in a deterministic order."""
    if seed_queries is None:
        return []

    normalized: list[str] = []
    for raw_query in seed_queries:
        query = raw_query.strip().lower()
        if not query:
            continue
        normalized.append(query)
    return normalized

