"""Роутер для получения списка доступных каналов пользователя."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from schemas import ChannelItem
from services.client_manager import TelegramClientManager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["Telegram Channels"])

client_manager: Optional[TelegramClientManager] = None


def set_client_manager(manager: TelegramClientManager) -> None:
    """Устанавливает менеджер клиентов для роутера."""
    global client_manager
    client_manager = manager


@router.get("/{user_id}", response_model=List[ChannelItem])
async def get_available_channels(user_id: int) -> List[ChannelItem]:
    """Возвращает список каналов, доступных клиенту пользователя (iter_dialogs, только каналы)."""
    if not client_manager:
        raise HTTPException(status_code=503, detail="Client manager not initialized")

    client = client_manager.get_client(user_id)
    if not client:
        raise HTTPException(
            status_code=404,
            detail="Telegram client not available. Save profile, authorize, and ensure tg-bot has loaded your profile (e.g. reload)."
        )

    channels: List[ChannelItem] = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                title = getattr(dialog, "title", None) or str(dialog.name or "")
                channels.append(ChannelItem(id=dialog.id, title=title))
    except Exception as e:
        logger.exception("Error listing channels for user_id=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to list channels: {e!s}") from e

    return channels
