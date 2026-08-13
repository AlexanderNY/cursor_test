"""Основной сервис Telegram бота."""

import asyncio
import logging
from typing import Dict, List, Set

from telethon import events
from telethon.client import TelegramClient

from config import settings
from shared.circuit_breaker import get_breaker
from .client_manager import TelegramClientManager
from .message_handler import MessageHandler
from .post_collector import PostCollector
from .post_publisher import PostPublisher
from .engagement_service import EngagementService
from .image_handler import ImageHandler
from .alert_service import AlertService
from .routing_engine import RoutingEngine, ensure_rule_ids
from .event_logger import EventLogger
from .post_enrichment import PostEnrichmentService
from .summary_aggregator import SummaryAggregator
from .discussion_bindings import list_discussion_bindings
from .inbox_ingest import push_inbox_ingest
from .brand_channel_flow import (
    list_tg_flow_channels,
    find_channel_for_chat,
    channel_alert_rules_as_profile_rules,
)


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
        self.engagement_service: EngagementService = None
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
        self._engagement_task = None
        self._discussion_refresh_task = None
        self._discussion_map: Dict[str, List[dict]] = {}
        self._brand_channels: List[dict] = []

    async def start(self) -> None:
        if self._running:
            logger.warning("Bot service is already running")
            return

        if not self.client_manager:
            logger.error("Client manager not set")
            return

        logger.info("Starting Telegram Bot Service...")
        await self.client_manager.start_all_clients()
        await self._refresh_flow_maps()

        clients = self.client_manager.get_all_clients()
        for user_id, client in clients.items():
            profile = self.client_manager.get_profile(user_id)
            if not profile:
                continue

            ensure_rule_ids(profile)
            chats = self._collect_monitored_chats(profile, user_id)
            if chats:
                self._register_unified_handler(client, user_id, profile, chats)
                _log_action(
                    "Registered unified handler for user %s with %d chats",
                    user_id,
                    len(chats),
                )

        self.post_publisher = PostPublisher(self.client_manager)
        self.engagement_service = EngagementService(self.client_manager)
        self._running = True
        self._publisher_task = asyncio.create_task(self._publisher_loop())
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        self._digest_task = asyncio.create_task(self._digest_loop())
        self._engagement_task = asyncio.create_task(self._engagement_loop())
        self._discussion_refresh_task = asyncio.create_task(self._discussion_refresh_loop())

        logger.info("Telegram Bot Service started successfully")

    async def _refresh_flow_maps(self) -> None:
        await self._refresh_discussion_map()
        self._brand_channels = await list_tg_flow_channels()
        _log_action("Brand flow channels: %d", len(self._brand_channels))

    async def _refresh_discussion_map(self) -> None:
        bindings = await list_discussion_bindings()
        mapping: Dict[str, List[dict]] = {}
        for b in bindings:
            key = str(b["discussion_id"]).strip()
            mapping.setdefault(key, []).append(b)
        self._discussion_map = mapping
        _log_action("Discussion map: %d chats", len(mapping))

    async def _discussion_refresh_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(60)
                if not self._running:
                    break
                await self._refresh_flow_maps()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("discussion refresh error: %s", e, exc_info=True)

    def _collect_monitored_chats(self, profile: Dict, user_id: int) -> list:
        chats: Set[str] = set()
        if profile.get("collect_enabled"):
            for chat in profile.get("chats_to_read") or []:
                chat_id = self.message_handler.chat_ref_id(chat)
                if chat_id:
                    chats.add(chat_id)

        if profile.get("alert_enabled"):
            from .alert_service import get_active_rules

            for rule in get_active_rules(profile):
                for chat in rule.get("chats_to_read") or []:
                    chat_id = self.message_handler.chat_ref_id(chat)
                    if chat_id:
                        chats.add(chat_id)

        for ch in self._brand_channels:
            if ch.get("user_id") != user_id:
                continue
            ext = str(ch.get("external_id") or "").strip()
            if ext:
                chats.add(ext)

        for disc_id, bindings in self._discussion_map.items():
            if any(b["user_id"] == user_id for b in bindings):
                chats.add(disc_id)

        return self.message_handler.get_chats_list(list(chats))

    async def _publisher_loop(self) -> None:
        interval = settings.PUBLISH_INTERVAL_SEC
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                if not get_breaker("telegram").allow_request():
                    logger.warning("Publisher loop skipped: telegram circuit open")
                    continue
                if self.post_publisher:
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
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in maintenance loop: %s", e, exc_info=True)

    async def _digest_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(1800)
                if not self._running:
                    break
                sent = await self.summary_aggregator.run_digest_cycle(self.client_manager)
                _log_action("Digest loop: sent %d digests", sent)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in digest loop: %s", e, exc_info=True)

    async def _engagement_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(900)
                if not self._running:
                    break
                if self.engagement_service:
                    updated = await self.engagement_service.refresh_engagement(limit=50)
                    _log_action("Engagement loop: updated %d posts", updated)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in engagement loop: %s", e, exc_info=True)

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

                await self._maybe_ingest_discussion_comment(user_id, event)

                message_metadata: Dict = {}
                brand_ch = await find_channel_for_chat(
                    user_id, event.chat_id, self._brand_channels
                )

                profile_collect = self.message_handler.chat_id_in_list(
                    event.chat_id,
                    profile.get("chats_to_read") or [],
                )
                channel_collect = bool(brand_ch and brand_ch.get("collect_enabled"))

                if (profile.get("collect_enabled") and profile_collect) or channel_collect:
                    if channel_collect and brand_ch is not None:
                        save_conditions = brand_ch.get("save_conditions") or []
                        collect_profile = dict(profile)
                        processing = brand_ch.get("processing") or {}
                        if isinstance(processing, dict) and processing:
                            collect_profile.update(processing)
                            if processing.get("process_services") is not None:
                                collect_profile["process_services"] = processing.get(
                                    "process_services"
                                )
                    else:
                        save_conditions = profile.get("save_conditions") or []
                        collect_profile = profile

                    should_save = self.message_handler.should_save_message(
                        event, save_conditions
                    )
                    if should_save:
                        images = await self.image_handler.download_images(event, user_id)
                        post = await self.post_collector.save_post(
                            user_id=user_id,
                            event=event,
                            images=images,
                            profile=collect_profile,
                        )
                        if post:
                            await self.event_logger.log_event(
                                user_id,
                                "collected",
                                event,
                                metadata={
                                    "post_id": post.get("id"),
                                    "brand_channel_id": brand_ch.get("id") if brand_ch else None,
                                },
                            )
                            enrichment = await self.post_enrichment.enrich_post_if_enabled(
                                post_id=post["id"],
                                text=post.get("post_text") or "",
                                profile=collect_profile,
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

                if brand_ch and brand_ch.get("alert_enabled"):
                    channel_rules = channel_alert_rules_as_profile_rules(brand_ch)
                    if channel_rules:
                        channel_profile = {
                            "alert_enabled": True,
                            "alert_rules": channel_rules,
                        }
                        await self.routing_engine.process(
                            client=client,
                            user_id=user_id,
                            profile=channel_profile,
                            event=event,
                            message_metadata=message_metadata,
                        )

            except Exception as e:
                logger.error("Error handling message for user %s: %s", user_id, e, exc_info=True)

    async def _maybe_ingest_discussion_comment(
        self, user_id: int, event: events.NewMessage.Event
    ) -> None:
        chat_key = str(event.chat_id)
        bindings = [
            b for b in (self._discussion_map.get(chat_key) or []) if b["user_id"] == user_id
        ]
        if not bindings:
            for disc_id, blist in self._discussion_map.items():
                if self.message_handler.chat_id_in_list(event.chat_id, [disc_id]):
                    bindings = [b for b in blist if b["user_id"] == user_id]
                    if bindings:
                        break
        if not bindings:
            return
        if getattr(event.message, "out", False):
            return
        text = event.raw_text or (event.message.message if event.message else "") or ""
        sender = await event.get_sender()
        author = None
        if sender:
            author = (
                getattr(sender, "username", None)
                or getattr(sender, "first_name", None)
                or getattr(sender, "title", None)
            )
            if author:
                author = str(author)[:255]
        reply_to = getattr(event.message, "reply_to_msg_id", None)
        msg_id = event.message.id
        await push_inbox_ingest(
            user_id=user_id,
            network="tg",
            external_id=chat_key,
            text=text,
            author=author,
            external_msg_id=f"tg:{chat_key}:{msg_id}",
            item_type="comment",
            meta={
                "tg_msg_id": msg_id,
                "reply_to_msg_id": reply_to,
                "discussion_id": chat_key,
            },
        )
        _log_action("Ingested discussion comment user=%s chat=%s msg=%s", user_id, chat_key, msg_id)

    async def stop(self) -> None:
        if not self._running:
            return

        logger.info("Stopping Telegram Bot Service...")
        self._running = False

        for task in (
            self._publisher_task,
            self._maintenance_task,
            self._digest_task,
            self._engagement_task,
            self._discussion_refresh_task,
        ):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._publisher_task = None
        self._maintenance_task = None
        self._digest_task = None
        self._engagement_task = None
        self._discussion_refresh_task = None

        if self.client_manager:
            await self.client_manager.stop_all_clients()
        logger.info("Telegram Bot Service stopped")

    async def reload(self) -> None:
        logger.info("Reloading Telegram Bot Service...")
        await self.stop()
        await self.start()

    def is_running(self) -> bool:
        return self._running
