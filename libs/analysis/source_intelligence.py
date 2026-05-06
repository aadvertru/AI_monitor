"""Domain-level source aggregation for Source Intelligence v2."""

from __future__ import annotations

from dataclasses import dataclass, field

from libs.analysis.source_urls import normalize_source_url


@dataclass(frozen=True)
class SourceEvidence:
    url: str | None
    title: str | None = None
    snippet: str | None = None
    source_type: str | None = None
    query_id: str | None = None
    query_text: str | None = None
    target_id: str | None = None
    model_id: str | None = None
    model_provider: str | None = None
    execution_provider: str | None = None
    level: str | None = None
    gateway: bool = False
    gateway_l2_experimental: bool = False


@dataclass(frozen=True)
class SourceDomainUrlEvidence:
    url: str
    normalized_url: str
    title: str | None = None
    snippet: str | None = None
    query_id: str | None = None
    query_text: str | None = None
    target_id: str | None = None
    model_id: str | None = None
    model_provider: str | None = None
    execution_provider: str | None = None
    level: str | None = None
    source_type: str | None = None
    gateway: bool = False
    gateway_l2_experimental: bool = False


@dataclass(frozen=True)
class SourceDomainGroup:
    domain: str
    source_count: int
    unique_url_count: int
    query_count: int
    target_count: int
    levels: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    urls: list[SourceDomainUrlEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class SourceDomainAggregationResult:
    domains: list[SourceDomainGroup] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class _MutableDomainGroup:
    domain: str
    source_count: int = 0
    urls_by_normalized: dict[str, SourceDomainUrlEvidence] = field(default_factory=dict)
    query_ids: set[str] = field(default_factory=set)
    targets: set[str] = field(default_factory=set)
    levels: set[str] = field(default_factory=set)
    models: set[str] = field(default_factory=set)
    providers: set[str] = field(default_factory=set)


def aggregate_source_domains(
    evidence_items: list[SourceEvidence],
) -> SourceDomainAggregationResult:
    groups: dict[str, _MutableDomainGroup] = {}
    skipped_invalid_urls = 0

    for evidence in evidence_items:
        if not evidence.url:
            skipped_invalid_urls += 1
            continue
        normalized = normalize_source_url(evidence.url)
        if normalized is None:
            skipped_invalid_urls += 1
            continue

        group = groups.setdefault(
            normalized.registrable_domain,
            _MutableDomainGroup(domain=normalized.registrable_domain),
        )
        group.source_count += 1
        if evidence.query_id:
            group.query_ids.add(str(evidence.query_id))
        elif evidence.query_text:
            group.query_ids.add(evidence.query_text)
        if evidence.target_id:
            group.targets.add(str(evidence.target_id))
        if evidence.level:
            group.levels.add(evidence.level)
        if evidence.model_id:
            group.models.add(evidence.model_id)
        if evidence.execution_provider:
            group.providers.add(evidence.execution_provider)

        group.urls_by_normalized.setdefault(
            normalized.normalized_url,
            SourceDomainUrlEvidence(
                url=normalized.original_url,
                normalized_url=normalized.normalized_url,
                title=evidence.title,
                snippet=evidence.snippet,
                query_id=evidence.query_id,
                query_text=evidence.query_text,
                target_id=evidence.target_id,
                model_id=evidence.model_id,
                model_provider=evidence.model_provider,
                execution_provider=evidence.execution_provider,
                level=evidence.level,
                source_type=evidence.source_type,
                gateway=evidence.gateway,
                gateway_l2_experimental=evidence.gateway_l2_experimental,
            ),
        )

    warnings = []
    if skipped_invalid_urls:
        warnings.append(f"Skipped {skipped_invalid_urls} invalid source URL(s).")

    domains = [
        SourceDomainGroup(
            domain=group.domain,
            source_count=group.source_count,
            unique_url_count=len(group.urls_by_normalized),
            query_count=len(group.query_ids),
            target_count=len(group.targets),
            levels=sorted(group.levels),
            models=sorted(group.models),
            providers=sorted(group.providers),
            urls=sorted(
                group.urls_by_normalized.values(),
                key=lambda item: (item.normalized_url, item.query_id or ""),
            ),
        )
        for group in groups.values()
    ]
    domains.sort(key=lambda group: (-group.source_count, -group.unique_url_count, group.domain))
    return SourceDomainAggregationResult(domains=domains, warnings=warnings)
