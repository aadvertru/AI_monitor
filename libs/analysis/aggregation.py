"""Aggregation helpers for run-level score rollups."""

from __future__ import annotations

import math
from typing import Any


def _safe_success_score(run_result: dict[str, Any]) -> float | None:
    status = run_result.get("status")
    if not isinstance(status, str):
        return None
    if status != "success":
        return None

    score = run_result.get("final_score")
    if isinstance(score, bool):
        return None
    if not isinstance(score, (int, float)):
        return None

    numeric_score = float(score)
    if not math.isfinite(numeric_score):
        return None
    if numeric_score < 0.0 or numeric_score > 1.0:
        return None
    return numeric_score


def compute_query_score(run_results: list[dict]) -> float | None:
    """Return mean final_score for successful runs or None when no data."""
    try:
        if not isinstance(run_results, list):
            return None
        if not run_results:
            return None

        successful_scores: list[float] = []
        for run_result in run_results:
            if not isinstance(run_result, dict):
                return None

            success_score = _safe_success_score(run_result)
            if success_score is None:
                status = run_result.get("status")
                if status == "success":
                    return None
                continue

            successful_scores.append(success_score)

        if not successful_scores:
            return None

        mean_score = sum(successful_scores) / len(successful_scores)
        return round(mean_score, 4)
    except Exception:
        return None
