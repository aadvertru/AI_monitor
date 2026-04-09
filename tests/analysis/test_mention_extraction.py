from __future__ import annotations

import unittest

from libs.analysis.mention_extraction import BrandMention, extract_mentions
from libs.analysis.preprocessing import PreprocessedText, preprocess


class MentionExtractionTests(unittest.TestCase):
    def test_multiple_mentions_across_sentences_are_in_document_order(self) -> None:
        preprocessed = preprocess("Acme AI wins. We compare acme ai often.")

        mentions = extract_mentions(preprocessed, brand_name="Acme AI")

        self.assertEqual(
            mentions,
            [
                BrandMention(text="acme ai", sentence_index=0, char_offset=0),
                BrandMention(text="acme ai", sentence_index=1, char_offset=11),
            ],
        )

    def test_sentence_index_and_char_offset_are_correct(self) -> None:
        preprocessed = preprocess("Other intro. Prefix acme ai suffix.")

        mentions = extract_mentions(preprocessed, brand_name="Acme AI")

        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0].sentence_index, 1)
        self.assertEqual(mentions[0].char_offset, 7)
        self.assertEqual(mentions[0].text, "acme ai")

    def test_multiple_mentions_in_same_sentence_are_all_returned(self) -> None:
        preprocessed = preprocess("we use acme ai and acme ai daily.")

        mentions = extract_mentions(preprocessed, brand_name="Acme AI")

        self.assertEqual(
            mentions,
            [
                BrandMention(text="acme ai", sentence_index=0, char_offset=7),
                BrandMention(text="acme ai", sentence_index=0, char_offset=19),
            ],
        )

    def test_no_mentions_returns_empty_list(self) -> None:
        preprocessed = preprocess("This text mentions no target brand.")
        mentions = extract_mentions(preprocessed, brand_name="Acme AI")
        self.assertEqual(mentions, [])

    def test_empty_preprocessed_text_returns_empty_list(self) -> None:
        preprocessed = PreprocessedText(original="", lowered="", sentences=[])
        mentions = extract_mentions(preprocessed, brand_name="Acme AI")
        self.assertEqual(mentions, [])


if __name__ == "__main__":
    unittest.main()

