"""Опрос core, сохранение снимков и оповещение ботов.

Фоновый poll работает без JWT и без SCHEDULER_LOGIN: расписания берутся из Core/БД
по профилям авторизованных пользователей (user_id), боты и curl вызываются напрямую
в Docker-сети.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from config import settings
from database import get_db_connection

logger = logging.getLogger(__name__)

BOT_PLATFORMS = [
    "tg",
    "wp",
    "vk",
    "tw",
    "url",
    "threads",
    "dzen",
    "instagram",
]

# Для /status: время последнего успешного цикла опроса
_last_poll_at: Optional[Any] = None


def get_last_poll_at():
    return _last_poll_at


def _payload_hash(schedules: list[dict[str, Any]]) -> str:
    raw = json.dumps(schedules, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _bot_service_url(platform: str) -> str | None:
    """Базовый URL бота платформы в Docker-сети."""
    mapping = {
        "tg": settings.TG_BOT_SERVICE_URL,
        "wp": settings.WP_BOT_SERVICE_URL,
        "vk": settings.VK_BOT_SERVICE_URL,
        "tw": settings.TW_BOT_SERVICE_URL,
        "url": settings.URL_BOT_SERVICE_URL,
        "threads": settings.THREADS_BOT_SERVICE_URL,
        "dzen": settings.DZEN_BOT_SERVICE_URL,
        "instagram": settings.INSTAGRAM_BOT_SERVICE_URL,
    }
    url = mapping.get(platform) or ""
    return url.rstrip("/") if url else None


async def _fetch_schedules() -> list[dict[str, Any]]:
    """Расписания всех пользователей из Core (агрегация профилей в БД)."""
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        raise RuntimeError("CORE_SERVICE_URL is not configured")
    url = f"{base}/schedules"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("schedules") or []


async def _fetch_profiles_parallel(token: str) -> dict[str, list[dict[str, Any]]]:
    """Параллельно получает профили через API Gateway (admin UI, JWT вызывающего).

    Args:
        token: JWT токен авторизации вызывающего администратора

    Returns:
        Словарь с данными профилей по платформам.
    """
    base = settings.API_GATEWAY_URL.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}

    async def fetch_platform_profiles(platform: str) -> tuple[str, list[dict[str, Any]]]:
        url = f"{base}/{platform}/profiles"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 401:
                    raise RuntimeError("Unauthorized")
                resp.raise_for_status()
                data = resp.json()
                return platform, data.get("profiles") or []
        except Exception as e:
            logger.warning("Failed to fetch %s profiles: %s", platform, e)
            return platform, []

    results = await asyncio.gather(
        fetch_platform_profiles("wp"),
        fetch_platform_profiles("tg"),
        fetch_platform_profiles("tw"),
        fetch_platform_profiles("vk"),
        fetch_platform_profiles("threads"),
        fetch_platform_profiles("dzen"),
        fetch_platform_profiles("instagram"),
        return_exceptions=True,
    )

    profiles_data: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error("Error fetching profiles: %s", result)
            continue
        platform, profiles = result
        profiles_data[platform] = profiles

    return profiles_data


def _transform_profiles_to_schedules(profiles_data: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Преобразует данные профилей в формат расписаний."""
    schedules = []

    for platform, profiles in profiles_data.items():
        for profile in profiles:
            time_intervals = profile.get("time_intervals", [])
            if isinstance(time_intervals, str):
                if time_intervals and ":" in time_intervals and len(time_intervals) <= 5:
                    time_intervals = [{"start": time_intervals, "end": time_intervals}]
                else:
                    try:
                        time_intervals = json.loads(time_intervals) if time_intervals else []
                    except json.JSONDecodeError:
                        time_intervals = []

            schedule = {
                "user_id": profile.get("user_id"),
                "platform": platform,
                "publish_enabled": bool(profile.get("publish_enabled", False)),
                "collect_enabled": bool(profile.get("collect_enabled", False)),
                "schedule_type": profile.get("schedule_type") or "immediate",
                "time_intervals": time_intervals if isinstance(time_intervals, list) else [],
            }
            schedules.append(schedule)

    return schedules


async def _load_previous_snapshot() -> list[dict[str, Any]]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT user_id, platform, publish_enabled, collect_enabled, schedule_type, time_intervals FROM schedule_snapshots"
            )
            rows = await cur.fetchall()
            cols = ["user_id", "platform", "publish_enabled", "collect_enabled", "schedule_type", "time_intervals"]
        out = []
        for row in rows:
            rec = dict(zip(cols, row))
            ti = rec.get("time_intervals")
            if isinstance(ti, str):
                try:
                    ti = json.loads(ti) if ti else []
                except json.JSONDecodeError:
                    ti = []
            rec["time_intervals"] = ti
            out.append(rec)
        return out


async def _store_snapshot(schedules: list[dict[str, Any]]) -> None:
    async with get_db_connection() as conn:
        cur = await conn.cursor()
        try:
            await cur.execute("BEGIN")
            await cur.execute("DELETE FROM schedule_snapshots")
            for s in schedules:
                ti = json.dumps(s.get("time_intervals") or [])
                await cur.execute(
                    """
                    INSERT INTO schedule_snapshots (
                        user_id, platform, publish_enabled, collect_enabled,
                        schedule_type, time_intervals, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """,
                    (
                        s["user_id"],
                        s["platform"],
                        s.get("publish_enabled", False),
                        s.get("collect_enabled", False),
                        s.get("schedule_type") or "immediate",
                        ti,
                    ),
                )
            wp_schedules = [s for s in schedules if s.get("platform") == "wp"]
            await cur.execute("DELETE FROM schedule_snapshots_wp")
            for s in wp_schedules:
                ti = json.dumps(s.get("time_intervals") or [])
                await cur.execute(
                    """
                    INSERT INTO schedule_snapshots_wp (
                        user_id, platform, publish_enabled, collect_enabled,
                        schedule_type, time_intervals, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """,
                    (
                        s["user_id"],
                        s["platform"],
                        s.get("publish_enabled", False),
                        s.get("collect_enabled", False),
                        s.get("schedule_type") or "immediate",
                        ti,
                    ),
                )
            await cur.execute("COMMIT")
        except Exception:
            await cur.execute("ROLLBACK")
            raise
        finally:
            cur.close()


async def _notify_bot(
    platform: str,
    schedules: list[dict[str, Any]],
    *,
    timeout_seconds: float = 60.0,
) -> dict[str, Any] | None:
    """Оповещает бота напрямую (без JWT). Контекст — user_id в schedules."""
    base = _bot_service_url(platform)
    if not base:
        logger.warning("No service URL for platform %s", platform)
        return None
    if not schedules and platform != "url":
        return None
    url = f"{base}/schedule"
    headers = {"Content-Type": "application/json"}
    payload = {"schedules": schedules}
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        logger.warning("Notify %s timeout: %s", platform, e)
        return None
    except httpx.HTTPError as e:
        logger.warning("Notify %s HTTP error: %s", platform, e)
        return None
    if resp.status_code >= 400:
        logger.warning("Notify %s failed: %s %s", platform, resp.status_code, resp.text)
        return None
    logger.info("Notified %s: %d schedules", platform, len(schedules))
    try:
        return resp.json()
    except Exception:
        return None


async def run_poll_cycle() -> bool:
    """Один цикл: запрос core, diff, сохранение, оповещение. Возвращает True если были изменения."""
    global _last_poll_at
    schedules = await _fetch_schedules()
    new_h = _payload_hash(schedules)
    try:
        prev = await _load_previous_snapshot()
        old_h = _payload_hash(prev)
    except Exception:
        old_h = None
    changed = old_h != new_h
    await _store_snapshot(schedules)

    by_platform: dict[str, list[dict[str, Any]]] = {p: [] for p in BOT_PLATFORMS}
    for s in schedules:
        p = s.get("platform")
        if p in by_platform:
            by_platform[p].append(s)

    # url первым и отдельно — сбор по schedule_time не ждёт остальных ботов
    if by_platform["url"]:
        try:
            data = await _notify_bot("url", by_platform["url"], timeout_seconds=120.0)
            if data:
                await _persist_url_posts(data)
                await _mark_curl_one_time_done(by_platform["url"], data)
        except Exception as e:
            logger.exception("Notify platform url failed: %s", e)

    notify_all = not settings.NOTIFY_ON_CHANGE_ONLY or changed
    if notify_all:
        other = [p for p in BOT_PLATFORMS if p != "url" and by_platform[p]]
        results = await asyncio.gather(
            *[
                _notify_bot(p, by_platform[p], timeout_seconds=15.0)
                for p in other
            ],
            return_exceptions=True,
        )
        for platform, result in zip(other, results):
            if isinstance(result, Exception):
                logger.warning("Notify platform %s failed: %s", platform, result)

    await _run_smm_jobs()
    await _sync_competitor_snapshots()
    await _recheck_stale_channel_auth()


async def _recheck_stale_channel_auth() -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    url = f"{base}/internal/smm/channels/auth/recheck-stale"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, params={"max_age_hours": 24})
        if resp.status_code >= 400:
            logger.warning("Channel auth recheck failed: %s %s", resp.status_code, resp.text)
        else:
            data = resp.json()
            if data.get("channels_updated"):
                logger.info("Channel auth rechecked: %s", data.get("channels_updated"))
    except Exception as e:
        logger.warning("Channel auth recheck error: %s", e)
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO service_cycle_log (
                        service_name, cycle_type, status, detail, items_processed
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        "scheduler",
                        "poll",
                        "ok",
                        f"schedules={len(schedules)} changed={changed}",
                        len(schedules),
                    ),
                )
    except Exception as e:
        logger.debug("service_cycle_log skip: %s", e)
    _last_poll_at = datetime.utcnow()
    return changed


async def _run_smm_jobs() -> None:
    """Drain due smm_publish_jobs via Core internal API."""
    if not getattr(settings, "SMM_JOBS_RUN_ENABLED", True):
        return
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    url = f"{base}/internal/smm/jobs/run"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, params={"limit": 50})
        if resp.status_code >= 400:
            logger.warning("SMM jobs run failed: %s %s", resp.status_code, resp.text)
        else:
            data = resp.json()
            logger.info("SMM jobs processed: %s", data.get("processed"))
    except Exception as e:
        logger.warning("SMM jobs run error: %s", e)


async def _sync_competitor_snapshots() -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    url = f"{base}/internal/smm/competitors/sync"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url)
        if resp.status_code >= 400:
            logger.warning("Competitor sync failed: %s %s", resp.status_code, resp.text)
        else:
            data = resp.json()
            if data.get("inserted"):
                logger.info("Competitor snapshots inserted: %s", data.get("inserted"))
    except Exception as e:
        logger.warning("Competitor sync error: %s", e)


async def _persist_url_posts(schedule_response: dict[str, Any]) -> None:
    """Сохраняет результаты url-bot в Core (url_posts) напрямую; user_id в каждом посте."""
    details = schedule_response.get("details") or []
    posts: list[dict[str, Any]] = []
    for d in details:
        if d.get("error"):
            continue
        if not d.get("has_text") and not d.get("has_screenshot"):
            continue
        post = {
            "user_id": d.get("user_id"),
            "url": d.get("url", ""),
            "post_text": (d.get("text") or "").strip(),
            "screenshot_path": d.get("screenshot_path"),
            "screenshot_base64": d.get("screenshot_base64"),
            "to_tg": d.get("to_tg", False),
            "to_wp": d.get("to_wp", False),
            "to_tw": d.get("to_tw", False),
            "to_vk": d.get("to_vk", False),
            "target_channels": list(d.get("target_channels") or []),
            "target_groups": list(d.get("target_groups") or []),
        }
        if post["user_id"] is not None:
            posts.append(post)
    if not posts:
        return
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    url = f"{base}/curl/url-posts"
    headers = {"Content-Type": "application/json"}
    payload = {"posts": posts}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.warning("Save url posts failed: %s %s", resp.status_code, resp.text)
        else:
            logger.info("Saved %d url posts to Core", len(posts))
    except Exception as e:
        logger.exception("Save url posts error: %s", e)


async def _mark_curl_one_time_done(
    url_schedules: list[dict[str, Any]], schedule_response: dict[str, Any]
) -> None:
    """Отмечает одноразовые URL как выполненные в Core (POST /curl/one-time-done)."""
    details = schedule_response.get("details") or []
    success_set = {
        (d.get("user_id"), (d.get("url") or "").strip(), (d.get("xpath") or "").strip())
        for d in details
        if not d.get("error")
    }
    run_once_triples = [
        (s.get("user_id"), (u.get("url") or "").strip(), (u.get("xpath") or "").strip())
        for s in url_schedules
        for u in (s.get("urls") or [])
        if u.get("run_once")
    ]
    items = [
        {"user_id": uid, "url": url, "xpath": xpath}
        for (uid, url, xpath) in run_once_triples
        if (uid, url, xpath) in success_set
    ]
    if not items:
        return
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    url = f"{base}/curl/one-time-done"
    headers = {"Content-Type": "application/json"}
    payload = {"items": items}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.warning("One-time-done failed: %s %s", resp.status_code, resp.text)
        else:
            logger.info("Marked %d one-time URL(s) done", len(items))
    except Exception as e:
        logger.exception("One-time-done request error: %s", e)


async def poll_loop() -> None:
    """Фоновый цикл без service-login: данные пользователей из Core/БД.

    Только один реплика держит pg advisory lock на цикл — безопасно replicas>1.
    """
    # Стабильный ключ для scheduler poll (не конфликтует с int4 user ids)
    lock_key = 87421003
    while True:
        held = False
        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT pg_try_advisory_lock(%s)", (lock_key,))
                    row = await cur.fetchone()
                    held = bool(row and row[0])
                    if not held:
                        logger.debug("Scheduler poll skipped — another replica holds advisory lock")
                    else:
                        try:
                            await run_poll_cycle()
                        finally:
                            await cur.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
                            held = False
        except Exception as e:
            logger.exception("Poll cycle error: %s", e)
            if held:
                try:
                    async with get_db_connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
                except Exception:
                    logger.exception("Failed to release scheduler advisory lock")

        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
