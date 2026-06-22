"""Оркестратор dzen-bot: публикация и сбор ленты."""

import asyncio
import logging

from config import settings

from .dzen_feed_collector import DzenFeedCollector
from .dzen_post_publisher import DzenPostPublisher

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class DzenBotService:
    """Фоновые циклы публикации (ready → Дзен) и сбора студии (collected)."""

    def __init__(self) -> None:
        self._publisher = DzenPostPublisher()
        self._collector = DzenFeedCollector()
        self._running = False
        self._publish_task: asyncio.Task | None = None
        self._collect_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            logger.warning("DzenBotService already running")
            return
        self._running = True
        self._publish_task = asyncio.create_task(self._publish_loop())
        self._collect_task = asyncio.create_task(self._collect_loop())
        logger.info("DzenBotService started")

    async def _publish_loop(self) -> None:
        interval = max(45, settings.PUBLISH_INTERVAL_SEC)
        while self._running:
            try:
                n = await self._publisher.publish_ready_posts()
                if n:
                    _log_action("Publish loop: %d dzen post(s)", n)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Dzen publish loop error: %s", e, exc_info=True)
                await asyncio.sleep(interval)

    async def _collect_loop(self) -> None:
        interval = max(120, settings.COLLECT_INTERVAL_SEC)
        while self._running:
            try:
                n = await self._collector.run_collect()
                if n:
                    _log_action("Collect loop: %d new link(s) in dzen_posts", n)
                await asyncio.sleep(interval)
                if not self._running:
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Dzen collect loop error: %s", e, exc_info=True)
                await asyncio.sleep(interval)

    def is_running(self) -> bool:
        return self._running

    async def stop(self) -> None:
        self._running = False
        for t in (self._publish_task, self._collect_task):
            if t:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
        self._publish_task = None
        self._collect_task = None
        logger.info("DzenBotService stopped")

    async def run_publish_once(self) -> int:
        """Один проход публикации."""
        return await self._publisher.publish_ready_posts()

    async def run_collect_once(self) -> int:
        """Один проход сбора студии."""
        return await self._collector.run_collect()
