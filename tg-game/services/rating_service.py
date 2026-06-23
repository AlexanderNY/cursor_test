"""Рейтинг игроков по лучшей завершённой сессии."""

from __future__ import annotations

from typing import Any

from services.game_repository import game_repository


async def get_leaderboard(*, limit: int = 20) -> list[dict[str, Any]]:
    """Возвращает топ игроков (лучший результат на пользователя)."""
    return await game_repository.fetch_leaderboard(limit=limit)
