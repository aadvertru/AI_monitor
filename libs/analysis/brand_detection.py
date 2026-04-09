"""Deterministic rule-based brand detection."""

from __future__ import annotations

from dataclasses import dataclass

from libs.analysis.preprocessing import PreprocessedText


@dataclass(frozen=True)
class BrandDetectionResult:
    detected: bool
    match_type: str | None


def _alnum_only(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _extract_domain_token(brand_domain: str | None) -> str | None:
    if not brand_domain:
        return None

    value = brand_domain.strip().casefold()
    if not value:
        return None

    # Remove URL scheme if present.
    if "://" in value:
        value = value.split("://", 1)[1]

    # Keep host portion only.
    value = value.split("/", 1)[0]
    value = value.split(":", 1)[0]

    labels = [label for label in value.split(".") if label]
    if not labels:
        return None

    if labels[0] == "www" and len(labels) > 1:
        return labels[1]
    return labels[0]


def detect_brand(
    preprocessed: PreprocessedText,
    brand_name: str,
    brand_domain: str | None = None,
) -> BrandDetectionResult:
    """Detect brand with ordered exact/normalized/domain rules."""
    try:
        lowered_text = (preprocessed.lowered or "").casefold()
        lowered_brand = (brand_name or "").strip().casefold()

        if not lowered_text or not lowered_brand:
            return BrandDetectionResult(detected=False, match_type=None)

        # Rule 1: exact lowered substring match.
        if lowered_brand in lowered_text:
            return BrandDetectionResult(detected=True, match_type="exact")

        # Rule 2: normalized alphanumeric-only match.
        normalized_brand = _alnum_only(lowered_brand)
        normalized_text = _alnum_only(lowered_text)
        if normalized_brand and normalized_brand in normalized_text:
            return BrandDetectionResult(detected=True, match_type="normalized")

        # Rule 3: domain token (without TLD) match.
        domain_token = _extract_domain_token(brand_domain)
        if domain_token and domain_token in lowered_text:
            return BrandDetectionResult(detected=True, match_type="domain")

        return BrandDetectionResult(detected=False, match_type=None)
    except Exception:
        return BrandDetectionResult(detected=False, match_type=None)

