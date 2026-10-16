"""Pure helpers for recurring tasks and habit streaks (no DB)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Literal

RepeatRule = Literal["none", "daily", "weekly", "monthly"]
BoardColumn = Literal["backlog", "week", "today", "done"]
Priority = Literal["low", "normal", "high"]

VALID_REPEAT_RULES = frozenset({"none", "daily", "weekly", "monthly"})
VALID_BOARDS = frozenset({"backlog", "week", "today", "done"})
VALID_PRIORITIES = frozenset({"low", "normal", "high"})

MAX_CATCH_UP = 14


def next_due_date(current: date | None, rule: str, *, from_day: date | None = None) -> date | None:
    """Shift a due date by the repeat rule. Without a date, start from from_day or today."""
    if rule not in VALID_REPEAT_RULES or rule == "none":
        return None
    base = current or from_day or date.today()
    if rule == "daily":
        return base + timedelta(days=1)
    if rule == "weekly":
        return base + timedelta(days=7)
    # monthly: same day-of-month when possible, else last day of next month
    year = base.year
    month = base.month + 1
    if month > 12:
        month = 1
        year += 1
    day = base.day
    while day >= 28:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
    return date(year, month, day)


def catch_up_due_dates(
    last_due: date | None,
    rule: str,
    *,
    until: date,
    max_items: int = MAX_CATCH_UP,
) -> list[date]:
    """Dates strictly after last_due that fall on or before until (inclusive)."""
    if rule not in VALID_REPEAT_RULES or rule == "none":
        return []
    if last_due is None:
        return []
    out: list[date] = []
    cursor = last_due
    while len(out) < max_items:
        nxt = next_due_date(cursor, rule)
        if nxt is None or nxt > until:
            break
        out.append(nxt)
        cursor = nxt
    return out


def habit_streak(checked_days: Iterable[date], *, today: date | None = None) -> int:
    """Count consecutive days ending at today (or yesterday if today is not checked)."""
    day_set = {d for d in checked_days}
    if not day_set:
        return 0
    anchor = today or date.today()
    if anchor not in day_set:
        anchor = anchor - timedelta(days=1)
    if anchor not in day_set:
        return 0
    streak = 0
    cursor = anchor
    while cursor in day_set:
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


def board_for_completion(is_done: bool, board: str) -> BoardColumn:
    """Keep board column in sync with completion."""
    if is_done:
        return "done"
    if board == "done":
        return "backlog"
    if board in VALID_BOARDS:
        return board  # type: ignore[return-value]
    return "backlog"


def due_hint_for_board(board: str, *, today: date | None = None) -> date | None:
    """Suggested due date when moving a card onto a board column."""
    day = today or date.today()
    if board == "today":
        return day
    if board == "week":
        # Monday=0 … Sunday=6 → end of current week (Sunday)
        return day + timedelta(days=(6 - day.weekday()))
    return None


def reset_checklist(items: list[dict] | None) -> list[dict]:
    """Copy checklist with all items unchecked."""
    if not items:
        return []
    out: list[dict] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        if not title:
            continue
        item_id = str(raw.get("id") or "").strip() or title[:32]
        out.append({"id": item_id[:64], "title": title[:256], "done": False})
    return out


def normalize_checklist(items: list | None) -> list[dict]:
    """Validate and clamp checklist payload from the client."""
    if not items:
        return []
    out: list[dict] = []
    for raw in items[:100]:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        if not title:
            continue
        item_id = str(raw.get("id") or "").strip() or title[:32]
        out.append(
            {
                "id": item_id[:64],
                "title": title[:256],
                "done": bool(raw.get("done")),
            }
        )
    return out
