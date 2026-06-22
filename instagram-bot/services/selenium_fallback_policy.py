"""Политика: когда после неудачи instagrapi запускать Selenium fallback."""

from typing import Optional

from config import settings


_NETWORK_ERROR_MARKERS = (
    "ssl",
    "sslerror",
    "eof",
    "connection",
    "timeout",
    "network",
    "reset",
    "broken pipe",
    "max retries",
    "unavailable",
    "temporarily",
    "bad handshake",
    "name or service not known",
    "failed to establish",
)


def should_attempt_selenium_fallback(last_error_message: Optional[str]) -> bool:
    """
    Возвращает True, если разрешено и нужно пробовать вход через Selenium.

    При INSTAGRAM_SELENIUM_FALLBACK_NETWORK_ERRORS_ONLY=True учитываются только
    сообщения, похожие на сетевые/TLS сбои.
    """
    if not getattr(settings, "INSTAGRAM_SELENIUM_FALLBACK_ENABLED", False):
        return False
    network_only = getattr(settings, "INSTAGRAM_SELENIUM_FALLBACK_NETWORK_ERRORS_ONLY", True)
    if not last_error_message or not str(last_error_message).strip():
        return not network_only
    msg = str(last_error_message).lower()
    if network_only:
        return any(m in msg for m in _NETWORK_ERROR_MARKERS)
    return True
