"""Pure helpers for roadmap voting (no I/O, no pydantic)."""

from typing import Any, Mapping, Optional, Sequence


def next_voted_state(*, already_voted: bool) -> bool:
    """Toggle: повторный клик снимает голос."""
    return not already_voted


def next_vote_count(*, current_count: int, will_vote: bool) -> int:
    """Счётчик после toggle; не уходит ниже нуля."""
    if will_vote:
        return current_count + 1
    return max(0, current_count - 1)


def row_to_roadmap_dict(row: Sequence[Any], *, voted: bool = False) -> dict[str, Any]:
    """Собирает dict полей RoadmapItem из SQL-строки."""
    return {
        "id": int(row[0]),
        "title": str(row[1]),
        "description": row[2],
        "is_active": bool(row[3]),
        "created_by": row[4],
        "created_at": row[5],
        "updated_at": row[6],
        "vote_count": int(row[7] or 0),
        "voted": voted,
    }


def parse_user_id(raw: Optional[str]) -> Optional[int]:
    """Парсит X-User-Id; None если пусто или не число."""
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def sort_items_by_votes(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Сортировка как в SQL: vote_count DESC, затем id DESC."""
    return sorted(
        items,
        key=lambda item: (-int(item.get("vote_count") or 0), -int(item.get("id") or 0)),
    )
