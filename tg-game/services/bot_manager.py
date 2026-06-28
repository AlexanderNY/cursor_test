"""Управление polling нескольких игровых ботов."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from services.game_repository import game_repository

logger = logging.getLogger(__name__)

_poll_tasks: dict[int, asyncio.Task] = {}


async def start_bot_polling(bot_id: int, token: str) -> None:
    from bots.game_bot_runner import run_game_bot_polling

    await stop_bot_polling(bot_id)
    task = asyncio.create_task(
        run_game_bot_polling(token, bot_id),
        name=f"game-bot-{bot_id}",
    )
    _poll_tasks[bot_id] = task
    logger.info("Started polling for game bot id=%s", bot_id)


async def stop_bot_polling(bot_id: int) -> None:
    task = _poll_tasks.pop(bot_id, None)
    if not task:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Stopped polling for game bot id=%s", bot_id)


async def reload_all_bots() -> None:
    for bot_id in list(_poll_tasks):
        await stop_bot_polling(bot_id)

    rows = await game_repository.list_active_bots_with_tokens()
    for row in rows:
        await start_bot_polling(int(row["id"]), str(row["token"]))

    logger.info("Reloaded %s active game bot(s)", len(rows))


def is_bot_polling(bot_id: int) -> bool:
    task = _poll_tasks.get(bot_id)
    return task is not None and not task.done()


async def stop_all_bots() -> None:
    for bot_id in list(_poll_tasks):
        await stop_bot_polling(bot_id)
