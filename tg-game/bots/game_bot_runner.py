"""Запуск polling игрового бота (aiogram)."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher

from bots.game_handlers import game_router
from bots.menu_handlers import menu_router

logger = logging.getLogger(__name__)


class GameBotContextMiddleware(BaseMiddleware):
  def __init__(self, bot_id: int) -> None:
      self.bot_id = bot_id

  async def __call__(
      self,
      handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
      event: Any,
      data: dict[str, Any],
  ) -> Any:
      data["game_bot_id"] = self.bot_id
      return await handler(event, data)


async def run_game_bot_polling(bot_token: str, bot_id: int) -> None:
    """Блокирует до остановки polling (или CancelledError)."""
    token = (bot_token or "").strip()
    if not token:
        logger.warning("Bot token is empty for bot_id=%s; polling not started.", bot_id)
        return

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.update.middleware(GameBotContextMiddleware(bot_id))
    dp.include_router(menu_router)
    dp.include_router(game_router)

    logger.info("Starting game bot polling id=%s (aiogram)...", bot_id)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Game bot session closed id=%s.", bot_id)
