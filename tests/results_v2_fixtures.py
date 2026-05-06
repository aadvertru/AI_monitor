from __future__ import annotations

from copy import deepcopy
from typing import Any


def _mentionability(mentioned: int, total: int) -> dict[str, Any]:
    return {
        "found": mentioned,
        "total": total,
        "percentage": round((mentioned / total) * 100, 2) if total else None,
    }


def summary_v2_fixture(
    *,
    status: str = "completed",
    query_count: int = 1,
    target_count: int = 1,
    run_count: int = 1,
    completed_runs: int = 1,
    failed_runs: int = 0,
    levels: list[str] | None = None,
    model_summaries: list[dict[str, Any]] | None = None,
    provider_diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    levels = levels or ["L1"]
    return {
        "audit_id": 42,
        "status": status,
        "totals": {
            "query_count": query_count,
            "target_count": target_count,
            "run_count": run_count,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "levels": levels,
        },
        "overall": {
            "mentionability_l1": _mentionability(1 if completed_runs else 0, completed_runs),
            "mentionability_l2": _mentionability(0, 0),
            "accuracy_l1": None,
            "accuracy_l2": None,
            "tone": {
                "positive": 0,
                "neutral": completed_runs,
                "negative": 0,
                "unknown": failed_runs,
            },
        },
        "model_summaries": model_summaries
        if model_summaries is not None
        else [model_summary_fixture()],
        "concepts": [],
        "competitor_candidates": [],
        "provider_diagnostics": provider_diagnostics or [],
    }


def model_summary_fixture(
    *,
    label: str = "GPT-4o mini",
    ai_family: str | None = "chatgpt",
    execution_provider: str = "openrouter",
    model_provider: str = "openai",
    model_id: str = "openai/gpt-4o-mini",
    mr_l1: float | None = 100.0,
    mr_l2: float | None = None,
) -> dict[str, Any]:
    return {
        "target_group_label": label,
        "ai_family": ai_family,
        "execution_provider": execution_provider,
        "model_provider": model_provider,
        "model_id": model_id,
        "mr_l1": mr_l1,
        "mr_l2": mr_l2,
        "delta_mr": mr_l2 - mr_l1 if mr_l1 is not None and mr_l2 is not None else None,
        "accuracy_l1": None,
        "accuracy_l2": None,
        "delta_accuracy": None,
        "tone_l1": "neutral",
        "tone_l2": None,
        "concepts": [],
        "competitor_candidates": [],
    }


def provider_diagnostic_fixture() -> dict[str, Any]:
    return {
        "code": "RATE_LIMIT",
        "message": "OpenRouter rate limit exceeded.",
        "provider": "openrouter",
        "model": "google/gemini-2.0-flash-001",
        "level": "L1",
        "retryable": True,
        "run_id": 1002,
        "query_id": 101,
    }


def answer_matrix_fixture(
    *,
    columns: list[dict[str, Any]] | None = None,
    rows: list[dict[str, Any]] | None = None,
    provider_diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "audit_id": 42,
        "columns": columns or [answer_matrix_column_fixture()],
        "rows": rows or [answer_matrix_row_fixture()],
        "provider_diagnostics": provider_diagnostics or [],
    }


def answer_matrix_column_fixture(
    *,
    target_id: str = "10",
    label: str = "GPT-4o mini / L1",
    level: str = "L1",
    gateway: bool = True,
    gateway_l2_experimental: bool = False,
) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "label": label,
        "ai_family": "chatgpt",
        "execution_provider": "openrouter",
        "model_provider": "openai",
        "model_id": "openai/gpt-4o-mini",
        "level": level,
        "gateway": gateway,
        "gateway_l2_experimental": gateway_l2_experimental,
    }


def answer_matrix_row_fixture(
    *,
    cells: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "query_id": "101",
        "query_text": "best ai visibility tools",
        "query_type": "category_discovery",
        "cells": cells or [answer_matrix_cell_fixture()],
    }


def answer_matrix_cell_fixture(
    *,
    target_id: str = "10",
    status: str = "completed",
    provider_error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "run_id": 1001 if status == "completed" else 1002,
        "status": status,
        "answer_excerpt": "Acme AI is visible in this answer."
        if status == "completed"
        else None,
        "brand_mentioned": True if status == "completed" else None,
        "score": 0.82 if status == "completed" else None,
        "evaluation": None,
        "sources_count": 1 if status == "completed" else 0,
        "provider_error": provider_error,
        "concepts": [],
        "competitor_candidates": [],
    }


def source_domain_url_fixture(
    *,
    url: str = "https://docs.example.com/path?utm_source=test",
    normalized_url: str = "https://docs.example.com/path",
    title: str | None = "Example docs",
    query_id: str | None = "101",
    target_id: str | None = "11",
    model_id: str | None = "openai/gpt-4o-mini",
    execution_provider: str | None = "openrouter",
    level: str | None = "L2",
) -> dict[str, Any]:
    return {
        "url": url,
        "normalized_url": normalized_url,
        "title": title,
        "snippet": "Safe evidence snippet.",
        "query_id": query_id,
        "query_text": "best ai visibility tools",
        "target_id": target_id,
        "model_id": model_id,
        "model_provider": "openai" if model_id else None,
        "execution_provider": execution_provider,
        "level": level,
        "source_type": "web",
        "gateway": execution_provider == "openrouter",
        "gateway_l2_experimental": execution_provider == "openrouter" and level == "L2",
    }


def source_domain_group_fixture(
    *,
    domain: str = "example.com",
    urls: list[dict[str, Any]] | None = None,
    source_count: int | None = None,
    levels: list[str] | None = None,
    providers: list[str] | None = None,
) -> dict[str, Any]:
    urls = urls if urls is not None else [source_domain_url_fixture()]
    query_ids = {url.get("query_id") for url in urls if url.get("query_id")}
    target_ids = {url.get("target_id") for url in urls if url.get("target_id")}
    return {
        "domain": domain,
        "source_count": source_count if source_count is not None else len(urls),
        "unique_url_count": len({url["normalized_url"] for url in urls}),
        "query_count": len(query_ids),
        "target_count": len(target_ids),
        "levels": levels if levels is not None else sorted({url["level"] for url in urls}),
        "models": sorted({url["model_id"] for url in urls if url.get("model_id")}),
        "providers": providers
        if providers is not None
        else sorted({url["execution_provider"] for url in urls if url.get("execution_provider")}),
        "urls": urls,
    }


def source_domains_fixture(
    *,
    domains: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {"audit_id": 42, "domains": domains or [], "warnings": warnings or []}


EMPTY_AUDIT_RESULTS_V2 = {
    "summary": summary_v2_fixture(
        status="created",
        query_count=0,
        target_count=1,
        run_count=0,
        completed_runs=0,
        failed_runs=0,
    ),
    "matrix": answer_matrix_fixture(rows=[]),
    "source_domains": source_domains_fixture(),
}

SINGLE_MODEL_L1_RESULTS_V2 = {
    "summary": summary_v2_fixture(),
    "matrix": answer_matrix_fixture(),
    "source_domains": source_domains_fixture(),
}

SINGLE_MODEL_L1_L2_RESULTS_V2 = {
    "summary": summary_v2_fixture(
        levels=["L1", "L2"],
        target_count=2,
        run_count=2,
        completed_runs=2,
        model_summaries=[
            model_summary_fixture(label="GPT-4o mini", mr_l1=100.0, mr_l2=0.0)
        ],
    ),
    "matrix": answer_matrix_fixture(
        columns=[
            answer_matrix_column_fixture(),
            answer_matrix_column_fixture(
                target_id="11",
                label="GPT-4o mini / L2",
                level="L2",
                gateway_l2_experimental=True,
            ),
        ],
        rows=[
            answer_matrix_row_fixture(
                cells=[
                    answer_matrix_cell_fixture(),
                    answer_matrix_cell_fixture(target_id="11", status="not_run"),
                ]
            )
        ],
    ),
    "source_domains": source_domains_fixture(),
}

MULTI_MODEL_RESULTS_V2 = deepcopy(SINGLE_MODEL_L1_RESULTS_V2)
MULTI_MODEL_RESULTS_V2["summary"]["totals"]["target_count"] = 2
MULTI_MODEL_RESULTS_V2["summary"]["model_summaries"] = [
    model_summary_fixture(),
    model_summary_fixture(
        label="Claude 3.5 Sonnet",
        ai_family="claude",
        model_provider="anthropic",
        model_id="anthropic/claude-3.5-sonnet",
    ),
]
MULTI_MODEL_RESULTS_V2["matrix"]["columns"] = [
    answer_matrix_column_fixture(),
    answer_matrix_column_fixture(
        target_id="12",
        label="Claude 3.5 Sonnet / L1",
    ),
]

PARTIAL_WITH_FAILED_CELLS_RESULTS_V2 = {
    "summary": summary_v2_fixture(
        status="partial",
        query_count=1,
        target_count=2,
        run_count=2,
        completed_runs=1,
        failed_runs=1,
        provider_diagnostics=[provider_diagnostic_fixture()],
    ),
    "matrix": answer_matrix_fixture(
        columns=[
            answer_matrix_column_fixture(),
            answer_matrix_column_fixture(target_id="11", label="Gemini 2.0 Flash / L1"),
        ],
        rows=[
            answer_matrix_row_fixture(
                cells=[
                    answer_matrix_cell_fixture(),
                    answer_matrix_cell_fixture(
                        target_id="11",
                        status="failed",
                        provider_error=provider_diagnostic_fixture(),
                    ),
                ]
            )
        ],
        provider_diagnostics=[provider_diagnostic_fixture()],
    ),
    "source_domains": source_domains_fixture(),
}

OPENROUTER_GATEWAY_L1_L2_RESULTS_V2 = deepcopy(SINGLE_MODEL_L1_L2_RESULTS_V2)

LEGACY_WITHOUT_TARGETS_RESULTS_V2 = {
    "summary": summary_v2_fixture(
        model_summaries=[
            model_summary_fixture(
                label="mock",
                ai_family=None,
                execution_provider="mock",
                model_provider="mock",
                model_id="mock",
            )
        ]
    ),
    "matrix": answer_matrix_fixture(
        columns=[
            {
                **answer_matrix_column_fixture(
                    target_id="legacy:mock:L1",
                    label="mock / L1",
                    gateway=False,
                ),
                "ai_family": None,
                "execution_provider": "mock",
                "model_provider": "mock",
                "model_id": "mock",
            }
        ]
    ),
    "source_domains": source_domains_fixture(),
}

EVALUATION_NULL_RESULTS_V2 = deepcopy(SINGLE_MODEL_L1_RESULTS_V2)

RESULTS_V2_FIXTURES = {
    "empty_audit": EMPTY_AUDIT_RESULTS_V2,
    "single_model_l1": SINGLE_MODEL_L1_RESULTS_V2,
    "single_model_l1_l2": SINGLE_MODEL_L1_L2_RESULTS_V2,
    "multi_model": MULTI_MODEL_RESULTS_V2,
    "partial_with_failed_cells": PARTIAL_WITH_FAILED_CELLS_RESULTS_V2,
    "openrouter_gateway_l1_l2": OPENROUTER_GATEWAY_L1_L2_RESULTS_V2,
    "legacy_without_targets": LEGACY_WITHOUT_TARGETS_RESULTS_V2,
    "evaluation_null": EVALUATION_NULL_RESULTS_V2,
}

SOURCE_INTELLIGENCE_V2_FIXTURES = {
    "no_sources": source_domains_fixture(),
    "single_domain_one_url": source_domains_fixture(
        domains=[source_domain_group_fixture()]
    ),
    "single_domain_multiple_urls": source_domains_fixture(
        domains=[
            source_domain_group_fixture(
                urls=[
                    source_domain_url_fixture(),
                    source_domain_url_fixture(
                        url="https://blog.example.com/article",
                        normalized_url="https://blog.example.com/article",
                        title="Example blog",
                    ),
                ],
                source_count=2,
            )
        ]
    ),
    "same_registrable_domain_across_subdomains": source_domains_fixture(
        domains=[
            source_domain_group_fixture(
                domain="bbc.co.uk",
                urls=[
                    source_domain_url_fixture(
                        url="https://news.bbc.co.uk/story",
                        normalized_url="https://news.bbc.co.uk/story",
                    ),
                    source_domain_url_fixture(
                        url="https://www.bbc.co.uk/other",
                        normalized_url="https://www.bbc.co.uk/other",
                    ),
                ],
            )
        ]
    ),
    "multiple_domains": source_domains_fixture(
        domains=[
            source_domain_group_fixture(domain="example.com"),
            source_domain_group_fixture(
                domain="wikipedia.org",
                urls=[
                    source_domain_url_fixture(
                        url="https://wikipedia.org/wiki/X",
                        normalized_url="https://wikipedia.org/wiki/X",
                    )
                ],
                providers=["openrouter"],
            ),
        ]
    ),
    "duplicate_urls": source_domains_fixture(
        domains=[
            source_domain_group_fixture(
                urls=[source_domain_url_fixture()],
                source_count=2,
            )
        ]
    ),
    "invalid_url_skipped": source_domains_fixture(
        domains=[source_domain_group_fixture()],
        warnings=["Skipped 1 invalid source URL(s)."],
    ),
    "openrouter_l2_with_citations": source_domains_fixture(
        domains=[source_domain_group_fixture()]
    ),
    "openrouter_l2_without_citations": source_domains_fixture(),
    "legacy_source_records": source_domains_fixture(
        domains=[
            source_domain_group_fixture(
                urls=[
                    source_domain_url_fixture(
                        model_id="mock",
                        execution_provider="mock",
                        level="L1",
                        target_id=None,
                    )
                ],
                levels=["L1"],
                providers=["mock"],
            )
        ]
    ),
    "partial_audit_some_sources": source_domains_fixture(
        domains=[source_domain_group_fixture()],
        warnings=["Some runs did not return citations."],
    ),
}
