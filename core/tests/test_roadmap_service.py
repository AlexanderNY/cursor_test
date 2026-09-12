"""Unit tests for roadmap voting helpers (no Postgres)."""

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

_HELPERS = Path(__file__).resolve().parents[1] / "services" / "roadmap_helpers.py"


def _load_helpers():
    spec = importlib.util.spec_from_file_location("roadmap_helpers_under_test", _HELPERS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_helpers()
next_voted_state = _mod.next_voted_state
next_vote_count = _mod.next_vote_count
row_to_roadmap_dict = _mod.row_to_roadmap_dict
parse_user_id = _mod.parse_user_id
sort_items_by_votes = _mod.sort_items_by_votes


def test_toggle_adds_vote_when_not_voted():
    assert next_voted_state(already_voted=False) is True


def test_toggle_removes_vote_when_already_voted():
    assert next_voted_state(already_voted=True) is False


def test_vote_count_increments_and_decrements():
    assert next_vote_count(current_count=3, will_vote=True) == 4
    assert next_vote_count(current_count=3, will_vote=False) == 2


def test_vote_count_does_not_go_negative():
    assert next_vote_count(current_count=0, will_vote=False) == 0


def test_row_to_roadmap_dict_maps_fields():
    created = datetime(2026, 9, 11, tzinfo=timezone.utc)
    updated = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
    row = (7, "Dark mode", "UI theme", True, 42, created, updated, 5)
    item = row_to_roadmap_dict(row, voted=True)
    assert item["id"] == 7
    assert item["title"] == "Dark mode"
    assert item["description"] == "UI theme"
    assert item["is_active"] is True
    assert item["created_by"] == 42
    assert item["vote_count"] == 5
    assert item["voted"] is True


def test_parse_user_id():
    assert parse_user_id("12") == 12
    assert parse_user_id(None) is None
    assert parse_user_id("") is None
    assert parse_user_id("abc") is None


def test_sort_items_by_votes():
    items = [
        {"id": 1, "vote_count": 2},
        {"id": 3, "vote_count": 5},
        {"id": 2, "vote_count": 5},
    ]
    sorted_items = sort_items_by_votes(items)
    assert [item["id"] for item in sorted_items] == [3, 2, 1]
