"""Основной сервис Telegram бота."""

import asyncio
import logging
from typing import Dict
from telethon import events
from telethon.client import TelegramClient

from config import settings
from .client_manager import TelegramClientManager
from .message_handler import MessageHandler
from .post_collector import PostCollector
from .post_publisher import PostPublisher
from .image_handler import ImageHandler
from .alert_service import AlertService, get_active_rules, message_matches_conditions


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class TelegramBotService:
    """Основной сервис для управления Telegram ботом."""

    def __init__(self):
        """Инициализация сервиса."""
        self.client_manager: TelegramClientManager = None
        self.message_handler = MessageHandler()
        self.post_collector = PostCollector()
        self.post_publisher: PostPublisher = None
        self.image_handler = ImageHandler()
        self.alert_service = AlertService(self.message_handler)
        self._running = False
        self._publisher_task = None
    
    async def start(self) -> None:
        """Запускает бота и регистрирует обработчики событий."""
        if self._running:
            logger.warning("Bot service is already running")
            return
        
        if not self.client_manager:
            logger.error("Client manager not set")
            return
        
        logger.info("Starting Telegram Bot Service...")
        
        # Загружаем и запускаем все клиенты
        await self.client_manager.start_all_clients()
        
        # Регистрируем обработчики для каждого клиента
        clients = self.client_manager.get_all_clients()
        
        for user_id, client in clients.items():
            profile = self.client_manager.get_profile(user_id)
            if not profile:
                continue

            if profile.get('collect_enabled'):
                chats_to_read = profile.get('chats_to_read', [])
                if chats_to_read:
                    chats_list = self.message_handler.get_chats_list(chats_to_read)
                    if chats_list:
                        self._register_collection_handler(client, user_id, profile, chats_list)
                        _log_action(
                            "Registered collection handler for user %s with %d chats",
                            user_id,
                            len(chats_list),
                        )
                    else:
                        logger.warning(f"Empty chats_list for user {user_id}")
                else:
                    logger.warning(f"No chats_to_read for user {user_id}")

            if profile.get('alert_enabled'):
                active_rules = get_active_rules(profile)
                for index, rule in enumerate(active_rules):
                    chats_list = self.message_handler.get_chats_list(rule.get('chats_to_read') or [])
                    if not chats_list:
                        continue
                    self._register_alert_handler(client, user_id, rule, chats_list, index)
                    _log_action(
                        "Registered alert handler for user %s rule %d with %d chats",
                        user_id,
                        index,
                        len(chats_list),
                    )

        # Запускаем фоновую задачу публикации постов
        self.post_publisher = PostPublisher(self.client_manager)
        self._publisher_task = asyncio.create_task(self._publisher_loop())

        self._running = True
        logger.info("Telegram Bot Service started successfully")

    async def _publisher_loop(self) -> None:
        """Цикл проверки и публикации постов со статусом ready."""
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
                logger.error(f"Error in publisher loop: {e}", exc_info=True)
    
    def _register_collection_handler(
        self,
        client: TelegramClient,
        user_id: int,
        profile: Dict,
        chats_list: list
    ) -> None:
        """Регистрирует обработчик сбора сообщений в tg_posts."""
        @client.on(events.NewMessage(chats=chats_list))
        async def handle_new_message(event: events.NewMessage.Event):
            """Обработчик новых сообщений. Сохраняет все сообщения в tg_posts."""
            try:
                _log_action("Processing message %s for user %s", event.message.id, user_id)
                
                images = await self.image_handler.download_images(event, user_id)
                
                post = await self.post_collector.save_post(
                    user_id=user_id,
                    event=event,
                    images=images,
                    profile=profile
                )
                
                if post:
                    _log_action("Successfully saved post %s for user %s", post.get('id'), user_id)
                else:
                    logger.error(f"Failed to save post for user {user_id}")
            
            except Exception as e:
                logger.error(f"Error handling message for user {user_id}: {e}", exc_info=True)

    def _register_alert_handler(
        self,
        client: TelegramClient,
        user_id: int,
        rule: Dict,
        chats_list: list,
        rule_index: int,
    ) -> None:
        """Регистрирует обработчик алертинга для одного правила."""
        @client.on(events.NewMessage(chats=chats_list))
        async def handle_alert_message(event: events.NewMessage.Event):
            try:
                if not message_matches_conditions(
                    event,
                    rule.get('save_conditions') or [],
                    self.message_handler,
                ):
                    return

                _log_action(
                    "Alert match for user %s rule %d message %s",
                    user_id,
                    rule_index,
                    event.message.id,
                )
                await self.alert_service.send_alert(client, rule, event)
            except Exception as e:
                logger.error(
                    "Error handling alert for user %s rule %d: %s",
                    user_id,
                    rule_index,
                    e,
                    exc_info=True,
                )
    
    async def stop(self) -> None:
        """Останавливает бота."""
        if not self._running:
            return

        logger.info("Stopping Telegram Bot Service...")
        self._running = False

        if self._publisher_task:
            self._publisher_task.cancel()
            try:
                await self._publisher_task
            except asyncio.CancelledError:
                pass
            self._publisher_task = None

        if self.client_manager:
            await self.client_manager.stop_all_clients()
        logger.info("Telegram Bot Service stopped")
    
    async def reload(self) -> None:
        """Перезагружает клиенты и обработчики."""
        logger.info("Reloading Telegram Bot Service...")
        await self.stop()
        await self.start()
    
    def is_running(self) -> bool:
        """Проверяет, запущен ли сервис."""
        return self._running
