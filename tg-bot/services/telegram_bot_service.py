"""Основной сервис Telegram бота."""

import asyncio
import logging
from typing import Dict, Set

from telethon import events
from telethon.client import TelegramClient

from config import settings
from .client_manager import TelegramClientManager
from .message_handler import MessageHandler
from .post_collector import PostCollector
from .post_publisher import PostPublisher
from .image_handler import ImageHandler
from .alert_service import AlertService
from .routing_engine import RoutingEngine, ensure_rule_ids
from .event_logger import EventLogger
from .post_enrichment import PostEnrichmentService
from .summary_aggregator import SummaryAggregator


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class TelegramBotService:
    """Основной сервис для управления Telegram ботом."""

    def __init__(self):
        self.client_manager: TelegramClientManager = None
        self.message_handler = MessageHandler()
        self.post_collector = PostCollector()
        self.post_publisher: PostPublisher = None
        self.image_handler = ImageHandler()
        self.alert_service = AlertService(self.message_handler)
        self.event_logger = EventLogger()
        self.routing_engine = RoutingEngine(
            self.message_handler,
            self.alert_service,
            self.event_logger,
        )
        self.post_enrichment = PostEnrichmentService()
        self.summary_aggregator = SummaryAggregator()
        self._running = False
        self._publisher_task = None
        self._maintenance_task = None
        self._digest_task = None

    async def start(self) -> None:
        if self._running:
            logger.warning("Bot service is already running")
            return

        if not self.client_manager:
            logger.error("Client manager not set")
            return

        logger.info("Starting Telegram Bot Service...")
        await self.client_manager.start_all_clients()

        clients = self.client_manager.get_all_clients()
        for user_id, client in clients.items():
            profile = self.client_manager.get_profile(user_id)
            if not profile:
                continue

            ensure_rule_ids(profile)
            chats = self._collect_monitored_chats(profile)
            if chats:
                self._register_unified_handler(client, user_id, profile, chats)
                _log_action(
                    "Registered unified handler for user %s with %d chats",
                    user_id,
                    len(chats),
                )

        self.post_publisher = PostPublisher(self.client_manager)
        self._publisher_task = asyncio.create_task(self._publisher_loop())
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        self._digest_task = asyncio.create_task(self._digest_loop())

        self._running = True
        logger.info("Telegram Bot Service started successfully")

    def _collect_monitored_chats(self, profile: Dict) -> list:
        chats: Set[str] = set()
        if profile.get("collect_enabled"):
            for chat in profile.get("chats_to_read") or []:
                if chat:
                    chats.add(str(chat).strip())

        if profile.get("alert_enabled"):
            from .alert_service import get_active_rules

            for rule in get_active_rules(profile):
                for chat in rule.get("chats_to_read") or []:
                    if chat:
                        chats.add(str(chat).strip())

        return self.message_handler.get_chats_list(list(chats))

    async def _publisher_loop(self) -> None:
        interval = settings.PUBLISH_INTERVAL_SEC
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                published = await self.post_publisher.publish_ready_posts()
                _log_action("Publisher loop: published %d posts", published)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in publisher loop: %s", e, exc_info=True)

    async def _maintenance_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                if not self._running:
                    break
                removed_events = await self.event_logger.cleanup_old_events()
                removed_dedup = await self.event_logger.cleanup_expired_dedup()
                _log_action(
                    "Maintenance: removed %d old events, %d expired dedup entries",
                    removed_events,
                    removed_dedup,
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in maintenance loop: %s", e, exc_info=True)

    async def _digest_loop(self) -> None:
        while self._running:
            try:
                sleep_sec = await self.summary_aggregator.get_digest_sleep_interval_sec()
                await asyncio.sleep(sleep_sec)
                if not self._running:
                    break
                sent = await self.summary_aggregator.run_digest_cycle(self.client_manager)
                _log_action("Digest loop: sent %d digests (next in %ds)", sent, sleep_sec)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in digest loop: %s", e, exc_info=True)

    def _register_unified_handler(
        self,
        client: TelegramClient,
        user_id: int,
        profile: Dict,
        chats_list: list,
    ) -> None:
        @client.on(events.NewMessage(chats=chats_list))
        async def handle_new_message(event: events.NewMessage.Event):
            try:
                _log_action("Processing message %s for user %s", event.message.id, user_id)

                message_metadata: Dict = {}
                collect_chat = self.message_handler.chat_id_in_list(
                    event.chat_id,
                    profile.get("chats_to_read") or [],
                )

                if profile.get("collect_enabled") and collect_chat:
                    save_conditions = profile.get("save_conditions") or []
                    should_save = self.message_handler.should_save_message(event, save_conditions)
                    if should_save:
                        images = await self.image_handler.download_images(event, user_id)
                        post = await self.post_collector.save_post(
                            user_id=user_id,
                            event=event,
                            images=images,
                            profile=profile,
                        )
                        if post:
                            await self.event_logger.log_event(
                                user_id,
                                "collected",
                                event,
                                metadata={"post_id": post.get("id")},
                            )
                            enrichment = await self.post_enrichment.enrich_post_if_enabled(
                                post_id=post["id"],
                                text=post.get("post_text") or "",
                                profile=profile,
                            )
                            if enrichment:
                                message_metadata = enrichment
                            _log_action("Saved post %s for user %s", post.get("id"), user_id)

                if profile.get("alert_enabled"):
                    await self.routing_engine.process(
                        client=client,
                        user_id=user_id,
                        profile=profile,
                        event=event,
                        message_metadata=message_metadata,
                    )

            except Exception as e:
                logger.error("Error handling message for user %s: %s", user_id, e, exc_info=True)

    async def stop(self) -> None:
        if not self._running:
            return

        logger.info("Stopping Telegram Bot Service...")
        self._running = False

        for task in (self._publisher_task, self._maintenance_task, self._digest_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._publisher_task = None
        self._maintenance_task = None
        self._digest_task = None

        if self.client_manager:
            await self.client_manager.stop_all_clients()
        logger.info("Telegram Bot Service stopped")

    async def reload(self) -> None:
        logger.info("Reloading Telegram Bot Service...")
        await self.stop()
        await self.start()

    def is_running(self) -> bool:
        return self._running
