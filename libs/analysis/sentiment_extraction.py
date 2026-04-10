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

NEGATION_TOKENS: tuple[str, ...] = (
    "not",
    "no",
    "never",
    "without",
    "cannot",
    "can't",
    "won't",
    "wouldn't",
    "shouldn't",
    "couldn't",
    "don't",
    "doesn't",
    "didn't",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
)
NEGATION_LOOKBACK_TOKENS = 3

_TOKEN_PATTERN = re.compile(r"[a-z]+(?:['’][a-z]+)?")
_POSITIVE_KEYWORDS_SET = set(POSITIVE_KEYWORDS)
_NEGATIVE_KEYWORDS_SET = set(NEGATIVE_KEYWORDS)
_NEGATION_TOKENS_SET = set(NEGATION_TOKENS)


def _tokenize(sentence: str) -> list[str]:
    return _TOKEN_PATTERN.findall(sentence)


def _is_negated(tokens: list[str], index: int) -> bool:
    start = max(0, index - NEGATION_LOOKBACK_TOKENS)
    for lookback_index in range(start, index):
        if tokens[lookback_index] in _NEGATION_TOKENS_SET:
            return True
    return False


def _count_polarity_occurrences(sentences: list[str]) -> tuple[int, int]:
    positive_count = 0
    negative_count = 0

    for sentence in sentences:
        tokens = _tokenize(sentence)
        for index, token in enumerate(tokens):
            if token in _POSITIVE_KEYWORDS_SET:
                if _is_negated(tokens, index):
                    negative_count += 1
                else:
                    positive_count += 1
                continue

            if token in _NEGATIVE_KEYWORDS_SET:
                if _is_negated(tokens, index):
                    positive_count += 1
                else:
                    negative_count += 1

    return positive_count, negative_count


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
        positive_count, negative_count = _count_polarity_occurrences(
            searchable_sentences
        )

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        net = positive_count - negative_count
        sentiment = net / max(total, 1)
        return float(_clamp(sentiment, -1.0, 1.0))
    except Exception:
        return 0.0
