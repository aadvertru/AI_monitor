from libs.analysis.longitudinal_diffs import (
    diff_competitors,
    diff_concepts,
    diff_source_domains,
    normalize_change_key,
)


def test_source_domain_diff_detects_added_removed_and_count_changes() -> None:
    changes = diff_source_domains(
        [
            {"domain": "example.com", "source_count": 3},
            {"domain": "new.com", "source_count": 1},
        ],
        [
            {"domain": "example.com", "source_count": 1},
            {"domain": "old.com", "source_count": 2},
        ],
    )

    by_key = {item.key: item for item in changes}
    assert by_key["example.com"].status == "increased"
    assert by_key["example.com"].delta == 2
    assert by_key["new.com"].status == "added"
    assert by_key["old.com"].status == "removed"


def test_concept_and_competitor_diff_normalize_case_and_whitespace() -> None:
    concept_changes = diff_concepts(
        [{"text": "  Brand Visibility ", "count": 2}],
        [{"text": "brand   visibility", "count": 2}],
    )
    competitor_changes = diff_competitors(
        [{"name": "Rival Co", "evidence_count": 1}],
        [{"name": "Old Co", "evidence_count": 1}],
    )

    assert concept_changes[0].key == "brand visibility"
    assert concept_changes[0].status == "persisted"
    assert {item.status for item in competitor_changes} == {"added", "removed"}
    assert normalize_change_key("  Acme   AI ") == "acme ai"


def test_missing_previous_data_is_safe() -> None:
    changes = diff_concepts([{"text": "New", "count": 1}], [])

    assert len(changes) == 1
    assert changes[0].status == "added"

