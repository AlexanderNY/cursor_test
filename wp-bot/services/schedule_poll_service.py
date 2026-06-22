"""Фоновый опрос schedule_snapshot_wp и запуск публикации/сбора."""

import asyncio
import json
import logging
from typing import Any

from config import settings
from database import get_db_connection, release_db_connection
from services.publish_service import publish_service
from services.collect_service import collect_service

logger = logging.getLogger(__name__)


async def _load_wp_schedules() -> list[dict[str, Any]]:
    """Загружает расписания WordPress из schedule_snapshot_wp."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, platform, publish_enabled, collect_enabled, schedule_type, time_intervals
                FROM schedule_snapshots_wp
                WHERE platform = 'wp'
                """
            )
            rows = await cur.fetchall()
            cols = ["user_id", "platform", "publish_enabled", "collect_enabled", "schedule_type", "time_intervals"]
            result = []
            for row in rows:
                rec = dict(zip(cols, row))
                ti = rec.get("time_intervals")
                if isinstance(ti, str):
                    try:
                        ti = json.loads(ti) if ti else []
                    except json.JSONDecodeError:
                        ti = []
                rec["time_intervals"] = ti
                result.append(rec)
            return result
    finally:
        await release_db_connection(conn)


async def _run_poll_cycle() -> None:
    """Один цикл: загрузка расписаний, запуск публикации и сбора при необходимости."""
    schedules = await _load_wp_schedules()
    if not schedules:
        return

    # Публикация: publish_enabled AND schedule_type == 'on_new_messages'
    publish_user_ids = [
        s["user_id"]
        for s in schedules
        if s.get("publish_enabled") and s.get("schedule_type") == "on_new_messages"
    ]

    # Сбор: collect_enabled
    collect_user_ids = [
        s["user_id"]
        for s in schedules
        if s.get("collect_enabled")
    ]

    # Публикация
    if publish_user_ids:
        try:
            for user_id in publish_user_ids:
                result = await publish_service.publish_pending_posts(user_id=user_id)
                logger.info(
                    "Publish user_id=%s: %s published, %s failed",
                    user_id,
                    result.get("published", 0),
                    result.get("failed", 0),
                )
        except Exception as e:
            logger.exception("Error during publish: %s", e)

    # Сбор
    if collect_user_ids:
        try:
            for user_id in collect_user_ids:
                result = await collect_service.collect_posts(user_id=user_id)
                logger.info(
                    "Collect user_id=%s: %s collected, %s failed",
                    user_id,
                    result.get("collected", 0),
                    result.get("failed", 0),
                )
        except Exception as e:
            logger.exception("Error during collect: %s", e)


async def poll_loop() -> None:
    """Бесконечный цикл опроса schedule_snapshot_wp."""
    while True:
        try:
            await _run_poll_cycle()
        except Exception as e:
            logger.exception("Poll cycle error: %s", e)

        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
