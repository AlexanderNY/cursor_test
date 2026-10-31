"""Pure task planner helpers (no DB)."""
from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "task_planner_ut",
        API_DIR / "services" / "task_planner.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["task_planner_ut"] = module
    spec.loader.exec_module(module)
    return module


planner = _load()


def test_next_due_daily_weekly_monthly():
    base = date(2026, 1, 15)
    assert planner.next_due_date(base, "daily") == date(2026, 1, 16)
    assert planner.next_due_date(base, "weekly") == date(2026, 1, 22)
    assert planner.next_due_date(base, "monthly") == date(2026, 2, 15)
    assert planner.next_due_date(date(2026, 1, 31), "monthly") == date(2026, 2, 28)
    assert planner.next_due_date(base, "none") is None


def test_catch_up_caps_and_skips_future():
    last = date(2026, 3, 1)
    until = date(2026, 3, 5)
    missing = planner.catch_up_due_dates(last, "daily", until=until)
    assert missing == [
        date(2026, 3, 2),
        date(2026, 3, 3),
        date(2026, 3, 4),
        date(2026, 3, 5),
    ]
    assert planner.catch_up_due_dates(last, "daily", until=last) == []
    many = planner.catch_up_due_dates(
        date(2026, 1, 1), "daily", until=date(2026, 3, 1), max_items=5
    )
    assert len(many) == 5


def test_habit_streak_today_and_yesterday_anchor():
    today = date(2026, 4, 10)
    assert planner.habit_streak([], today=today) == 0
    checks = [date(2026, 4, 8), date(2026, 4, 9), date(2026, 4, 10)]
    assert planner.habit_streak(checks, today=today) == 3
    # Today missing → count through yesterday
    assert planner.habit_streak([date(2026, 4, 8), date(2026, 4, 9)], today=today) == 2
    assert planner.habit_streak([date(2026, 4, 7)], today=today) == 0


def test_board_and_due_hints():
    assert planner.board_for_completion(True, "today") == "done"
    assert planner.board_for_completion(False, "done") == "backlog"
    assert planner.board_for_completion(False, "week") == "week"
    monday = date(2026, 4, 6)  # Monday
    assert planner.due_hint_for_board("today", today=monday) == monday
    assert planner.due_hint_for_board("week", today=monday) == date(2026, 4, 12)
    assert planner.due_hint_for_board("backlog", today=monday) is None
    assert planner.due_hint_for_board("inbox", today=monday) is None
    assert planner.board_for_completion(False, "inbox") == "inbox"
    assert "inbox" in planner.VALID_BOARDS


def test_checklist_normalize_and_reset():
    raw = [
        {"id": "a", "title": " One ", "done": True},
        {"title": "", "done": False},
        {"id": "b", "title": "Two", "done": False},
    ]
    norm = planner.normalize_checklist(raw)
    assert norm == [
        {"id": "a", "title": "One", "done": True},
        {"id": "b", "title": "Two", "done": False},
    ]
    reset = planner.reset_checklist(norm)
    assert all(item["done"] is False for item in reset)
    assert [item["title"] for item in reset] == ["One", "Two"]
