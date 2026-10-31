"""Управление polling нескольких игровых ботов."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bots.game_bot_runner import attach_game_routers
from services.bot_registry import set_bot_mapping
from services.game_repository import game_repository
from services.order_desk_seed import ensure_order_desk

logger = logging.getLogger(__name__)

_dispatcher: Dispatcher | None = None
_polling_task: asyncio.Task | None = None
_polling_game_ids: set[int] = set()
_reload_lock = asyncio.Lock()


def _shared_dispatcher() -> Dispatcher:
    global _dispatcher
    if _dispatcher is None:
        dispatcher = Dispatcher()
        attach_game_routers(dispatcher)
        _dispatcher = dispatcher
    return _dispatcher


def _on_polling_done(task: asyncio.Task) -> None:
    error = None
    if not task.cancelled():
        error = task.exception()
        if error:
            logger.error("Game bots polling crashed: %s", error, exc_info=error)
    if task is not _polling_task:
        return
    _polling_game_ids.clear()
    if error:
        set_bot_mapping({})


async def _stop_polling() -> None:
    global _polling_task
    task = _polling_task
    _polling_task = None
    _polling_game_ids.clear()
    set_bot_mapping({})
    if task is None:
        return
    if not task.done() and _dispatcher is not None:
        try:
            await _dispatcher.stop_polling()
        except RuntimeError:
            task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Game bots polling stopped with an error")


async def _prepare_bot(bot_id: int, token: str) -> tuple[Bot, int, str | None] | None:
    cleaned = token.strip()
    if not cleaned:
        logger.warning("Bot token is empty for bot_id=%s; polling skipped.", bot_id)
        return None

    try:
        await game_repository.ensure_country_modes(bot_id)
    except Exception:
        logger.exception("Failed to ensure country modes for bot_id=%s", bot_id)

    try:
        await ensure_order_desk(bot_id)
    except Exception:
        logger.exception("Failed to ensure order desk for bot_id=%s", bot_id)

    bot = Bot(token=cleaned)
    try:
        me = await bot.get_me()
    except Exception:
        logger.exception("Telegram getMe failed for bot_id=%s; polling skipped.", bot_id)
        await bot.session.close()
        return None
    return bot, int(me.id), me.username


async def reload_all_bots() -> None:
    async with _reload_lock:
        await _stop_polling()

        rows = await game_repository.list_active_bots_with_tokens()
        bots: list[Bot] = []
        mapping: dict[int, int] = {}
        started_ids: set[int] = set()
        for row in rows:
            bot_id = int(row["id"])
            prepared = await _prepare_bot(bot_id, str(row["token"]))
            if prepared is None:
                continue
            bot, telegram_bot_id, username = prepared
            if telegram_bot_id in mapping:
                logger.error(
                    "Telegram bot id=%s is already mapped to game bot id=%s; skip game bot id=%s",
                    telegram_bot_id,
                    mapping[telegram_bot_id],
                    bot_id,
                )
                await bot.session.close()
                continue
            mapping[telegram_bot_id] = bot_id
            bots.append(bot)
            started_ids.add(bot_id)
            logger.info(
                "Prepared game bot id=%s as @%s (%s)",
                bot_id,
                username or telegram_bot_id,
                telegram_bot_id,
            )

        set_bot_mapping(mapping)
        if not bots:
            logger.info("No active game bots to poll")
            return

        dispatcher = _shared_dispatcher()
        task = asyncio.create_task(
            dispatcher.start_polling(*bots, handle_signals=False),
            name="game-bots-polling",
        )
        task.add_done_callback(_on_polling_done)
        global _polling_task
        _polling_task = task
        _polling_game_ids.update(started_ids)
        logger.info("Started polling for %s game bot(s): %s", len(started_ids), sorted(started_ids))


def is_bot_polling(bot_id: int) -> bool:
    task = _polling_task
    return bot_id in _polling_game_ids and task is not None and not task.done()


async def stop_all_bots() -> None:
    async with _reload_lock:
        await _stop_polling()
