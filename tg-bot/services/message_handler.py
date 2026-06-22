"""Обработка входящих сообщений Telegram."""

import logging
from typing import List, Optional, Dict
from telethon import events


logger = logging.getLogger(__name__)


class MessageHandler:
    """Обработчик сообщений Telegram."""
    
    @staticmethod
    def should_save_message(event: events.NewMessage.Event, save_conditions: List[str]) -> bool:
        """Проверяет, нужно ли сохранять сообщение на основе Save Conditions.
        
        Args:
            event: Событие нового сообщения
            save_conditions: Список условий для сохранения
            
        Returns:
            True если сообщение нужно сохранить, False иначе
        """
        if not save_conditions:
            # Если условий нет - сохранять все сообщения
            return True
        
        # Получаем текст сообщения
        raw_text = event.raw_text or ""
        
        # Проверяем каждое условие в тексте сообщения
        for condition in save_conditions:
            if condition and condition in raw_text:
                logger.debug(f"Message matches condition: {condition}")
                return True
        
        logger.debug("Message does not match any save conditions")
        return False
    
    @staticmethod
    async def extract_message_data(event: events.NewMessage.Event) -> Dict:
        """Извлекает данные из сообщения.
        
        Args:
            event: Событие нового сообщения
            
        Returns:
            Словарь с данными сообщения
        """
        message = event.message
        sender = await event.get_sender()
        
        # Извлекаем текст
        text = message.message or ""
        
        # Извлекаем метаданные
        data = {
            'text': text,
            'raw_text': event.raw_text or "",
            'message_id': message.id,
            'date': message.date,
            'author_id': sender.id if sender else None,
            'author_username': getattr(sender, 'username', None) if sender else None,
            'author_title': getattr(sender, 'title', None) if sender else None,
            'chat_id': event.chat_id,
            'has_media': message.media is not None,
            'media': message.media,
        }
        
        return data
    
    @staticmethod
    def get_chats_list(chats_to_read: List) -> List:
        """Преобразует chats_to_read в список для telethon.
        
        Args:
            chats_to_read: Список чатов из БД (может быть строками или числами)
            
        Returns:
            Список чатов для telethon
        """
        if not chats_to_read:
            return []
        
        result = []
        for chat in chats_to_read:
            # Если это строка, пытаемся преобразовать в число (ID канала)
            if isinstance(chat, str):
                try:
                    # Убираем @ если есть
                    if chat.startswith('@'):
                        result.append(chat)
                    else:
                        # Пытаемся преобразовать в число
                        result.append(int(chat))
                except ValueError:
                    # Если не число, используем как есть (username)
                    result.append(chat)
            else:
                result.append(chat)
        
        return result
