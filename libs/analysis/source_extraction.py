"""Citation/source normalization and source type classification."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class NormalizedSource:
    url: str
    title: str | None
    domain: str
    source_type: str


def _extract_domain(url: str) -> str:
    # Parse URLs with and without explicit scheme.
    parsed = urlsplit(url if "://" in url else f"//{url}")
    host = parsed.netloc or parsed.path.split("/", 1)[0]

    # Remove credentials and port.
    host = host.rsplit("@", 1)[-1]
    host = host.split(":", 1)[0]
    domain = host.casefold().strip()

    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _classify_source_type(domain: str) -> str:
    if "wikipedia.org" in domain:
        return "encyclopedia"
    if "github.com" in domain:
        return "code_repository"
    if "arxiv.org" in domain:
        return "academic"
    if "scholar.google" in domain:
        return "academic"
    if domain.endswith(".gov"):
        return "government"
    if domain.endswith(".edu"):
        return "academic"
    if "reddit.com" in domain or "quora.com" in domain:
        return "forum"
    if "medium.com" in domain or "substack.com" in domain:
        return "blog"
    if any(
        news_domain in domain
        for news_domain in [
            "nytimes.com",
            "bbc.com",
            "reuters.com",
            "wsj.com",
            "bloomberg.com",
        ]
    ):
        return "news"
    return "other"


def extract_sources(citations: list[dict] | None) -> list[NormalizedSource]:
    """Normalize citation list to deterministic sources and stable source_type."""
    try:
        if not citations:
            return []

        seen_urls: set[str] = set()
        sources: list[NormalizedSource] = []

        for citation in citations:
            if not isinstance(citation, dict):
                continue

            raw_url = citation.get("url")
            if not isinstance(raw_url, str):
                continue

            normalized_url = raw_url.strip()
            if not normalized_url:
                continue

            if normalized_url in seen_urls:
                continue

            raw_title = citation.get("title")
            title = raw_title if isinstance(raw_title, str) else None
            domain = _extract_domain(normalized_url)
            source_type = _classify_source_type(domain)

            sources.append(
                NormalizedSource(
                    url=normalized_url,
                    title=title,
                    domain=domain,
                    source_type=source_type,
                )
            )
            seen_urls.add(normalized_url)

        return sources
    except Exception:
        return []

