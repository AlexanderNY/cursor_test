"""Перенос веб-cookies Instagram в instagrapi Client и сохранение сессии в БД."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from services.instagram_client import _new_instagrapi_client

logger = logging.getLogger(__name__)


def build_instagrapi_settings_from_browser_cookies(cookie_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Собирает минимальный settings для Client.init() из cookies веб-сессии.

    Нужны как минимум sessionid и ds_user_id (как в браузере после входа).
    """
    sessionid = (cookie_dict.get("sessionid") or "").strip()
    ds_raw = cookie_dict.get("ds_user_id") or cookie_dict.get("ds_userid") or ""
    ds_user_id = str(ds_raw).strip()
    if not sessionid or len(sessionid) < 20:
        raise ValueError("missing_or_invalid_sessionid")
    if not ds_user_id:
        raise ValueError("missing_ds_user_id")

    authorization_data = {
        "ds_user_id": ds_user_id,
        "sessionid": sessionid,
        "should_use_header_over_cookies": True,
    }
    cookies_for_settings = {k: v for k, v in cookie_dict.items() if v is not None}
    return {
        "cookies": cookies_for_settings,
        "authorization_data": authorization_data,
    }


def client_from_browser_cookies(cookie_dict: Dict[str, str]) -> Any:
    """Создаёт авторизованный instagrapi Client из cookies Selenium."""
    merged = build_instagrapi_settings_from_browser_cookies(cookie_dict)
    cl = _new_instagrapi_client()
    cl.set_settings(merged)
    return cl


def verify_client_and_get_settings(cl: Any) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Проверяет сессию запросом к API и возвращает get_settings() для сохранения в БД.
    """
    try:
        uid = cl.user_id
        if uid is None:
            return False, None, "user_id_missing_after_init"
        cl.user_info_v1(int(uid))
        return True, cl.get_settings(), None
    except Exception as e:
        logger.warning("verify_client_and_get_settings: %s", e, exc_info=True)
        return False, None, f"{type(e).__name__}: {e}"
