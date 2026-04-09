"""Brand mention extraction from preprocessed text."""

from __future__ import annotations

from dataclasses import dataclass

from libs.analysis.brand_detection import detect_brand
from libs.analysis.preprocessing import PreprocessedText


@dataclass(frozen=True)
class BrandMention:
    text: str
    sentence_index: int
    char_offset: int


def _alnum_only(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _extract_domain_token(brand_domain: str | None) -> str | None:
    if not brand_domain:
        return None

    value = brand_domain.strip().casefold()
    if not value:
        return None

    if "://" in value:
        value = value.split("://", 1)[1]

    value = value.split("/", 1)[0]
    value = value.split(":", 1)[0]

    labels = [label for label in value.split(".") if label]
    if not labels:
        return None

    if labels[0] == "www" and len(labels) > 1:
        return labels[1]
    return labels[0]


def _find_all_substrings(sentence: str, needle: str) -> list[tuple[int, str]]:
    if not needle:
        return []

    results: list[tuple[int, str]] = []
    start = 0
    while True:
        index = sentence.find(needle, start)
        if index < 0:
            break
        results.append((index, sentence[index : index + len(needle)]))
        start = index + 1
    return results


def _normalized_with_index_map(sentence: str) -> tuple[str, list[int]]:
    normalized_chars: list[str] = []
    index_map: list[int] = []
    for index, char in enumerate(sentence):
        if char.isalnum():
            normalized_chars.append(char)
            index_map.append(index)
    return "".join(normalized_chars), index_map


def _find_normalized_mentions(sentence: str, normalized_brand: str) -> list[tuple[int, str]]:
    if not normalized_brand:
        return []

    normalized_sentence, index_map = _normalized_with_index_map(sentence)
    if not normalized_sentence:
        return []

    matches: list[tuple[int, str]] = []
    start = 0
    while True:
        normalized_index = normalized_sentence.find(normalized_brand, start)
        if normalized_index < 0:
            break

        normalized_end = normalized_index + len(normalized_brand)
        if normalized_end - 1 < len(index_map):
            sentence_start = index_map[normalized_index]
            sentence_end = index_map[normalized_end - 1] + 1
            matches.append((sentence_start, sentence[sentence_start:sentence_end]))

        start = normalized_index + 1

    return matches


def extract_mentions(
    preprocessed: PreprocessedText,
    brand_name: str,
    brand_domain: str | None = None,
) -> list[BrandMention]:
    """Extract brand mentions in document order from preprocessed sentences."""
    try:
        if not preprocessed.sentences:
            return []

        overall_detection = detect_brand(preprocessed, brand_name, brand_domain)
        if not overall_detection.detected:
            return []

        lowered_brand = (brand_name or "").strip().casefold()
        normalized_brand = _alnum_only(lowered_brand)
        domain_token = _extract_domain_token(brand_domain)

        mentions: list[BrandMention] = []
        for sentence_index, sentence in enumerate(preprocessed.sentences):
            sentence_preprocessed = PreprocessedText(
                original=sentence,
                lowered=sentence,
                sentences=[sentence],
            )
            sentence_detection = detect_brand(
                sentence_preprocessed,
                brand_name=brand_name,
                brand_domain=brand_domain,
            )

            if not sentence_detection.detected:
                continue

            sentence_matches: list[tuple[int, str]] = []
            if sentence_detection.match_type == "exact":
                sentence_matches = _find_all_substrings(sentence, lowered_brand)
            elif sentence_detection.match_type == "normalized":
                sentence_matches = _find_normalized_mentions(sentence, normalized_brand)
            elif sentence_detection.match_type == "domain" and domain_token:
                sentence_matches = _find_all_substrings(sentence, domain_token)

            sentence_matches.sort(key=lambda item: item[0])
            for char_offset, text in sentence_matches:
                mentions.append(
                    BrandMention(
                        text=text,
                        sentence_index=sentence_index,
                        char_offset=char_offset,
                    )
                )

        mentions.sort(key=lambda mention: (mention.sentence_index, mention.char_offset))
        return mentions
    except Exception:
        return []

