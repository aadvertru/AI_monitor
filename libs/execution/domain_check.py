"""SSRF-safe brand domain availability checks."""

from __future__ import annotations

import asyncio
import inspect
import ipaddress
import re
import socket
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlparse

import httpx

DOMAIN_CHECK_CACHE_TTL_SECONDS = 86400
DOMAIN_CHECK_TIMEOUT_SECONDS = 3.0
DOMAIN_STATUS_VALUES = (
    "reachable",
    "dns_failed",
    "http_failed",
    "timeout",
    "invalid_domain",
    "blocked_private_network",
    "unknown",
)
DomainCheckStatus = Literal[
    "reachable",
    "dns_failed",
    "http_failed",
    "timeout",
    "invalid_domain",
    "blocked_private_network",
    "unknown",
]

DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
BLOCKED_HOSTS = {"localhost"}
HTTP_STATUS_REACHABLE_MAX = 499


@dataclass(frozen=True)
class DomainCheckResult:
    input: str
    normalized_domain: str | None
    status: DomainCheckStatus
    http_status: int | None
    checked_at: datetime
    query_generation_allowed: bool
    reason: str | None
    cache_ttl_seconds: int = DOMAIN_CHECK_CACHE_TTL_SECONDS


@dataclass(frozen=True)
class _CachedDomainCheck:
    result: DomainCheckResult
    expires_at: datetime


_DOMAIN_CHECK_CACHE: dict[str, _CachedDomainCheck] = {}


def clear_domain_check_cache() -> None:
    _DOMAIN_CHECK_CACHE.clear()


def normalize_domain_input(value: str) -> str | None:
    raw_value = value.strip()
    if not raw_value:
        return None

    parse_value = raw_value if "://" in raw_value else f"//{raw_value}"
    parsed = urlparse(parse_value)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None

    host = parsed.hostname
    if not host:
        return None
    host = host.rstrip(".").lower()
    if host.endswith("/"):
        host = host.rstrip("/")
    return host or None


def is_valid_public_domain(domain: str) -> bool:
    if domain in BLOCKED_HOSTS:
        return False
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        return bool(DOMAIN_PATTERN.fullmatch(domain))
    return False


def is_blocked_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


async def resolve_domain_ips(domain: str) -> list[str]:
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise
    ips: list[str] = []
    for info in infos:
        address = info[4][0]
        if address not in ips:
            ips.append(address)
    return ips


async def check_brand_domain_availability(
    domain_input: str,
    *,
    resolver: Any | None = None,
    http_client: Any | None = None,
    now: datetime | None = None,
) -> DomainCheckResult:
    checked_at = now or datetime.now(UTC)
    normalized_domain = normalize_domain_input(domain_input)
    if normalized_domain is None or not is_valid_public_domain(normalized_domain):
        return _result(
            domain_input,
            normalized_domain,
            "invalid_domain",
            checked_at=checked_at,
            reason="invalid_domain",
        )

    cached = _DOMAIN_CHECK_CACHE.get(normalized_domain)
    if cached and cached.expires_at > checked_at:
        return cached.result

    try:
        resolved = (resolver or resolve_domain_ips)(normalized_domain)
        ips = await resolved if inspect.isawaitable(resolved) else resolved
    except socket.gaierror:
        result = _result(
            domain_input,
            normalized_domain,
            "dns_failed",
            checked_at=checked_at,
            reason="dns_failed",
        )
        _cache_result(result, checked_at)
        return result
    except TimeoutError:
        result = _result(
            domain_input,
            normalized_domain,
            "timeout",
            checked_at=checked_at,
            reason="dns_timeout",
        )
        _cache_result(result, checked_at)
        return result

    if not ips:
        result = _result(
            domain_input,
            normalized_domain,
            "dns_failed",
            checked_at=checked_at,
            reason="dns_failed",
        )
        _cache_result(result, checked_at)
        return result
    if any(is_blocked_ip(ip) for ip in ips):
        result = _result(
            domain_input,
            normalized_domain,
            "blocked_private_network",
            checked_at=checked_at,
            reason="blocked_private_network",
        )
        _cache_result(result, checked_at)
        return result

    result = await _check_http_status(
        domain_input,
        normalized_domain,
        checked_at=checked_at,
        http_client=http_client,
    )
    _cache_result(result, checked_at)
    return result


async def _check_http_status(
    domain_input: str,
    normalized_domain: str,
    *,
    checked_at: datetime,
    http_client: Any | None,
) -> DomainCheckResult:
    close_client = http_client is None
    client = http_client or httpx.AsyncClient(
        follow_redirects=False,
        timeout=DOMAIN_CHECK_TIMEOUT_SECONDS,
    )
    try:
        response = await client.get(
            f"https://{normalized_domain}",
            headers={"User-Agent": "AI-Monitor-Domain-Check"},
        )
    except (asyncio.TimeoutError, httpx.TimeoutException):
        return _result(
            domain_input,
            normalized_domain,
            "timeout",
            checked_at=checked_at,
            reason="http_timeout",
        )
    except httpx.HTTPError:
        return _result(
            domain_input,
            normalized_domain,
            "http_failed",
            checked_at=checked_at,
            reason="http_failed",
        )
    finally:
        if close_client:
            await client.aclose()

    if 300 <= response.status_code < 400:
        location = response.headers.get("location")
        redirect_domain = normalize_domain_input(location or "")
        if redirect_domain and (
            not is_valid_public_domain(redirect_domain)
            or redirect_domain in BLOCKED_HOSTS
        ):
            return _result(
                domain_input,
                normalized_domain,
                "blocked_private_network",
                checked_at=checked_at,
                http_status=response.status_code,
                reason="blocked_redirect",
            )

    if 200 <= response.status_code <= HTTP_STATUS_REACHABLE_MAX:
        return _result(
            domain_input,
            normalized_domain,
            "reachable",
            checked_at=checked_at,
            http_status=response.status_code,
            reason=None,
        )
    return _result(
        domain_input,
        normalized_domain,
        "http_failed",
        checked_at=checked_at,
        http_status=response.status_code,
        reason="http_failed",
    )


def _result(
    domain_input: str,
    normalized_domain: str | None,
    status: DomainCheckStatus,
    *,
    checked_at: datetime,
    http_status: int | None = None,
    reason: str | None,
) -> DomainCheckResult:
    return DomainCheckResult(
        input=domain_input,
        normalized_domain=normalized_domain,
        status=status,
        http_status=http_status,
        checked_at=checked_at,
        query_generation_allowed=status == "reachable",
        reason=reason,
    )


def _cache_result(result: DomainCheckResult, checked_at: datetime) -> None:
    if result.normalized_domain is None:
        return
    _DOMAIN_CHECK_CACHE[result.normalized_domain] = _CachedDomainCheck(
        result=result,
        expires_at=checked_at + timedelta(seconds=DOMAIN_CHECK_CACHE_TTL_SECONDS),
    )
