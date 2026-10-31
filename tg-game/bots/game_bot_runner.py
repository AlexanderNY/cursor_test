"""Общий диспетчер игровых ботов (aiogram).

Роутеры можно подключить только к одному Dispatcher, поэтому все токены
опрашиваются одним экземпляром, а game_bot_id берётся из реестра.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Dispatcher

from bots.country_handlers import country_router
from bots.game_handlers import game_router
from bots.menu_handlers import menu_router
from services.bot_registry import resolve_game_bot_id

logger = logging.getLogger(__name__)


class GameBotContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        telegram_bot_id = None
        if bot is not None:
            try:
                raw_id = bot.id
            except Exception:
                raw_id = None
            if isinstance(raw_id, int):
                telegram_bot_id = raw_id
        game_bot_id = resolve_game_bot_id(telegram_bot_id)
        if game_bot_id is None:
            logger.warning(
                "Update ignored: no game bot mapping for telegram bot id=%s",
                telegram_bot_id,
            )
            return None
        data["game_bot_id"] = game_bot_id
        return await handler(event, data)


def attach_game_routers(dispatcher: Dispatcher) -> None:
    dispatcher.update.middleware(GameBotContextMiddleware())
    dispatcher.include_router(menu_router)
    dispatcher.include_router(country_router)
    dispatcher.include_router(game_router)
