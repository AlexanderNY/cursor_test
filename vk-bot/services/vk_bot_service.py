"""Основной сервис VK бота: циклы сбора и публикации."""

import asyncio
import logging

from config import settings
from shared.circuit_breaker import get_breaker
from .post_collector import PostCollector
from .post_publisher import PostPublisher
from .engagement_service import VkEngagementService
from .subscriber_service import VkSubscriberService


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class VkBotService:
    """Оркестратор: сбор постов и публикация."""

    def __init__(self) -> None:
        self._post_collector = PostCollector()
        self._post_publisher = PostPublisher()
        self._engagement_service = VkEngagementService()
        self._subscriber_service = VkSubscriberService()
        self._running = False
        self._collect_task: asyncio.Task | None = None
        self._publisher_task: asyncio.Task | None = None
        self._engagement_task: asyncio.Task | None = None
        self._subscriber_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            logger.warning("VkBotService already running")
            return
        logger.info("Starting VkBotService...")
        self._running = True
        self._collect_task = asyncio.create_task(self._collect_loop())
        self._publisher_task = asyncio.create_task(self._publisher_loop())
        self._engagement_task = asyncio.create_task(self._engagement_loop())
        self._subscriber_task = asyncio.create_task(self._subscriber_loop())
        logger.info("VkBotService started")

    async def _collect_loop(self) -> None:
        interval = max(60, settings.VK_COLLECT_INTERVAL_SEC)
        while self._running:
            try:
                if not get_breaker("vk_api").allow_request():
                    logger.warning("Collect loop skipped: VK circuit open")
                    await asyncio.sleep(interval)
                    continue
                saved = await self._post_collector.run_collect()
                _log_action("Collect loop: saved %d new vk posts", saved)
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
                if not get_breaker("vk_api").allow_request():
                    logger.warning("Publisher loop skipped: VK circuit open")
                    continue
                published = await self._post_publisher.publish_ready_posts()
                _log_action("Publisher loop: published %d vk posts", published)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Publisher loop error: %s", e, exc_info=True)

    async def _engagement_loop(self) -> None:
        interval = max(300, getattr(settings, "ENGAGEMENT_INTERVAL_SEC", 900))
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                updated = await self._engagement_service.refresh_engagement(limit=100)
                _log_action("Engagement loop: updated %d vk posts", updated)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Engagement loop error: %s", e, exc_info=True)

    async def _subscriber_loop(self) -> None:
        interval = max(3600, getattr(settings, "SUBSCRIBER_INTERVAL_SEC", 86400))
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                updated = await self._subscriber_service.sync_subscribers()
                _log_action("Subscriber loop: updated %d vk channels", updated)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Subscriber loop error: %s", e, exc_info=True)

    def is_running(self) -> bool:
        return self._running

    async def stop(self) -> None:
        if not self._running:
            return
        logger.info("Stopping VkBotService...")
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
        if self._engagement_task:
            self._engagement_task.cancel()
            try:
                await self._engagement_task
            except asyncio.CancelledError:
                pass
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
        logger.info("VkBotService stopped")

    async def run_collect_once(self) -> int:
        """Один проход сбора (для ручного reload)."""
        return await self._post_collector.run_collect()
