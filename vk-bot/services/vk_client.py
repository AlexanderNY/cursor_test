"""Обёртка над vk_api для вызова в executor (синхронный API)."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import vk_api
from vk_api import VkUpload

from shared.circuit_breaker import get_breaker
from shared.retry import retry_async
from shared.post_adapt import NETWORK_TEXT_LIMITS

logger = logging.getLogger(__name__)

_VK_MESSAGE_LIMIT = NETWORK_TEXT_LIMITS["vk"]

try:
    from vk_api.exceptions import ApiError as VkApiError
except ImportError:  # pragma: no cover
    try:
        from vk_api.vk_api import ApiError as VkApiError  # type: ignore
    except ImportError:
        VkApiError = type("VkApiError", (Exception,), {})  # type: ignore

# Коды VK API: auth / access — не даун платформы
_VK_AUTH_OR_ACCESS_CODES = frozenset({5, 15, 17, 27, 28, 29, 113, 200, 201, 203})


def _vk_breaker():
    return get_breaker("vk_api")


def _is_platform_failure(exc: BaseException) -> bool:
    """True, если сбой похож на недоступность VK API (не битый токен профиля)."""
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    if isinstance(exc, VkApiError):
        code = getattr(exc, "code", None)
        if code in _VK_AUTH_OR_ACCESS_CODES:
            return False
        return True
    msg = str(exc).lower()
    if any(x in msg for x in ("connection", "timeout", "timed out", "network", "503", "502", "500")):
        return True
    return True


def _is_retryable_vk_error(exc: BaseException) -> bool:
    """Retry только для platform/transient; auth — без повтора."""
    if isinstance(exc, VkApiError):
        code = getattr(exc, "code", None)
        if code in _VK_AUTH_OR_ACCESS_CODES:
            return False
    return _is_platform_failure(exc)


def _wall_get_sync(access_token: str, owner_id: int, count: int = 20) -> Dict[str, Any]:
    """Синхронный вызов wall.get. owner_id для группы отрицательный (например -123456)."""
    vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
    vk = vk_session.get_api()
    return vk.wall.get(owner_id=owner_id, count=count, filter="owner")


def _wall_get_by_id_sync(access_token: str, owner_id: int, post_id: int) -> List[Dict[str, Any]]:
    vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
    vk = vk_session.get_api()
    posts = f"{owner_id}_{post_id}"
    return vk.wall.getById(posts=posts)


def _groups_get_by_id_sync(access_token: str, group_ids: List[str]) -> List[Dict[str, Any]]:
    vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
    vk = vk_session.get_api()
    result = vk.groups.getById(group_ids=",".join(group_ids), fields="members_count")
    if isinstance(result, dict):
        groups = result.get("groups")
        if isinstance(groups, list):
            return [g for g in groups if isinstance(g, dict)]
        if result.get("id") is not None:
            return [result]
        return []
    return result or []


def _wall_post_sync(
    access_token: str,
    owner_id: int,
    message: str,
    from_group: bool = True,
    attachments: Optional[str] = None,
) -> Dict[str, Any]:
    """Синхронный вызов wall.post. owner_id — ID владельца стены (положительный — пользователь, отрицательный — группа)."""
    vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
    vk = vk_session.get_api()
    # На стену сообщества всегда from_group=1 (пост от имени группы), иначе VK может отклонить community-токен.
    post_as_group = owner_id < 0 and from_group
    params = {
        "owner_id": owner_id,
        "message": message[:_VK_MESSAGE_LIMIT] if message else "",
        "from_group": 1 if post_as_group else 0,
    }
    if attachments:
        params["attachments"] = attachments
    return vk.wall.post(**params)


def _users_get_sync(access_token: str) -> Optional[int]:
    """Синхронный вызов users.get без параметров — возвращает id текущего пользователя по токену."""
    try:
        vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
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
        vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
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
        raise


def _upload_document_wall_sync(
    access_token: str, file_path: str, owner_id: int, title: Optional[str] = None
) -> Optional[str]:
    """Загружает документ на стену. owner_id > 0 — пользователь, < 0 — группа. Возвращает строку вложения doc{owner_id}_{id}."""
    try:
        vk_session = vk_api.VkApi(token=access_token, api_version="5.199")
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
        raise


class VkClient:
    """Клиент VK API. Вызовы выполняются в executor, чтобы не блокировать event loop."""

    def __init__(self, access_token: str):
        self._access_token = access_token

    async def get_current_user_id(self) -> Optional[int]:
        """Возвращает id текущего пользователя по токену (users.get)."""
        return await asyncio.to_thread(_users_get_sync, self._access_token)

    async def wall_get(self, owner_id: int, count: int = 20) -> List[Dict[str, Any]]:
        """Получает посты со стены. owner_id для группы — отрицательное число."""
        breaker = _vk_breaker()
        if not breaker.allow_request():
            logger.warning("wall.get skipped: VK circuit open")
            return []

        async def _call() -> Dict[str, Any]:
            return await asyncio.to_thread(
                _wall_get_sync, self._access_token, owner_id, count
            )

        try:
            result = await retry_async(
                _call,
                retry_on=_is_retryable_vk_error,
                operation_name=f"wall.get owner_id={owner_id}",
            )
            breaker.record_success()
            return result.get("items") or []
        except Exception as e:
            logger.error("wall.get owner_id=%s error: %s", owner_id, e, exc_info=True)
            if _is_platform_failure(e):
                breaker.record_failure()
            return []

    async def wall_get_by_id(self, owner_id: int, post_id: int) -> List[Dict[str, Any]]:
        breaker = _vk_breaker()
        if not breaker.allow_request():
            return []

        async def _call() -> List[Dict[str, Any]]:
            return await asyncio.to_thread(
                _wall_get_by_id_sync, self._access_token, owner_id, post_id
            )

        try:
            result = await retry_async(
                _call,
                retry_on=_is_retryable_vk_error,
                operation_name=f"wall.getById owner_id={owner_id} post_id={post_id}",
            )
            breaker.record_success()
            return result or []
        except Exception as e:
            logger.error("wall.getById owner_id=%s post_id=%s error: %s", owner_id, post_id, e)
            if _is_platform_failure(e):
                breaker.record_failure()
            return []

    async def groups_get_by_id(self, group_ids: List[str]) -> List[Dict[str, Any]]:
        if not group_ids:
            return []
        breaker = _vk_breaker()
        if not breaker.allow_request():
            return []

        async def _call() -> List[Dict[str, Any]]:
            return await asyncio.to_thread(
                _groups_get_by_id_sync, self._access_token, group_ids
            )

        try:
            result = await retry_async(
                _call,
                retry_on=_is_retryable_vk_error,
                operation_name=f"groups.getById ids={','.join(group_ids[:3])}",
            )
            breaker.record_success()
            return result or []
        except Exception as e:
            logger.error("groups.getById error: %s", e, exc_info=True)
            if _is_platform_failure(e):
                breaker.record_failure()
            return []

    async def wall_post(
        self,
        owner_id: int,
        message: str,
        from_group: bool = True,
        attachments: Optional[str] = None,
    ) -> Optional[int]:
        """Публикует пост на стену. owner_id: положительный — пользователь, отрицательный — группа. Возвращает post_id при успехе."""
        breaker = _vk_breaker()
        if not breaker.allow_request():
            logger.warning("wall.post skipped: VK circuit open")
            return None

        async def _call() -> Dict[str, Any]:
            return await asyncio.to_thread(
                _wall_post_sync,
                self._access_token,
                owner_id,
                message,
                from_group,
                attachments,
            )

        try:
            result = await retry_async(
                _call,
                retry_on=_is_retryable_vk_error,
                operation_name=f"wall.post owner_id={owner_id}",
            )
            breaker.record_success()
            return result.get("post_id")
        except Exception as e:
            logger.error("wall.post owner_id=%s error: %s", owner_id, e, exc_info=True)
            if _is_platform_failure(e):
                breaker.record_failure()
            return None

    async def upload_photo_wall(self, photo_path: str, owner_id: int) -> Optional[str]:
        """Загружает фото на стену. Возвращает строку вложения photo{owner_id}_{id}."""
        breaker = _vk_breaker()
        if not breaker.allow_request():
            logger.warning("upload_photo_wall skipped: VK circuit open")
            return None

        async def _call() -> Optional[str]:
            return await asyncio.to_thread(
                _upload_photo_wall_sync, self._access_token, photo_path, owner_id
            )

        try:
            result = await retry_async(
                _call,
                retry_on=_is_retryable_vk_error,
                operation_name=f"upload_photo_wall owner_id={owner_id}",
            )
            if result:
                breaker.record_success()
            return result
        except Exception as e:
            if _is_platform_failure(e):
                breaker.record_failure()
            return None

    async def upload_document_wall(
        self, file_path: str, owner_id: int, title: Optional[str] = None
    ) -> Optional[str]:
        """Загружает документ на стену. Возвращает строку вложения doc{owner_id}_{id}."""
        breaker = _vk_breaker()
        if not breaker.allow_request():
            logger.warning("upload_document_wall skipped: VK circuit open")
            return None

        async def _call() -> Optional[str]:
            return await asyncio.to_thread(
                _upload_document_wall_sync,
                self._access_token,
                file_path,
                owner_id,
                title,
            )

        try:
            result = await retry_async(
                _call,
                retry_on=_is_retryable_vk_error,
                operation_name=f"upload_document_wall owner_id={owner_id}",
            )
            if result:
                breaker.record_success()
            return result
        except Exception as e:
            if _is_platform_failure(e):
                breaker.record_failure()
            return None
