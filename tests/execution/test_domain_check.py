from __future__ import annotations

import asyncio
import socket
import unittest
from datetime import UTC, datetime, timedelta

import httpx

from libs.execution.domain_check import (
    DOMAIN_CHECK_CACHE_TTL_SECONDS,
    check_brand_domain_availability,
    clear_domain_check_cache,
    normalize_domain_input,
)


class _FakeResponse:
    def __init__(self, status_code: int, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}


class _FakeHttpClient:
    def __init__(
        self,
        response: _FakeResponse | None = None,
        exception: Exception | None = None,
    ) -> None:
        self.response = response or _FakeResponse(200)
        self.exception = exception
        self.calls: list[str] = []
        self.closed = False

    async def get(self, url: str, **_kwargs: object) -> _FakeResponse:
        self.calls.append(url)
        if self.exception is not None:
            raise self.exception
        return self.response

    async def aclose(self) -> None:
        self.closed = True


class DomainCheckServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        clear_domain_check_cache()

    def tearDown(self) -> None:
        clear_domain_check_cache()

    def test_normalizes_protocol_path_query_and_trailing_slash(self) -> None:
        self.assertEqual(
            normalize_domain_input(" HTTPS://Example.COM/path?a=1#top "),
            "example.com",
        )
        self.assertEqual(normalize_domain_input("Example.COM/"), "example.com")

    async def test_reachable_domain_allows_query_generation(self) -> None:
        result = await check_brand_domain_availability(
            "https://Example.com/path",
            resolver=lambda _domain: ["93.184.216.34"],
            http_client=_FakeHttpClient(_FakeResponse(200)),
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )

        self.assertEqual(result.input, "https://Example.com/path")
        self.assertEqual(result.normalized_domain, "example.com")
        self.assertEqual(result.status, "reachable")
        self.assertEqual(result.http_status, 200)
        self.assertTrue(result.query_generation_allowed)
        self.assertEqual(result.cache_ttl_seconds, DOMAIN_CHECK_CACHE_TTL_SECONDS)

    async def test_invalid_domain_does_not_call_network(self) -> None:
        calls: list[str] = []

        async def resolver(domain: str) -> list[str]:
            calls.append(domain)
            return ["93.184.216.34"]

        result = await check_brand_domain_availability(
            "http://localhost/path",
            resolver=resolver,
            http_client=_FakeHttpClient(_FakeResponse(200)),
        )

        self.assertEqual(result.status, "invalid_domain")
        self.assertFalse(result.query_generation_allowed)
        self.assertEqual(calls, [])

    async def test_dns_failure(self) -> None:
        async def resolver(_domain: str) -> list[str]:
            raise socket.gaierror

        result = await check_brand_domain_availability(
            "missing.example",
            resolver=resolver,
            http_client=_FakeHttpClient(_FakeResponse(200)),
        )

        self.assertEqual(result.status, "dns_failed")
        self.assertFalse(result.query_generation_allowed)

    async def test_http_failure_and_timeout(self) -> None:
        http_failed = await check_brand_domain_availability(
            "example.com",
            resolver=lambda _domain: ["93.184.216.34"],
            http_client=_FakeHttpClient(exception=httpx.ConnectError("network down")),
        )
        self.assertEqual(http_failed.status, "http_failed")
        self.assertFalse(http_failed.query_generation_allowed)

        clear_domain_check_cache()
        timeout = await check_brand_domain_availability(
            "example.com",
            resolver=lambda _domain: ["93.184.216.34"],
            http_client=_FakeHttpClient(exception=httpx.TimeoutException("timeout")),
        )
        self.assertEqual(timeout.status, "timeout")
        self.assertFalse(timeout.query_generation_allowed)

    async def test_private_ip_and_redirect_to_private_ip_blocked(self) -> None:
        private_result = await check_brand_domain_availability(
            "example.com",
            resolver=lambda _domain: ["127.0.0.1"],
            http_client=_FakeHttpClient(_FakeResponse(200)),
        )
        self.assertEqual(private_result.status, "blocked_private_network")

        clear_domain_check_cache()
        redirect_result = await check_brand_domain_availability(
            "example.com",
            resolver=lambda _domain: ["93.184.216.34"],
            http_client=_FakeHttpClient(
                _FakeResponse(302, headers={"location": "http://127.0.0.1/admin"})
            ),
        )
        self.assertEqual(redirect_result.status, "blocked_private_network")
        self.assertFalse(redirect_result.query_generation_allowed)

    async def test_cache_hit_avoids_repeated_network_calls(self) -> None:
        resolver_calls = 0
        http_client = _FakeHttpClient(_FakeResponse(200))

        async def resolver(_domain: str) -> list[str]:
            nonlocal resolver_calls
            resolver_calls += 1
            return ["93.184.216.34"]

        now = datetime(2026, 1, 1, tzinfo=UTC)
        first = await check_brand_domain_availability(
            "example.com",
            resolver=resolver,
            http_client=http_client,
            now=now,
        )
        second = await check_brand_domain_availability(
            "example.com",
            resolver=resolver,
            http_client=http_client,
            now=now + timedelta(seconds=60),
        )

        self.assertEqual(first, second)
        self.assertEqual(resolver_calls, 1)
        self.assertEqual(len(http_client.calls), 1)

    async def test_all_non_reachable_statuses_disallow_query_generation(self) -> None:
        statuses = [
            await check_brand_domain_availability("not a domain"),
            await check_brand_domain_availability(
                "example.com",
                resolver=lambda _domain: ["93.184.216.34"],
                http_client=_FakeHttpClient(_FakeResponse(500)),
            ),
        ]
        for result in statuses:
            self.assertFalse(result.query_generation_allowed)


class DomainCheckAsyncResolverTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolver_timeout_is_safe(self) -> None:
        async def resolver(_domain: str) -> list[str]:
            raise TimeoutError

        result = await check_brand_domain_availability(
            "example.com",
            resolver=resolver,
            http_client=_FakeHttpClient(_FakeResponse(200)),
        )

        self.assertEqual(result.status, "timeout")
        self.assertFalse(result.query_generation_allowed)


async def _never_called_resolver(_domain: str) -> list[str]:
    raise AssertionError("resolver should not be called")


def test_ip_literals_are_invalid_before_network() -> None:
    result = asyncio.run(
        check_brand_domain_availability(
            "192.168.1.1",
            resolver=_never_called_resolver,
            http_client=_FakeHttpClient(_FakeResponse(200)),
        )
    )

    assert result.status == "invalid_domain"
    assert result.query_generation_allowed is False
