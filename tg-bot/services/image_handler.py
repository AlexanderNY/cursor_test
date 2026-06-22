"""Обработка изображений из Telegram сообщений."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from telethon import events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from config import settings


logger = logging.getLogger(__name__)


class ImageHandler:
    """Обработчик изображений из сообщений Telegram."""
    
    def __init__(self):
        """Инициализация обработчика изображений."""
        self.uploads_dir = Path(settings.UPLOADS_DIR)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_images(
        self,
        event: events.NewMessage.Event,
        user_id: int
    ) -> List[str]:
        """Скачивает изображения из сообщения.
        
        Args:
            event: Событие нового сообщения
            user_id: ID пользователя для создания структуры папок
            
        Returns:
            Список относительных путей к сохраненным изображениям
        """
        message = event.message
        
        if not message.media:
            return []
        
        # Проверяем тип медиа
        if not isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
            logger.debug(f"Media type {type(message.media)} is not an image")
            return []
        
        # Проверяем, является ли документ изображением
        mime_type = None
        if isinstance(message.media, MessageMediaDocument):
            # Проверяем mime_type документа
            if not hasattr(message.media, 'document') or not message.media.document:
                return []
            
            mime_type = getattr(message.media.document, 'mime_type', '')
            if not mime_type or not mime_type.startswith('image/'):
                logger.debug(f"Document mime_type {mime_type} is not an image")
                return []
        
        # Создаем структуру папок: uploads/tg/{user_id}/{date}/
        date_str = datetime.now().strftime("%Y-%m-%d")
        user_dir = self.uploads_dir / str(user_id) / date_str
        user_dir.mkdir(parents=True, exist_ok=True)
        
        image_paths = []
        
        try:
            # Скачиваем медиа
            timestamp = datetime.now().strftime("%f")
            file_path = user_dir / f"{timestamp}_{message.id}"
            
            # Скачиваем файл
            downloaded_path = await event.download_media(file=str(file_path))
            
            if downloaded_path:
                # Получаем расширение файла
                if isinstance(message.media, MessageMediaPhoto):
                    ext = '.jpg'  # По умолчанию для фото
                else:
                    # Используем уже полученный mime_type
                    ext_map = {
                        'image/jpeg': '.jpg',
                        'image/png': '.png',
                        'image/gif': '.gif',
                        'image/webp': '.webp',
                    }
                    ext = ext_map.get(mime_type, '.jpg') if mime_type else '.jpg'
                
                # Переименовываем файл с правильным расширением
                final_path = Path(downloaded_path).with_suffix(ext)
                if downloaded_path != str(final_path):
                    os.rename(downloaded_path, final_path)
                
                # Сохраняем относительный путь
                relative_path = f"/{settings.UPLOADS_DIR}/{user_id}/{date_str}/{final_path.name}"
                image_paths.append(relative_path)
                logger.info(f"Downloaded image: {relative_path}")
        
        except Exception as e:
            logger.error(f"Error downloading image from message {message.id}: {e}", exc_info=True)
        
        return image_paths
