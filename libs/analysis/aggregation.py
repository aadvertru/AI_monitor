"""Aggregation helpers for run-level score rollups."""

from __future__ import annotations

import math
from typing import Any


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def _empty_audit_summary() -> dict[str, Any]:
    return {
        "total_queries": 0,
        "total_runs": 0,
        "successful_runs": 0,
        "failed_runs": 0,
        "completion_ratio": 0.0,
        "visibility_ratio": 0.0,
        "average_score": None,
        "critical_query_count": 0,
        "provider_scores": {},
    }


def _is_valid_run_result_for_summary(run_result: dict[str, Any]) -> bool:
    status = run_result.get("status")
    provider = run_result.get("provider")
    query = run_result.get("query")
    visible_brand = run_result.get("visible_brand")
    final_score = run_result.get("final_score")

    if not isinstance(status, str):
        return False
    if not isinstance(provider, str):
        return False
    if not isinstance(query, str):
        return False
    if not isinstance(visible_brand, bool):
        return False
    if isinstance(final_score, bool):
        return False
    if not isinstance(final_score, (int, float)):
        return False

    numeric_score = float(final_score)
    if not math.isfinite(numeric_score):
        return False

    return True


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


def compute_provider_scores(run_results: list[dict]) -> dict[str, float | None]:
    """Return per-provider query-style averages over successful runs only."""
    try:
        if not isinstance(run_results, list):
            return {}
        if not run_results:
            return {}

        grouped_runs: dict[str, list[dict]] = {}
        for run_result in run_results:
            if not isinstance(run_result, dict):
                return {}

            provider = run_result.get("provider")
            status = run_result.get("status")
            if not isinstance(provider, str):
                return {}
            if not isinstance(status, str):
                return {}

            grouped_runs.setdefault(provider, []).append(run_result)

        provider_scores: dict[str, float | None] = {}
        for provider in sorted(grouped_runs):
            provider_scores[provider] = compute_query_score(grouped_runs[provider])

        return provider_scores
    except Exception:
        return {}


def build_audit_summary(run_results: list[dict]) -> dict[str, Any]:
    """Build deterministic audit-level summary from run-level results."""
    try:
        if not isinstance(run_results, list):
            return _empty_audit_summary()
        if not run_results:
            return _empty_audit_summary()

        for run_result in run_results:
            if not isinstance(run_result, dict):
                return _empty_audit_summary()
            if not _is_valid_run_result_for_summary(run_result):
                return _empty_audit_summary()

        total_runs = len(run_results)
        unique_queries = {run_result["query"] for run_result in run_results}
        successful_runs_list = [
            run_result for run_result in run_results if run_result["status"] == "success"
        ]
        successful_runs = len(successful_runs_list)
        failed_runs = total_runs - successful_runs

        completion_ratio = _clamp(successful_runs / max(total_runs, 1), 0.0, 1.0)
        visible_success_count = sum(
            1
            for run_result in successful_runs_list
            if run_result["visible_brand"] is True
        )
        visibility_ratio = _clamp(
            visible_success_count / max(successful_runs, 1),
            0.0,
            1.0,
        )

        average_score = compute_query_score(run_results)
        provider_scores = compute_provider_scores(run_results)

        query_groups: dict[str, list[dict]] = {}
        for run_result in run_results:
            query_groups.setdefault(run_result["query"], []).append(run_result)

        critical_query_count = 0
        for query in sorted(query_groups):
            query_runs = query_groups[query]
            all_runs_not_visible = all(
                run_result["visible_brand"] is False for run_result in query_runs
            )
            query_score = compute_query_score(query_runs)
            low_query_score = query_score is not None and query_score < 0.3

            if all_runs_not_visible or low_query_score:
                critical_query_count += 1

        return {
            "total_queries": len(unique_queries),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "completion_ratio": round(completion_ratio, 4),
            "visibility_ratio": round(visibility_ratio, 4),
            "average_score": average_score,
            "critical_query_count": critical_query_count,
            "provider_scores": provider_scores,
        }
    except Exception:
        return _empty_audit_summary()
