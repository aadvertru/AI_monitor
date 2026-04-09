"""Deterministic intent tagging rules for prepared queries."""

from __future__ import annotations

INTENT_COMPARISON = "comparison"
INTENT_USE_CASE = "use_case"
INTENT_GENERAL = "general"


def tag_query_intent(query: str) -> str:
    """Tag query intent using ordered, case-insensitive first-match rules."""
    lowered = query.casefold()

    if "best" in lowered:
        return INTENT_COMPARISON

    if lowered.lstrip().startswith("how"):
        return INTENT_USE_CASE

    return INTENT_GENERAL

