"""Запуск polling игрового бота (aiogram)."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher

from bots.game_handlers import game_router

logger = logging.getLogger(__name__)


async def run_game_bot_polling(bot_token: str) -> None:
    """Блокирует до остановки polling (или CancelledError)."""
    token = (bot_token or "").strip()
    if not token:
        logger.warning("GAME_BOT_TOKEN is empty; game bot not started.")
        return

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(game_router)

    logger.info("Starting game bot polling (aiogram)...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Game bot session closed.")
