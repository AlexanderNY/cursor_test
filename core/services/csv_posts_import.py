"""Helpers for SMM publish-jobs CSV import (delimiter, headers, publish_at)."""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from typing import Any, Optional

_DATE_ALIASES = frozenset(
    {
        "publish_at",
        "scheduled_at",
        "planned_date",
        "planned_publication",
        "дата_публикации",
        "датапубликации",
    }
)
_TEXT_ALIASES = frozenset({"text", "post_text", "content", "текст"})
_CHANNEL_ALIASES = frozenset({"channel", "external_id", "канал"})
_NETWORK_ALIASES = frozenset({"network", "сеть"})
_ASSIGNED_ALIASES = frozenset({"assigned_to", "assignee"})

_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%d.%m.%Y",
)


def normalize_csv_header(name: str) -> str:
    raw = (name or "").replace("\ufeff", "").strip().lower()
    raw = re.sub(r"\s+", "_", raw)
    return raw


def detect_csv_delimiter(sample: str) -> str:
    """Prefer semicolon when Excel-RU style; otherwise comma."""
    first_line = ""
    for line in sample.splitlines():
        if line.strip():
            first_line = line
            break
    if not first_line:
        return ","
    try:
        dialect = csv.Sniffer().sniff(first_line, delimiters=",;")
        if dialect.delimiter in (",", ";"):
            return dialect.delimiter
    except csv.Error:
        pass
    return ";" if first_line.count(";") > first_line.count(",") else ","


def _cell(row: dict[str, Any], aliases: frozenset[str]) -> str:
    for key, value in row.items():
        if normalize_csv_header(str(key)) in aliases:
            return ("" if value is None else str(value)).strip()
    return ""


def row_text(row: dict[str, Any]) -> str:
    return _cell(row, _TEXT_ALIASES)


def row_publish_at_raw(row: dict[str, Any]) -> str:
    return _cell(row, _DATE_ALIASES)


def row_network(row: dict[str, Any]) -> str:
    return _cell(row, _NETWORK_ALIASES).lower()


def row_channel(row: dict[str, Any]) -> str:
    return _cell(row, _CHANNEL_ALIASES)


def row_assigned_to(row: dict[str, Any]) -> Optional[int]:
    raw = _cell(row, _ASSIGNED_ALIASES)
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)
    return None


def parse_publish_at(value: str) -> str:
    """
    Parse planned publication datetime into UTC ISO-8601 with Z suffix.

    Naive values are treated as UTC. Raises ValueError on invalid input.
    """
    raw = (value or "").strip()
    if not raw:
        raise ValueError("empty publish_at")

    normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        dt = None
        for fmt in _DATE_FORMATS:
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            raise ValueError(f"invalid publish_at: {value!r}") from None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_csv_rows(content: str) -> tuple[list[dict[str, str]], str]:
    """
    Return (rows, delimiter). Field names left as in file;
    lookup uses normalize_csv_header via row_* helpers.
    """
    delimiter = detect_csv_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows = [dict(row) for row in reader]
    return rows, delimiter
