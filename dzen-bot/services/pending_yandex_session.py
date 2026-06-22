"""In-memory сессия Selenium для двухшаговой проверки (код пуша). Только один инстанс dzen-bot (без sticky K8S)."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional

from config import settings

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

_lock = threading.RLock()
_store: Dict[int, "PendingSession"] = {}


@dataclass
class PendingSession:
    driver: "WebDriver"
    created_at: float
    op_lock: threading.RLock = field(default_factory=threading.RLock, repr=False)


def _ttl() -> int:
    return int(getattr(settings, "PENDING_DZEN_AUTH_TTL_SEC", 900) or 900)


def _quit_driver_safe(driver: Optional["WebDriver"]) -> None:
    if not driver:
        return
    try:
        driver.quit()
    except Exception as e:
        logger.debug("pending session quit: %s", e)


def cleanup_stale_unlocked() -> None:
    now = time.time()
    t = _ttl()
    stale = [uid for uid, s in _store.items() if now - s.created_at > t]
    for uid in stale:
        s = _store.pop(uid, None)
        if s:
            _quit_driver_safe(s.driver)
            logger.info("Pending dzen session expired user_id=%s", uid)


def put_session(user_id: int, driver: "WebDriver") -> None:
    with _lock:
        cleanup_stale_unlocked()
        old = _store.pop(user_id, None)
        if old:
            _quit_driver_safe(old.driver)
        _store[user_id] = PendingSession(driver=driver, created_at=time.time())
        logger.info("Pending dzen session stored user_id=%s", user_id)


def get_session(user_id: int) -> Optional[PendingSession]:
    with _lock:
        cleanup_stale_unlocked()
        s = _store.get(user_id)
        if not s:
            return None
        if time.time() - s.created_at > _ttl():
            _store.pop(user_id, None)
            _quit_driver_safe(s.driver)
            return None
        return s


def take_session_and_remove(user_id: int) -> Optional[PendingSession]:
    with _lock:
        cleanup_stale_unlocked()
        s = _store.pop(user_id, None)
        if s and time.time() - s.created_at > _ttl():
            _quit_driver_safe(s.driver)
            return None
        return s


def pop_and_quit(user_id: int) -> None:
    with _lock:
        s = _store.pop(user_id, None)
        if s:
            _quit_driver_safe(s.driver)
