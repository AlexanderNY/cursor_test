"""Обёртка над instagrapi: сессия в БД, 2FA, сохранение settings."""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from config import settings

from .instagram_session import (
    clear_instagram_verification_code,
    persist_instagram_session,
    set_instagram_auth_error,
)

logger = logging.getLogger(__name__)


def _session_file_path(user_id: int) -> Optional[str]:
    base = (getattr(settings, "SESSION_SAVE_PATH", None) or "").strip()
    if not base:
        return None
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"instagram_{user_id}.json")


def _load_session_file(user_id: int) -> Optional[Dict[str, Any]]:
    path = _session_file_path(user_id)
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception as e:
        logger.warning("load session file %s: %s", path, e)
        return None


def _dump_session_file(user_id: int, session_dict: Dict[str, Any]) -> None:
    path = _session_file_path(user_id)
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, default=str)
    except Exception as e:
        logger.warning("dump session file %s: %s", path, e)


def _normalize_session(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _new_instagrapi_client() -> Any:
    """Создаёт instagrapi.Client с прокси и задержками из настроек."""
    from instagrapi import Client

    proxy_raw = (getattr(settings, "INSTAGRAM_HTTP_PROXY", None) or "").strip()
    proxy = proxy_raw or None
    dmin = int(getattr(settings, "INSTAGRAM_DELAY_RANGE_MIN", 1))
    dmax = int(getattr(settings, "INSTAGRAM_DELAY_RANGE_MAX", 4))
    if dmin > dmax:
        dmin, dmax = dmax, dmin
    delay_range = [dmin, dmax]
    return Client(proxy=proxy, delay_range=delay_range)


def _client_from_settings_dict(settings_dict: Dict[str, Any]) -> Any:
    """Восстанавливает Client из сохранённого get_settings() (в т.ч. после Selenium)."""
    cl = _new_instagrapi_client()
    cl.set_settings(settings_dict)
    return cl


def _is_retryable_instagram_network_error(exc: BaseException) -> bool:
    """Ошибки сети/TLS, при которых имеет смысл повторить попытку входа."""
    text = f"{type(exc).__name__}: {exc}".lower()
    needles = (
        "ssl",
        "sslerror",
        "connection",
        "eof",
        "timeout",
        "reset",
        "broken pipe",
        "temporarily",
        "unavailable",
        "network",
        "max retries",
        "bad handshake",
    )
    return any(n in text for n in needles)


def _login_sync(
    username: str,
    password: str,
    session_dict: Optional[Dict[str, Any]],
    verification_code: Optional[str],
) -> Any:
    """Синхронный логин. Возвращает Client или бросает исключение."""
    retries = max(1, int(getattr(settings, "INSTAGRAM_LOGIN_RETRIES", 3)))
    retry_pause = float(getattr(settings, "INSTAGRAM_LOGIN_RETRY_DELAY_SEC", 4.0))

    for attempt in range(retries):
        try:
            cl = _new_instagrapi_client()
            if session_dict:
                try:
                    cl.set_settings(session_dict)
                except Exception as e:
                    logger.warning("set_settings failed, full login: %s", e)
            if verification_code:
                cl.login(username, password, verification_code=verification_code)
            else:
                cl.login(username, password)
            return cl
        except Exception as e:
            is_last = attempt >= retries - 1
            if is_last or not _is_retryable_instagram_network_error(e):
                raise
            wait = retry_pause * (attempt + 1)
            logger.warning(
                "Instagram login attempt %s/%s failed (%s: %s), retry in %.1fs",
                attempt + 1,
                retries,
                type(e).__name__,
                e,
                wait,
            )
            time.sleep(wait)


def _user_id_from_username_sync(cl: Any, username: str) -> Optional[int]:
    try:
        return cl.user_id_from_username(username.strip())
    except Exception as e:
        logger.debug("user_id_from_username %s: %s", username, e)
        return None


def _user_medias_sync(cl: Any, user_id: int, amount: int = 20) -> List[Dict[str, Any]]:
    try:
        medias = cl.user_medias(user_id, amount)
        result = []
        for m in medias:
            cap = getattr(m, "caption", None)
            caption = (cap.get("text", "") if isinstance(cap, dict) else cap) or ""
            images = []
            if getattr(m, "resources", None):
                for r in m.resources:
                    url = getattr(r, "thumbnail_url", None) or getattr(r, "video_url", None)
                    if url:
                        images.append(url)
            if not images and getattr(m, "thumbnail_url", None):
                images.append(m.thumbnail_url)
            if not images and getattr(m, "image_versions2", None):
                cands = m.image_versions2.get("candidates", []) if isinstance(m.image_versions2, dict) else []
                if cands and isinstance(cands[0], dict) and cands[0].get("url"):
                    images.append(cands[0]["url"])
            result.append({
                "pk": str(getattr(m, "pk", None) or getattr(m, "id", None) or ""),
                "caption": caption[:2200] if caption else "",
                "taken_at": getattr(m, "taken_at", None),
                "like_count": getattr(m, "like_count", 0) or 0,
                "comment_count": getattr(m, "comment_count", 0) or 0,
                "images": images,
            })
        return result
    except Exception as e:
        logger.warning("user_medias %s: %s", user_id, e)
        return []


def _photo_upload_sync(cl: Any, path: str, caption: str = "") -> Optional[str]:
    try:
        return cl.photo_upload(path, caption=caption or "")
    except Exception as e:
        logger.warning("photo_upload %s: %s", path[:80], e)
        return None


def _album_upload_sync(cl: Any, paths: List[str], caption: str = "") -> Optional[str]:
    try:
        return cl.album_upload(paths, caption=caption or "")
    except Exception as e:
        logger.warning("album_upload: %s", e)
        return None


def _get_settings_sync(cl: Any) -> Dict[str, Any]:
    try:
        return cl.get_settings()
    except Exception as e:
        logger.warning("get_settings: %s", e)
        return {}


def _user_following_sync(cl: Any, user_id: int, amount: int) -> List[Dict[str, Any]]:
    """Аккаунты, на которые подписан user_id (подписки / following)."""
    if amount <= 0:
        return []
    try:
        raw = cl.user_following(str(user_id), use_cache=False, amount=amount)
    except Exception as e:
        logger.warning("user_following %s: %s", user_id, e)
        return []
    result: List[Dict[str, Any]] = []
    if isinstance(raw, dict):
        for uid, u in raw.items():
            pk_val = getattr(u, "pk", None)
            if pk_val is None:
                try:
                    pk_val = int(uid)
                except (TypeError, ValueError):
                    pk_val = 0
            result.append({
                "pk": int(pk_val) if pk_val is not None else 0,
                "username": (getattr(u, "username", None) or "").strip(),
                "full_name": (getattr(u, "full_name", None) or "").strip(),
            })
    elif isinstance(raw, list):
        for u in raw:
            pk_val = getattr(u, "pk", None) or getattr(u, "id", None)
            result.append({
                "pk": int(pk_val) if pk_val is not None else 0,
                "username": (getattr(u, "username", None) or "").strip(),
                "full_name": (getattr(u, "full_name", None) or "").strip(),
            })
    result.sort(key=lambda x: (x.get("username") or "").lower())
    return result


class InstagramClient:
    """Асинхронная обёртка над instagrapi Client с сохранением сессии."""

    def __init__(
        self,
        username: str,
        password: str,
        *,
        user_id: Optional[int] = None,
        session_dict: Optional[Dict[str, Any]] = None,
        verification_code: Optional[str] = None,
    ):
        self._username = (username or "").strip()
        self._password = password or ""
        self._user_id = user_id
        self._session_dict = _normalize_session(session_dict)
        self._verification_code = (verification_code or "").strip() or None
        if not self._verification_code and getattr(settings, "INSTAGRAM_VERIFICATION_CODE", None):
            self._verification_code = (settings.INSTAGRAM_VERIFICATION_CODE or "").strip() or None
        self._client: Any = None

    async def load_from_saved_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """Использовать готовую сессию instagrapi (например после Selenium) без password login."""
        try:
            self._client = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _client_from_settings_dict(settings_dict),
            )
            return self._client is not None
        except Exception as e:
            logger.error("load_from_saved_settings: %s", e, exc_info=True)
            await self._auth_error(str(e))
            return False

    async def login(self) -> bool:
        """Логин с учётом сессии из БД/файла. Сохраняет сессию при успехе."""
        if not self._username or not self._password:
            await self._auth_error("missing_username_or_password")
            return False

        session = self._session_dict
        if session is None and self._user_id is not None:
            session = _load_session_file(self._user_id)

        try:
            self._client = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _login_sync(
                    self._username,
                    self._password,
                    session,
                    self._verification_code,
                ),
            )
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            logger.error("Instagram login failed for %s: %s", self._username, err, exc_info=True)
            await self._auth_error(err)
            return False

        settings_dict = await asyncio.get_event_loop().run_in_executor(
            None,
            _get_settings_sync,
            self._client,
        )
        if settings_dict and self._user_id is not None:
            await persist_instagram_session(self._user_id, settings_dict)
            _dump_session_file(self._user_id, settings_dict)
            await clear_instagram_verification_code(self._user_id)
        elif settings_dict:
            if self._user_id is not None:
                _dump_session_file(self._user_id, settings_dict)

        await self._auth_error(None)
        return self._client is not None

    async def _auth_error(self, message: Optional[str]) -> None:
        if self._user_id is None:
            return
        await set_instagram_auth_error(self._user_id, message)

    async def user_id_from_username(self, username: str) -> Optional[int]:
        if not self._client:
            if not await self.login():
                return None
        return await asyncio.get_event_loop().run_in_executor(
            None,
            _user_id_from_username_sync,
            self._client,
            username,
        )

    async def user_medias(self, user_id: int, amount: int = 20) -> List[Dict[str, Any]]:
        if not self._client:
            if not await self.login():
                return []
        return await asyncio.get_event_loop().run_in_executor(
            None,
            _user_medias_sync,
            self._client,
            user_id,
            amount,
        )

    async def get_self_user_id(self) -> Optional[int]:
        if not self._client:
            if not await self.login():
                return None
        return getattr(self._client, "user_id", None)

    async def get_self_following(self, amount: int = 50) -> List[Dict[str, Any]]:
        """Список подписок (following) для текущего аккаунта, до amount записей."""
        if not self._client:
            if not await self.login():
                return []
        uid = getattr(self._client, "user_id", None)
        if uid is None:
            return []
        return await asyncio.get_event_loop().run_in_executor(
            None,
            _user_following_sync,
            self._client,
            int(uid),
            amount,
        )

    async def photo_upload(self, path: str, caption: str = "") -> Optional[str]:
        if not self._client:
            if not await self.login():
                return None
        code = await asyncio.get_event_loop().run_in_executor(
            None,
            _photo_upload_sync,
            self._client,
            path,
            caption,
        )
        await self._persist_after_action()
        return code

    async def album_upload(self, paths: List[str], caption: str = "") -> Optional[str]:
        if not self._client:
            if not await self.login():
                return None
        code = await asyncio.get_event_loop().run_in_executor(
            None,
            _album_upload_sync,
            self._client,
            paths,
            caption,
        )
        await self._persist_after_action()
        return code

    async def _persist_after_action(self) -> None:
        if self._client is None or self._user_id is None:
            return
        settings_dict = await asyncio.get_event_loop().run_in_executor(
            None,
            _get_settings_sync,
            self._client,
        )
        if settings_dict:
            await persist_instagram_session(self._user_id, settings_dict)
            _dump_session_file(self._user_id, settings_dict)
