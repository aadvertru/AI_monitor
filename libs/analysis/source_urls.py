"""Safe source URL normalization helpers for source intelligence."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

SUPPORTED_SOURCE_SCHEMES = {"http", "https"}
TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "yclid",
}

# This is a deterministic fallback, not a full Public Suffix List. Additions should stay
# conservative so distinct real registrable domains are not merged incorrectly.
MULTI_PART_PUBLIC_SUFFIXES = {
    "ac.uk",
    "co.jp",
    "co.uk",
    "com.au",
    "com.br",
    "com.tr",
    "com.ua",
    "net.au",
    "net.br",
    "net.uk",
    "org.au",
    "org.br",
    "org.uk",
}


@dataclass(frozen=True)
class NormalizedUrl:
    original_url: str
    normalized_url: str
    scheme: str
    host: str
    registrable_domain: str


def normalize_source_url(url: str) -> NormalizedUrl | None:
    """Return a normalized source URL or None for unsafe/invalid values."""

    original_url = url.strip()
    if not original_url:
        return None

    parsed = urlparse(original_url)
    scheme = parsed.scheme.lower()
    if scheme not in SUPPORTED_SOURCE_SCHEMES:
        return None

    host = _normalize_host(parsed.hostname)
    if host is None:
        return None

    registrable_domain = extract_registrable_domain(host)
    if registrable_domain is None:
        return None

    netloc = host
    if parsed.port is not None and not _is_default_port(scheme, parsed.port):
        netloc = f"{host}:{parsed.port}"

    query = _normalize_query(parsed.query)
    path = parsed.path or ""
    if path == "/":
        path = ""

    normalized_url = urlunparse((scheme, netloc, path, "", query, ""))
    return NormalizedUrl(
        original_url=original_url,
        normalized_url=normalized_url,
        scheme=scheme,
        host=host,
        registrable_domain=registrable_domain,
    )


def extract_registrable_domain(url_or_host: str) -> str | None:
    """Extract a safe registrable domain using a conservative PSL fallback."""

    value = url_or_host.strip()
    if not value:
        return None

    parsed = urlparse(value if "://" in value else f"//{value}")
    if parsed.scheme and parsed.scheme.lower() not in SUPPORTED_SOURCE_SCHEMES:
        return None

    host = _normalize_host(parsed.hostname)
    if host is None:
        return None

    labels = [label for label in host.split(".") if label]
    if len(labels) < 2:
        return None

    suffix_two = ".".join(labels[-2:])
    suffix_three = ".".join(labels[-3:]) if len(labels) >= 3 else suffix_two

    if suffix_two in MULTI_PART_PUBLIC_SUFFIXES and len(labels) >= 3:
        return suffix_three

    return suffix_two


def _normalize_host(host: str | None) -> str | None:
    if host is None:
        return None
    normalized = host.strip().rstrip(".").lower()
    if not normalized:
        return None
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        return normalized
    return None


def _is_default_port(scheme: str, port: int) -> bool:
    return (scheme == "http" and port == 80) or (scheme == "https" and port == 443)


def _normalize_query(query: str) -> str:
    pairs = [
        (key, value)
        for key, value in parse_qsl(query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    ]
    return urlencode(pairs, doseq=True)
