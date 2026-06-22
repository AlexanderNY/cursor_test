"""Основной сервис Instagram бота: циклы сбора и публикации."""

import asyncio
import logging

from config import settings
from .post_collector import PostCollector
from .post_publisher import PostPublisher


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class InstagramBotService:
    """Оркестратор: сбор постов и публикация."""

    def __init__(self) -> None:
        self._post_collector = PostCollector()
        self._post_publisher = PostPublisher()
        self._running = False
        self._collect_task: asyncio.Task | None = None
        self._publisher_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            logger.warning("InstagramBotService already running")
            return
        logger.info("Starting InstagramBotService...")
        self._running = True
        self._collect_task = asyncio.create_task(self._collect_loop())
        self._publisher_task = asyncio.create_task(self._publisher_loop())
        logger.info("InstagramBotService started")

    async def _collect_loop(self) -> None:
        interval = max(60, getattr(settings, "INSTAGRAM_COLLECT_INTERVAL_SEC", 300))
        while self._running:
            try:
                saved = await self._post_collector.run_collect()
                _log_action("Collect loop: saved %d new instagram posts", saved)
                await asyncio.sleep(interval)
                if not self._running:
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Collect loop error: %s", e, exc_info=True)
                await asyncio.sleep(interval)

    async def _publisher_loop(self) -> None:
        interval = max(30, settings.PUBLISH_INTERVAL_SEC)
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                published = await self._post_publisher.publish_ready_posts()
                _log_action("Publisher loop: published %d instagram posts", published)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Publisher loop error: %s", e, exc_info=True)

    def is_running(self) -> bool:
        return self._running

    async def stop(self) -> None:
        if not self._running:
            return
        logger.info("Stopping InstagramBotService...")
        self._running = False
        if self._collect_task:
            self._collect_task.cancel()
            try:
                await self._collect_task
            except asyncio.CancelledError:
                pass
        if self._publisher_task:
            self._publisher_task.cancel()
            try:
                await self._publisher_task
            except asyncio.CancelledError:
                pass
        logger.info("InstagramBotService stopped")

    async def run_collect_once(self) -> int:
        """Один проход сбора (для ручного reload)."""
        return await self._post_collector.run_collect()
