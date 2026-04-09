from __future__ import annotations

import unittest

from libs.analysis.preprocessing import PreprocessedText, preprocess


class PreprocessingTests(unittest.TestCase):
    def test_normal_text_is_lowercased_and_split(self) -> None:
        result = preprocess("  Acme is great. It helps teams.  ")

        self.assertIsInstance(result, PreprocessedText)
        self.assertEqual(result.original, "  Acme is great. It helps teams.  ")
        self.assertEqual(result.lowered, "acme is great. it helps teams.")
        self.assertEqual(result.sentences, ["acme is great", "it helps teams"])

    def test_multiple_sentence_delimiters_are_supported(self) -> None:
        result = preprocess("Best tool! How does it work? Great.")
        self.assertEqual(
            result.sentences,
            ["best tool", "how does it work", "great"],
        )

    def test_none_input_returns_safe_empty_output(self) -> None:
        result = preprocess(None)
        self.assertEqual(result.original, "")
        self.assertEqual(result.lowered, "")
        self.assertEqual(result.sentences, [])

    def test_empty_string_returns_safe_empty_output(self) -> None:
        result = preprocess("")
        self.assertEqual(result.original, "")
        self.assertEqual(result.lowered, "")
        self.assertEqual(result.sentences, [])

    def test_whitespace_only_returns_safe_empty_output(self) -> None:
        result = preprocess("   \n\t  ")
        self.assertEqual(result.original, "   \n\t  ")
        self.assertEqual(result.lowered, "")
        self.assertEqual(result.sentences, [])

    def test_text_without_delimiters_returns_single_sentence(self) -> None:
        result = preprocess("Single sentence without delimiters")
        self.assertEqual(result.lowered, "single sentence without delimiters")
        self.assertEqual(result.sentences, ["single sentence without delimiters"])

    def test_corrupted_text_with_control_chars_does_not_crash(self) -> None:
        corrupted = "Hello\x00 world!\ud800 Bad?\x1fDone."
        result = preprocess(corrupted)

        self.assertEqual(result.lowered, "hello  world!  bad? done.")
        self.assertEqual(result.sentences, ["hello  world", "bad", "done"])
        self.assertNotIn("\x00", result.lowered)
        self.assertNotIn("\x1f", result.lowered)
        self.assertNotIn("\ud800", result.lowered)


if __name__ == "__main__":
    unittest.main()

