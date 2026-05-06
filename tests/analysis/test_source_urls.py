from __future__ import annotations

import unittest

from libs.analysis.source_urls import (
    extract_registrable_domain,
    normalize_source_url,
)


class SourceUrlNormalizationTests(unittest.TestCase):
    def test_normalizes_scheme_host_default_port_and_fragment(self) -> None:
        result = normalize_source_url(
            "  HTTPS://WWW.Example.COM:443/path/?b=2&utm_source=x#section  "
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.normalized_url, "https://www.example.com/path/?b=2")
        self.assertEqual(result.host, "www.example.com")
        self.assertEqual(result.registrable_domain, "example.com")

    def test_preserves_meaningful_query_and_non_default_port(self) -> None:
        result = normalize_source_url("http://Example.com:8080/search?q=a+b&gclid=hidden")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.normalized_url, "http://example.com:8080/search?q=a+b")

    def test_normalizes_root_trailing_slash_consistently(self) -> None:
        result = normalize_source_url("https://example.com/")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.normalized_url, "https://example.com")

    def test_rejects_unsupported_schemes(self) -> None:
        for url in (
            "javascript:alert(1)",
            "data:text/plain,hello",
            "file:///tmp/source",
            "ftp://example.com/file",
            "mailto:test@example.com",
        ):
            with self.subTest(url=url):
                self.assertIsNone(normalize_source_url(url))

    def test_invalid_or_private_hosts_return_none(self) -> None:
        for url in ("not a url", "https://localhost/path", "https://127.0.0.1/path"):
            with self.subTest(url=url):
                self.assertIsNone(normalize_source_url(url))

    def test_extracts_registrable_domains(self) -> None:
        cases = {
            "https://news.bbc.co.uk/article": "bbc.co.uk",
            "https://sub.example.com/path": "example.com",
            "https://www.wikipedia.org/wiki/X": "wikipedia.org",
            "m.example.com": "example.com",
            "https://shop.example.com.au/path": "example.com.au",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(extract_registrable_domain(value), expected)

    def test_extract_registrable_domain_rejects_invalid_values(self) -> None:
        for value in ("", "localhost", "127.0.0.1", "javascript:alert(1)"):
            with self.subTest(value=value):
                self.assertIsNone(extract_registrable_domain(value))


if __name__ == "__main__":
    unittest.main()
