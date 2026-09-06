"""In-memory сессия Selenium для двухшаговой проверки (код пуша). Только один инстанс dzen-bot (без sticky K8S)."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, Optional

from config import settings

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

_lock = threading.RLock()
_store: Dict[int, "PendingSession"] = {}
# Последний JPEG data URL по user_id — отдаём в UI, даже если HTTP-ответ проверки уже отвалился по таймауту.
_last_diag_url: Dict[int, str] = {}
_live_stop: Dict[int, threading.Event] = {}
_live_threads: Dict[int, threading.Thread] = {}

LIVE_SCREENCAP_INTERVAL_SEC = 3.0


@dataclass
class PendingSession:
    driver: "WebDriver"
    created_at: float
    awaiting_push: bool = False
    in_progress: bool = True
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


def set_last_diag_url(user_id: int, url: Optional[str]) -> None:
    if not url:
        return
    with _lock:
        _last_diag_url[user_id] = url


def get_last_diag_url(user_id: int) -> Optional[str]:
    with _lock:
        return _last_diag_url.get(user_id)


def clear_last_diag_url(user_id: int) -> None:
    with _lock:
        _last_diag_url.pop(user_id, None)


def cleanup_stale_unlocked() -> None:
    now = time.time()
    t = _ttl()
    stale = [uid for uid, s in _store.items() if now - s.created_at > t]
    for uid in stale:
        _stop_live_unlocked(uid)
        s = _store.pop(uid, None)
        if s:
            _quit_driver_safe(s.driver)
            logger.info("Pending dzen session expired user_id=%s", uid)


def _stop_live_unlocked(user_id: int) -> None:
    ev = _live_stop.pop(user_id, None)
    if ev:
        ev.set()
    _live_threads.pop(user_id, None)


def stop_live_screencap(user_id: int) -> None:
    with _lock:
        _stop_live_unlocked(user_id)


def start_live_screencap(
    user_id: int,
    capture_fn: Callable[[int], None],
    *,
    interval_sec: float = LIVE_SCREENCAP_INTERVAL_SEC,
) -> None:
    """Фоновый захват экрана каждые interval_sec, пока сессия жива."""
    with _lock:
        _stop_live_unlocked(user_id)
        stop_ev = threading.Event()
        _live_stop[user_id] = stop_ev

        def _loop() -> None:
            # Первая пауза — дать Chrome стартовать
            if stop_ev.wait(1.0):
                return
            while not stop_ev.is_set():
                try:
                    with _lock:
                        alive = user_id in _store
                    if not alive:
                        break
                    capture_fn(user_id)
                except Exception as e:
                    logger.debug("live screencap user_id=%s: %s", user_id, e)
                if stop_ev.wait(max(1.0, float(interval_sec))):
                    break

        th = threading.Thread(
            target=_loop,
            name=f"dzen-live-diag-{user_id}",
            daemon=True,
        )
        _live_threads[user_id] = th
        th.start()
        logger.info("Live screencap started user_id=%s interval=%.1fs", user_id, interval_sec)


def put_session(
    user_id: int,
    driver: "WebDriver",
    *,
    awaiting_push: bool = False,
    in_progress: bool = True,
) -> None:
    with _lock:
        cleanup_stale_unlocked()
        old = _store.pop(user_id, None)
        op_lock = threading.RLock()
        created_at = time.time()
        if old:
            if old.driver is not driver:
                _quit_driver_safe(old.driver)
            else:
                op_lock = old.op_lock
                created_at = old.created_at
        _store[user_id] = PendingSession(
            driver=driver,
            created_at=created_at,
            awaiting_push=awaiting_push,
            in_progress=in_progress,
            op_lock=op_lock,
        )
        logger.info(
            "Pending dzen session stored user_id=%s awaiting_push=%s in_progress=%s",
            user_id,
            awaiting_push,
            in_progress,
        )


def update_session_flags(
    user_id: int,
    *,
    awaiting_push: Optional[bool] = None,
    in_progress: Optional[bool] = None,
) -> None:
    with _lock:
        s = _store.get(user_id)
        if not s:
            return
        if awaiting_push is not None:
            s.awaiting_push = awaiting_push
        if in_progress is not None:
            s.in_progress = in_progress


def get_session(user_id: int) -> Optional[PendingSession]:
    with _lock:
        cleanup_stale_unlocked()
        s = _store.get(user_id)
        if not s:
            return None
        if time.time() - s.created_at > _ttl():
            _stop_live_unlocked(user_id)
            _store.pop(user_id, None)
            _quit_driver_safe(s.driver)
            return None
        return s


def take_session_and_remove(user_id: int) -> Optional[PendingSession]:
    with _lock:
        cleanup_stale_unlocked()
        _stop_live_unlocked(user_id)
        s = _store.pop(user_id, None)
        if s and time.time() - s.created_at > _ttl():
            _quit_driver_safe(s.driver)
            return None
        return s


def pop_and_quit(user_id: int) -> None:
    with _lock:
        _stop_live_unlocked(user_id)
        s = _store.pop(user_id, None)
        if s:
            _quit_driver_safe(s.driver)
