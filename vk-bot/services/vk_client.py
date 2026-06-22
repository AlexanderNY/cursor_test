"""Обёртка над vk_api для вызова в executor (синхронный API)."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import vk_api
from vk_api import VkUpload

logger = logging.getLogger(__name__)


def _wall_get_sync(access_token: str, owner_id: int, count: int = 20) -> Dict[str, Any]:
    """Синхронный вызов wall.get. owner_id для группы отрицательный (например -123456)."""
    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()
    return vk.wall.get(owner_id=owner_id, count=count, filter="owner")


def _wall_post_sync(
    access_token: str,
    owner_id: int,
    message: str,
    from_group: bool = True,
    attachments: Optional[str] = None,
) -> Dict[str, Any]:
    """Синхронный вызов wall.post. owner_id — ID владельца стены (положительный — пользователь, отрицательный — группа)."""
    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()
    params = {
        "owner_id": owner_id,
        "message": message[:16384] if message else "",
        "from_group": 1 if from_group and owner_id < 0 else 0,
    }
    if attachments:
        params["attachments"] = attachments
    return vk.wall.post(**params)


def _users_get_sync(access_token: str) -> Optional[int]:
    """Синхронный вызов users.get без параметров — возвращает id текущего пользователя по токену."""
    try:
        vk_session = vk_api.VkApi(token=access_token)
        vk = vk_session.get_api()
        resp = vk.users.get()
        if resp and len(resp) > 0:
            return resp[0].get("id")
    except Exception as e:
        logger.warning("users.get failed (token may be group/service or invalid): %s", e)
    return None


def _upload_photo_wall_sync(
    access_token: str, photo_path: str, owner_id: int
) -> Optional[str]:
    """Загружает фото на стену. owner_id > 0 — пользователь, < 0 — группа.

    Для группы VK требует **пользовательский** access_token (photos.getWallUploadServer недоступен с токеном сообщества).
    """
    try:
        vk_session = vk_api.VkApi(token=access_token)
        upload = VkUpload(vk_session)
        if owner_id > 0:
            photo_list = upload.photo_wall(photo_path, user_id=owner_id)
        else:
            photo_list = upload.photo_wall(photo_path, group_id=abs(owner_id))
        if not photo_list:
            return None
        p = photo_list[0]
        return f"photo{p['owner_id']}_{p['id']}"
    except Exception as e:
        logger.warning("photo_wall upload failed (owner_id=%s, path=%s): %s", owner_id, photo_path, e, exc_info=True)
        return None


def _upload_document_wall_sync(
    access_token: str, file_path: str, owner_id: int, title: Optional[str] = None
) -> Optional[str]:
    """Загружает документ на стену. owner_id > 0 — пользователь, < 0 — группа. Возвращает строку вложения doc{owner_id}_{id}."""
    try:
        vk_session = vk_api.VkApi(token=access_token)
        upload = VkUpload(vk_session)
        title = title or "document"
        if owner_id < 0:
            doc_list = upload.document_wall(file_path, title=title, group_id=abs(owner_id))
        else:
            doc_list = upload.document_wall(file_path, title=title)
        if not doc_list:
            return None
        d = doc_list[0]
        return f"doc{d['owner_id']}_{d['id']}"
    except Exception as e:
        logger.warning("document_wall upload failed (owner_id=%s, path=%s): %s", owner_id, file_path, e, exc_info=True)
        return None


class VkClient:
    """Клиент VK API. Вызовы выполняются в executor, чтобы не блокировать event loop."""

    def __init__(self, access_token: str):
        self._access_token = access_token

    async def get_current_user_id(self) -> Optional[int]:
        """Возвращает id текущего пользователя по токену (users.get)."""
        return await asyncio.to_thread(_users_get_sync, self._access_token)

    async def wall_get(self, owner_id: int, count: int = 20) -> List[Dict[str, Any]]:
        """Получает посты со стены. owner_id для группы — отрицательное число."""
        try:
            result = await asyncio.to_thread(
                _wall_get_sync, self._access_token, owner_id, count
            )
            return result.get("items") or []
        except Exception as e:
            logger.error("wall.get owner_id=%s error: %s", owner_id, e, exc_info=True)
            return []

    async def wall_post(
        self,
        owner_id: int,
        message: str,
        from_group: bool = True,
        attachments: Optional[str] = None,
    ) -> Optional[int]:
        """Публикует пост на стену. owner_id: положительный — пользователь, отрицательный — группа. Возвращает post_id при успехе."""
        try:
            result = await asyncio.to_thread(
                _wall_post_sync,
                self._access_token,
                owner_id,
                message,
                from_group,
                attachments,
            )
            return result.get("post_id")
        except Exception as e:
            logger.error("wall.post owner_id=%s error: %s", owner_id, e, exc_info=True)
            return None

    async def upload_photo_wall(self, photo_path: str, owner_id: int) -> Optional[str]:
        """Загружает фото на стену. Возвращает строку вложения photo{owner_id}_{id}."""
        return await asyncio.to_thread(
            _upload_photo_wall_sync, self._access_token, photo_path, owner_id
        )

    async def upload_document_wall(
        self, file_path: str, owner_id: int, title: Optional[str] = None
    ) -> Optional[str]:
        """Загружает документ на стену. Возвращает строку вложения doc{owner_id}_{id}."""
        return await asyncio.to_thread(
            _upload_document_wall_sync,
            self._access_token,
            file_path,
            owner_id,
            title,
        )
