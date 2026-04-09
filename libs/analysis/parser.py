"""Main parser entry point that assembles full ParsedResult payload."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from libs.analysis.brand_detection import detect_brand
from libs.analysis.competitor_extraction import extract_competitors
from libs.analysis.mention_extraction import extract_mentions
from libs.analysis.preprocessing import preprocess
from libs.analysis.ranking import compute_brand_rank
from libs.analysis.recommendation_extraction import extract_recommendation
from libs.analysis.sentiment_extraction import extract_sentiment
from libs.analysis.source_extraction import extract_sources
from libs.execution.provider_adapter import ProviderResponse


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def _safe_defaults() -> dict[str, Any]:
    return {
        "visible_brand": False,
        "brand_position_rank": None,
        "prominence_score": 0.0,
        "sentiment": 0.0,
        "recommendation_score": 0.0,
        "source_quality_score": 0.0,
        "competitors": [],
        "sources": [],
        "parsed_payload": {},
    }


def parse(
    brand_name: str,
    brand_domain: str | None,
    query: str,
    provider_response: ProviderResponse,
) -> dict[str, Any]:
    """Parse provider response into a full ParsedResult-shaped dictionary."""
    _ = query  # Reserved for traceability hooks in later tasks.
    safe_result = _safe_defaults()

    try:
        status = getattr(provider_response, "status", None)
        raw_answer = getattr(provider_response, "raw_answer", None)

        if status != "success":
            return safe_result
        if not isinstance(raw_answer, str) or not raw_answer.strip():
            return safe_result

        preprocessed = preprocess(raw_answer)
        if not preprocessed.lowered:
            return safe_result

        brand_detection = detect_brand(preprocessed, brand_name, brand_domain)
        mentions = extract_mentions(preprocessed, brand_name, brand_domain)
        rank = compute_brand_rank(mentions)
        competitors = extract_competitors(preprocessed, brand_name)
        sources = extract_sources(getattr(provider_response, "citations", None))
        sentiment = _clamp(float(extract_sentiment(preprocessed)), -1.0, 1.0)
        recommendation = _clamp(float(extract_recommendation(preprocessed)), 0.0, 1.0)

        mention_count = len(mentions)
        prominence = _clamp(mention_count / 5.0, 0.0, 1.0)
        source_quality_score = 0.5 if sources else 0.0

        return {
            "visible_brand": bool(mentions),
            "brand_position_rank": rank,
            "prominence_score": prominence,
            "sentiment": sentiment,
            "recommendation_score": recommendation,
            "source_quality_score": source_quality_score,
            "competitors": [asdict(item) for item in competitors],
            "sources": [asdict(item) for item in sources],
            "parsed_payload": {
                "match_type": brand_detection.match_type or "none",
                "mention_count": mention_count,
                "competitor_count": len(competitors),
            },
        }
    except Exception:
        return safe_result
