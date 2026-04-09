"""Rule-based competitor candidate extraction."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from libs.analysis.preprocessing import PreprocessedText

_SENTENCE_DELIMITERS = re.compile(r"[.!?]+")
_CAPITALIZED_PHRASE_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9&'\-]*)(?:\s+[A-Z][A-Za-z0-9&'\-]*)+\b"
)
_SUFFIX_CANDIDATE_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9&'\-]*)\s+(AI|Pro|Cloud|Labs|Studio|App|HQ)\b"
)
_SENTENCE_START_STOPWORDS = {
    "a",
    "an",
    "another",
    "it",
    "later",
    "the",
    "this",
    "today",
    "we",
}


@dataclass(frozen=True)
class CompetitorCandidate:
    name: str
    frequency: int


def _split_original_sentences(original: str) -> list[str]:
    parts = _SENTENCE_DELIMITERS.split(original)
    return [part.strip() for part in parts if part.strip()]


def _collapse_spaces(value: str) -> str:
    return " ".join(value.split())


def _name_key(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _is_sentence_start_match(sentence: str, start_index: int) -> bool:
    trimmed = sentence.lstrip()
    leading_spaces = len(sentence) - len(trimmed)
    return start_index == leading_spaces


def extract_competitors(
    preprocessed: PreprocessedText, brand_name: str
) -> list[CompetitorCandidate]:
    """Extract competitor candidates with deterministic rules and sorting."""
    try:
        original = preprocessed.original or ""
        if not original.strip():
            return []

        target_key = _name_key(brand_name.strip())
        frequencies: Counter[str] = Counter()

        for sentence in _split_original_sentences(original):
            seen_occurrences: set[tuple[int, int, str]] = set()

            # Rule 1: sequences of 2+ capitalized words.
            for match in _CAPITALIZED_PHRASE_RE.finditer(sentence):
                candidate_raw = _collapse_spaces(match.group(0))
                candidate_words = candidate_raw.split()

                if _is_sentence_start_match(sentence, match.start()):
                    first_word = candidate_words[0].casefold()
                    if first_word in _SENTENCE_START_STOPWORDS:
                        if len(candidate_words) >= 3:
                            candidate_raw = " ".join(candidate_words[1:])
                        else:
                            continue

                candidate = candidate_raw.casefold()
                if not candidate:
                    continue
                if _name_key(candidate) == target_key:
                    continue

                span_start = sentence.casefold().find(candidate, match.start())
                if span_start < 0:
                    span_start = match.start()
                span_end = span_start + len(candidate)
                occurrence_key = (span_start, span_end, candidate)
                if occurrence_key in seen_occurrences:
                    continue

                seen_occurrences.add(occurrence_key)
                frequencies[candidate] += 1

            # Rule 2: single capitalized word + common product suffix.
            for match in _SUFFIX_CANDIDATE_RE.finditer(sentence):
                if _is_sentence_start_match(sentence, match.start()):
                    continue

                candidate = _collapse_spaces(match.group(0)).casefold()
                if not candidate:
                    continue
                if _name_key(candidate) == target_key:
                    continue

                span_start, span_end = match.span()
                occurrence_key = (span_start, span_end, candidate)
                if occurrence_key in seen_occurrences:
                    continue

                seen_occurrences.add(occurrence_key)
                frequencies[candidate] += 1

        if not frequencies:
            return []

        candidates = [
            CompetitorCandidate(name=name, frequency=frequency)
            for name, frequency in frequencies.items()
        ]
        candidates.sort(key=lambda item: (-item.frequency, item.name))
        return candidates
    except Exception:
        return []
