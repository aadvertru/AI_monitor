"""Component scoring metrics derived from ParsedResult-like dictionaries."""

from __future__ import annotations

import math
from typing import Any


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def _safe_numeric_or_none(parsed: dict[str, Any], field: str) -> float | None:
    value = parsed.get(field)
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    return numeric


def compute_component_metrics(parsed: dict) -> dict[str, float]:
    """Compute bounded component metrics from parser output."""
    try:
        if not isinstance(parsed, dict):
            parsed = {}

        visible_brand_value = parsed.get("visible_brand")
        visibility_score = 1.0 if visible_brand_value is True else 0.0

        prominence_input = _safe_numeric_or_none(parsed, "prominence_score")
        sentiment_input = _safe_numeric_or_none(parsed, "sentiment")
        recommendation_input = _safe_numeric_or_none(parsed, "recommendation_score")
        source_quality_input = _safe_numeric_or_none(parsed, "source_quality_score")

        prominence_score = (
            _clamp(prominence_input, 0.0, 1.0) if prominence_input is not None else 0.0
        )
        sentiment_score = (
            _clamp((sentiment_input + 1.0) / 2.0, 0.0, 1.0)
            if sentiment_input is not None
            else 0.0
        )
        recommendation_score = (
            _clamp(recommendation_input, 0.0, 1.0)
            if recommendation_input is not None
            else 0.0
        )
        source_quality_score = (
            _clamp(source_quality_input, 0.0, 1.0)
            if source_quality_input is not None
            else 0.0
        )

        return {
            "visibility_score": _clamp(visibility_score, 0.0, 1.0),
            "prominence_score": _clamp(prominence_score, 0.0, 1.0),
            "sentiment_score": _clamp(sentiment_score, 0.0, 1.0),
            "recommendation_score": _clamp(recommendation_score, 0.0, 1.0),
            "source_quality_score": _clamp(source_quality_score, 0.0, 1.0),
        }
    except Exception:
        return {
            "visibility_score": 0.0,
            "prominence_score": 0.0,
            "sentiment_score": 0.0,
            "recommendation_score": 0.0,
            "source_quality_score": 0.0,
        }
