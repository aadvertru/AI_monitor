from __future__ import annotations

import unittest

from libs.analysis.brand_detection import BrandDetectionResult, detect_brand
from libs.analysis.preprocessing import PreprocessedText, preprocess


class BrandDetectionTests(unittest.TestCase):
    def test_exact_match_detected(self) -> None:
        preprocessed = preprocess("Acme AI is a top option.")

        result = detect_brand(preprocessed, brand_name="Acme AI")

        self.assertEqual(result, BrandDetectionResult(detected=True, match_type="exact"))

    def test_normalized_match_detected(self) -> None:
        preprocessed = preprocess("We benchmark acmeai every week.")

        result = detect_brand(preprocessed, brand_name="Acme.AI")

        self.assertEqual(result, BrandDetectionResult(detected=True, match_type="normalized"))

    def test_domain_match_detected(self) -> None:
        preprocessed = preprocess("Teams choose acme for monitoring.")

        result = detect_brand(
            preprocessed,
            brand_name="Acme Cloud",
            brand_domain="acme.ai",
        )

        self.assertEqual(result, BrandDetectionResult(detected=True, match_type="domain"))

    def test_brand_not_present_returns_negative(self) -> None:
        preprocessed = preprocess("This text mentions another brand.")

        result = detect_brand(preprocessed, brand_name="Acme AI", brand_domain="acme.ai")

        self.assertEqual(result, BrandDetectionResult(detected=False, match_type=None))

    def test_empty_preprocessed_text_returns_safe_negative(self) -> None:
        preprocessed = PreprocessedText(original="", lowered="", sentences=[])

        result = detect_brand(preprocessed, brand_name="Acme AI", brand_domain="acme.ai")

        self.assertEqual(result, BrandDetectionResult(detected=False, match_type=None))

    def test_none_brand_domain_skips_domain_rule_without_crash(self) -> None:
        preprocessed = preprocess("We use acme in many reports.")

        result = detect_brand(preprocessed, brand_name="Brand Not Present", brand_domain=None)

        self.assertEqual(result, BrandDetectionResult(detected=False, match_type=None))


if __name__ == "__main__":
    unittest.main()

