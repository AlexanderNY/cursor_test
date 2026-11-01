"""Cookies сессии X из браузера пользователя: auth_token и ct0."""

import json
import re
from typing import Any, Dict, List, Optional

_TOKEN_RE = re.compile(r"^[A-Za-z0-9]{16,400}$")


def clean_cookie_value(raw: Optional[str], name: str) -> str:
    """Убирает кавычки, пробелы и префикс «name=» после копирования из DevTools."""
    value = (raw or "").strip().strip(";").strip().strip('"').strip("'")
    prefix = f"{name}="
    if value.lower().startswith(prefix):
        value = value[len(prefix):].strip()
    return value


def build_x_session_cookies(auth_token: Optional[str], ct0: Optional[str]) -> Optional[str]:
    """JSON cookies для tw-bot. None — auth_token не передан; ValueError — значение битое."""
    token = clean_cookie_value(auth_token, "auth_token")
    if not token:
        return None
    if not _TOKEN_RE.match(token):
        raise ValueError("auth_token: ожидается строка из латинских букв и цифр")
    csrf = clean_cookie_value(ct0, "ct0")
    if csrf and not _TOKEN_RE.match(csrf):
        raise ValueError("ct0: ожидается строка из латинских букв и цифр")

    cookies: List[Dict[str, Any]] = [
        {
            "name": "auth_token",
            "value": token,
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
        }
    ]
    if csrf:
        cookies.append(
            {
                "name": "ct0",
                "value": csrf,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
                "httpOnly": False,
            }
        )
    return json.dumps(cookies, separators=(",", ":"))
