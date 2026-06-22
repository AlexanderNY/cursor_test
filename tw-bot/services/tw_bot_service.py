"""Оркестратор tw-bot: публикация и сбор ленты."""

import asyncio
import logging

from config import settings
from .feed_collector import FeedCollector
from .post_publisher import PostPublisher

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class TwBotService:
    def __init__(self) -> None:
        self._publisher = PostPublisher()
        self._collector = FeedCollector()
        self._running = False
        self._pub_task: asyncio.Task | None = None
        self._feed_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            logger.warning("TwBotService already running")
            return
        logger.info("Starting TwBotService...")
        self._running = True
        self._pub_task = asyncio.create_task(self._publisher_loop())
        self._feed_task = asyncio.create_task(self._feed_loop())
        logger.info("TwBotService started")

    async def _publisher_loop(self) -> None:
        interval = max(30, settings.PUBLISH_INTERVAL_SEC)
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                n = await self._publisher.publish_ready_posts()
                _log_action("Publisher: published %d tw_posts", n)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Publisher loop: %s", e, exc_info=True)

    async def _feed_loop(self) -> None:
        interval = max(120, settings.FEED_COLLECT_INTERVAL_SEC)
        while self._running:
            try:
                n = await self._collector.run_collect()
                _log_action("Feed collect: saved %d new tweets", n)
                await asyncio.sleep(interval)
                if not self._running:
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Feed loop: %s", e, exc_info=True)
                await asyncio.sleep(interval)

    async def stop(self) -> None:
        if not self._running:
            return
        logger.info("Stopping TwBotService...")
        self._running = False
        for t in (self._pub_task, self._feed_task):
            if t:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
        logger.info("TwBotService stopped")

    def is_running(self) -> bool:
        return self._running

    async def run_schedule_pass(self) -> dict[str, int]:
        """Один проход публикации и сбора по запросу scheduler."""
        published = await self._publisher.publish_ready_posts()
        collected = await self._collector.run_collect()
        return {"published": published, "collected": collected}
