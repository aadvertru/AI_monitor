"""Parser preprocessing for raw provider text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_SENTENCE_DELIMITERS = re.compile(r"[.!?]+")


@dataclass(frozen=True)
class PreprocessedText:
    original: str
    lowered: str
    sentences: list[str]


def _sanitize_text(text: str) -> str:
    sanitized_chars: list[str] = []
    for char in text:
        category = unicodedata.category(char)

        # Remove problematic Unicode surrogates and control characters.
        if category == "Cs":
            sanitized_chars.append(" ")
            continue
        if category.startswith("C") and char not in ("\n", "\r", "\t"):
            sanitized_chars.append(" ")
            continue

        sanitized_chars.append(char)
    return "".join(sanitized_chars)


def preprocess(raw_answer: str | None) -> PreprocessedText:
    """Normalize raw text to deterministic lowered text and sentence list."""
    original = raw_answer if raw_answer is not None else ""

    try:
        sanitized = _sanitize_text(original)
        trimmed = sanitized.strip()
        if not trimmed:
            return PreprocessedText(original=original, lowered="", sentences=[])

        lowered = trimmed.lower()
        split_parts = _SENTENCE_DELIMITERS.split(lowered)
        sentences = [part.strip() for part in split_parts if part.strip()]

        return PreprocessedText(
            original=original,
            lowered=lowered,
            sentences=sentences,
        )
    except Exception:
        return PreprocessedText(original=original, lowered="", sentences=[])

