from __future__ import annotations

import unittest

from libs.analysis.source_extraction import NormalizedSource, extract_sources


class SourceExtractionTests(unittest.TestCase):
    def test_valid_citations_are_normalized(self) -> None:
        citations = [
            {
                "url": "  https://www.wikipedia.org/wiki/Brand  ",
                "title": "Brand",
            }
        ]

        sources = extract_sources(citations)

        self.assertEqual(
            sources,
            [
                NormalizedSource(
                    url="https://www.wikipedia.org/wiki/Brand",
                    title="Brand",
                    domain="wikipedia.org",
                    source_type="encyclopedia",
                )
            ],
        )

    def test_multiple_source_types_are_classified_correctly(self) -> None:
        citations = [
            {"url": "https://github.com/acme/repo", "title": "Repo"},
            {"url": "https://arxiv.org/abs/1234.5678", "title": "Paper"},
            {"url": "https://example.gov/report", "title": "Gov Report"},
            {"url": "https://mit.edu/labs", "title": "University"},
            {"url": "https://reddit.com/r/ai", "title": "Thread"},
            {"url": "https://medium.com/@author/post", "title": "Blog"},
            {"url": "https://www.bbc.com/news/example", "title": "News"},
            {"url": "https://example.com/page", "title": "Other"},
        ]

        sources = extract_sources(citations)
        types = [source.source_type for source in sources]
        self.assertEqual(
            types,
            [
                "code_repository",
                "academic",
                "government",
                "academic",
                "forum",
                "blog",
                "news",
                "other",
            ],
        )

    def test_none_citations_returns_empty_list(self) -> None:
        self.assertEqual(extract_sources(None), [])

    def test_empty_citations_returns_empty_list(self) -> None:
        self.assertEqual(extract_sources([]), [])

    def test_malformed_citations_are_skipped(self) -> None:
        citations = [
            {},
            {"url": None},
            {"url": 123},
            {"url": "   "},
            {"title": "Missing URL"},
            {"url": "https://valid.com", "title": "Valid"},
        ]

        sources = extract_sources(citations)
        self.assertEqual(
            sources,
            [
                NormalizedSource(
                    url="https://valid.com",
                    title="Valid",
                    domain="valid.com",
                    source_type="other",
                )
            ],
        )

    def test_duplicate_urls_are_deduplicated_first_occurrence_kept(self) -> None:
        citations = [
            {"url": "https://example.com/a", "title": "First"},
            {"url": "https://example.com/a", "title": "Second"},
            {"url": "https://example.com/b", "title": "Third"},
        ]

        sources = extract_sources(citations)

        self.assertEqual(
            sources,
            [
                NormalizedSource(
                    url="https://example.com/a",
                    title="First",
                    domain="example.com",
                    source_type="other",
                ),
                NormalizedSource(
                    url="https://example.com/b",
                    title="Third",
                    domain="example.com",
                    source_type="other",
                ),
            ],
        )

    def test_classification_is_stable_across_repeated_calls(self) -> None:
        citations = [
            {"url": "https://github.com/acme/repo", "title": "Repo"},
            {"url": "https://example.com", "title": None},
        ]

        first = extract_sources(citations)
        second = extract_sources(citations)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

