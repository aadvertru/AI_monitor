"""Deterministic sentiment extraction from preprocessed text."""

from __future__ import annotations

import re

from libs.analysis.preprocessing import PreprocessedText

POSITIVE_KEYWORDS: tuple[str, ...] = (
    "best",
    "recommend",
    "excellent",
    "great",
    "top",
    "leading",
    "trusted",
    "reliable",
    "popular",
    "innovative",
)

NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "worst",
    "avoid",
    "poor",
    "unreliable",
    "bad",
    "lacking",
    "weak",
    "outdated",
    "disappointing",
    "risky",
)

_POSITIVE_PATTERNS = {
    keyword: re.compile(rf"\b{re.escape(keyword)}\b") for keyword in POSITIVE_KEYWORDS
}
_NEGATIVE_PATTERNS = {
    keyword: re.compile(rf"\b{re.escape(keyword)}\b") for keyword in NEGATIVE_KEYWORDS
}


def _count_keyword_occurrences(
    sentences: list[str],
    patterns: dict[str, re.Pattern[str]],
) -> int:
    count = 0
    for sentence in sentences:
        for pattern in patterns.values():
            count += len(pattern.findall(sentence))
    return count


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def extract_sentiment(preprocessed: PreprocessedText | None) -> float:
    """Extract a bounded sentiment score in [-1.0, 1.0] from keyword counts."""
    try:
        if preprocessed is None:
            return 0.0

        lowered = preprocessed.lowered if isinstance(preprocessed.lowered, str) else ""
        sentences = preprocessed.sentences if isinstance(preprocessed.sentences, list) else []
        if not lowered:
            return 0.0

        searchable_sentences = sentences or [lowered]
        positive_count = _count_keyword_occurrences(
            searchable_sentences,
            _POSITIVE_PATTERNS,
        )
        negative_count = _count_keyword_occurrences(
            searchable_sentences,
            _NEGATIVE_PATTERNS,
        )

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        net = positive_count - negative_count
        sentiment = net / max(total, 1)
        return float(_clamp(sentiment, -1.0, 1.0))
    except Exception:
        return 0.0
