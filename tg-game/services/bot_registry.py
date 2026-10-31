"""Соответствие Telegram bot id и записи game_bots."""

from __future__ import annotations

_telegram_to_game_bot: dict[int, int] = {}


def set_bot_mapping(mapping: dict[int, int]) -> None:
    _telegram_to_game_bot.clear()
    _telegram_to_game_bot.update(mapping)


def resolve_game_bot_id(telegram_bot_id: int | None) -> int | None:
    if telegram_bot_id is None:
        return None
    return _telegram_to_game_bot.get(telegram_bot_id)
