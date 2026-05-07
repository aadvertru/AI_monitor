"""Change detection for longitudinal analytics snapshots."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ChangeItem:
    key: str
    label: str | None
    current_count: int | None
    previous_count: int | None
    delta: int | None
    status: str


def normalize_change_key(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def diff_counted_items(
    current: Iterable[dict],
    previous: Iterable[dict],
    *,
    key_field: str,
    label_field: str | None = None,
    count_field: str = "count",
) -> list[ChangeItem]:
    current_items = list(current)
    previous_items = list(previous)
    current_map = _item_counts(current_items, key_field=key_field, count_field=count_field)
    previous_map = _item_counts(previous_items, key_field=key_field, count_field=count_field)
    labels = _item_labels(
        current_items + previous_items,
        key_field=key_field,
        label_field=label_field or key_field,
    )

    changes: list[ChangeItem] = []
    for key in sorted(set(current_map) | set(previous_map)):
        current_count = current_map.get(key)
        previous_count = previous_map.get(key)
        if previous_count is None:
            status = "added"
        elif current_count is None:
            status = "removed"
        elif current_count > previous_count:
            status = "increased"
        elif current_count < previous_count:
            status = "decreased"
        else:
            status = "persisted"
        delta = (
            None
            if current_count is None or previous_count is None
            else current_count - previous_count
        )
        changes.append(
            ChangeItem(
                key=key,
                label=labels.get(key),
                current_count=current_count,
                previous_count=previous_count,
                delta=delta,
                status=status,
            )
        )
    return changes


def diff_source_domains(current: Iterable[dict], previous: Iterable[dict]) -> list[ChangeItem]:
    return diff_counted_items(
        current,
        previous,
        key_field="domain",
        label_field="domain",
        count_field="source_count",
    )


def diff_concepts(current: Iterable[dict], previous: Iterable[dict]) -> list[ChangeItem]:
    return diff_counted_items(
        current,
        previous,
        key_field="text",
        label_field="text",
        count_field="count",
    )


def diff_competitors(current: Iterable[dict], previous: Iterable[dict]) -> list[ChangeItem]:
    return diff_counted_items(
        current,
        previous,
        key_field="name",
        label_field="name",
        count_field="evidence_count",
    )


def _item_counts(
    items: Iterable[dict],
    *,
    key_field: str,
    count_field: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = normalize_change_key(_as_str(item.get(key_field)))
        if not key:
            continue
        counts[key] = counts.get(key, 0) + _as_int(item.get(count_field), default=1)
    return counts


def _item_labels(
    items: Iterable[dict],
    *,
    key_field: str,
    label_field: str,
) -> dict[str, str]:
    labels: dict[str, str] = {}
    for item in items:
        key = normalize_change_key(_as_str(item.get(key_field)))
        label = _as_str(item.get(label_field))
        if key and label:
            labels.setdefault(key, label)
    return labels


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _as_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default
