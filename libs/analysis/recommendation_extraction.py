"""Deterministic recommendation-signal extraction from preprocessed text."""

from __future__ import annotations

import re

from libs.analysis.preprocessing import PreprocessedText

RECOMMENDATION_PATTERNS: tuple[tuple[str, float], ...] = (
    ("best", 1.0),
    ("top pick", 1.0),
    ("top choice", 1.0),
    ("highly recommended", 1.0),
    ("recommended", 0.8),
    ("strongly suggest", 0.8),
    ("we suggest", 0.8),
    ("good option", 0.6),
    ("solid choice", 0.6),
    ("worth considering", 0.6),
    ("listed", 0.3),
    ("mentioned", 0.3),
    ("included", 0.3),
    ("one of the options", 0.3),
)

_COMPILED_PATTERNS: tuple[tuple[re.Pattern[str], float], ...] = tuple(
    (re.compile(rf"\b{re.escape(pattern)}\b"), weight)
    for pattern, weight in RECOMMENDATION_PATTERNS
)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def extract_recommendation(preprocessed: PreprocessedText | None) -> float:
    """Extract a bounded recommendation score in [0.0, 1.0] using max-match rule."""
    try:
        if preprocessed is None:
            return 0.0

        text = preprocessed.lowered if isinstance(preprocessed.lowered, str) else ""
        if not text:
            return 0.0

        max_weight = 0.0
        for compiled_pattern, weight in _COMPILED_PATTERNS:
            if compiled_pattern.search(text):
                max_weight = max(max_weight, weight)

        return float(_clamp(max_weight, 0.0, 1.0))
    except Exception:
        return 0.0
