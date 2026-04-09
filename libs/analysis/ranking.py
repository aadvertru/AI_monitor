"""Brand ranking helpers for MVP parser output."""

from __future__ import annotations

from libs.analysis.mention_extraction import BrandMention


def compute_brand_rank(mentions: list[BrandMention]) -> int | None:
    """Return rank 1 when brand is present, otherwise None."""
    try:
        if not mentions:
            return None
        return 1
    except Exception:
        return None

