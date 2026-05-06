"""Small OpenXML helpers for dependency-free MVP exports."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape

FORBIDDEN_EXPORT_MARKERS = (
    "raw_response",
    "raw_prompt",
    "raw_tool_result",
    "raw_annotations",
    "request_snapshot",
    "headers",
    "authorization",
    "api_key",
    "stack_trace",
    "sk-",
)


def safe_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    lowered = text.lower()
    if any(marker in lowered for marker in FORBIDDEN_EXPORT_MARKERS):
        return "[redacted]"
    return text


def xml_text(value: object) -> str:
    return escape(safe_text(value), quote=False)


def join_values(values: Iterable[object]) -> str:
    return ", ".join(safe_text(value) for value in values if safe_text(value))


def percent(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    numeric = float(value)
    if 0 <= numeric <= 1:
        numeric *= 100
    return f"{numeric:.2f}%"


def number(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)
