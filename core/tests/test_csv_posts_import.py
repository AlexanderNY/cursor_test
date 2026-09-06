"""Unit tests for SMM posts CSV import helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_HELPER_PATH = Path(__file__).resolve().parents[1] / "services" / "csv_posts_import.py"
_SPEC = importlib.util.spec_from_file_location("csv_posts_import", _HELPER_PATH)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)

detect_csv_delimiter = _mod.detect_csv_delimiter
iter_csv_rows = _mod.iter_csv_rows
parse_publish_at = _mod.parse_publish_at
row_channel = _mod.row_channel
row_network = _mod.row_network
row_publish_at_raw = _mod.row_publish_at_raw
row_text = _mod.row_text


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2026-09-10T10:00:00Z", "2026-09-10T10:00:00Z"),
        ("2026-09-10T10:00:00+00:00", "2026-09-10T10:00:00Z"),
        ("2026-09-10 18:00", "2026-09-10T18:00:00Z"),
        ("10.09.2026 18:00", "2026-09-10T18:00:00Z"),
        ("10.09.2026", "2026-09-10T00:00:00Z"),
        ("2026-09-05T18:00", "2026-09-05T18:00:00Z"),
    ],
)
def test_parse_publish_at_formats(raw: str, expected: str) -> None:
    assert parse_publish_at(raw) == expected


def test_parse_publish_at_invalid() -> None:
    with pytest.raises(ValueError, match="invalid publish_at"):
        parse_publish_at("not-a-date")


def test_detect_semicolon_delimiter() -> None:
    sample = "text;publish_at;network;channel\nHello;10.09.2026 18:00;tg;-1001\n"
    assert detect_csv_delimiter(sample) == ";"


def test_detect_comma_delimiter() -> None:
    sample = "text,publish_at,network,channel\nHello,2026-09-10T10:00:00Z,tg,-1001\n"
    assert detect_csv_delimiter(sample) == ","


def test_iter_csv_rows_semicolon_and_aliases() -> None:
    content = (
        "текст;дата публикации;сеть;канал\n"
        "Пост один;10.09.2026 18:00;tg;-100123\n"
        "Пост два;bad-date;tg;-100123\n"
    )
    rows, delimiter = iter_csv_rows(content)
    assert delimiter == ";"
    assert len(rows) == 2
    assert row_text(rows[0]) == "Пост один"
    assert row_publish_at_raw(rows[0]) == "10.09.2026 18:00"
    assert row_network(rows[0]) == "tg"
    assert row_channel(rows[0]) == "-100123"
    assert parse_publish_at(row_publish_at_raw(rows[0])) == "2026-09-10T18:00:00Z"
    with pytest.raises(ValueError):
        parse_publish_at(row_publish_at_raw(rows[1]))


def test_planned_date_alias() -> None:
    content = "text,planned_date\nHello,2026-09-12T12:00:00Z\n"
    rows, _ = iter_csv_rows(content)
    assert row_publish_at_raw(rows[0]) == "2026-09-12T12:00:00Z"


def test_approval_without_channel_leaves_empty_targets() -> None:
    """Rows without network/channel yield empty targets (create_job fails on approval)."""
    content = "text,publish_at\nNo channel,2026-09-10T10:00:00Z\n"
    rows, _ = iter_csv_rows(content)
    assert row_text(rows[0]) == "No channel"
    assert row_network(rows[0]) == ""
    assert row_channel(rows[0]) == ""
    assert parse_publish_at(row_publish_at_raw(rows[0])) == "2026-09-10T10:00:00Z"
