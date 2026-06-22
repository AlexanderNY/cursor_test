"""Сервис агрегации расписаний из профилей платформ."""

import json
from typing import Any

from database import get_db_connection, release_db_connection


class SchedulesService:
    """Агрегирует schedule-relevant поля из tg/tw/wp/vk_profiles."""

    PLATFORMS_SINGLE = [
        ("tg_profiles", "tg"),
        ("tw_profiles", "tw"),
        ("vk_profiles", "vk"),
        ("threads_profiles", "threads"),
        ("dzen_profiles", "dzen"),
        ("instagram_profiles", "instagram"),
    ]

    async def get_all_schedules(self) -> list[dict[str, Any]]:
        """Собирает расписания из всех таблиц профилей.

        Returns:
            Список записей {user_id, platform, publish_enabled, collect_enabled,
            schedule_type, time_intervals}.
        """
        result: list[dict[str, Any]] = []
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                for table, platform in self.PLATFORMS_SINGLE:
                    await cur.execute(
                        f"""
                        SELECT user_id, publish_enabled, collect_enabled,
                               schedule_type, time_intervals
                        FROM {table}
                        """
                    )
                    rows = await cur.fetchall()
                    desc = cur.description
                    cols = [c.name for c in desc] if desc else []
                    for row in rows:
                        rec = dict(zip(cols, row))
                        ti = rec.get("time_intervals")
                        if isinstance(ti, str):
                            try:
                                ti = json.loads(ti) if ti else []
                            except json.JSONDecodeError:
                                ti = []
                        result.append({
                            "user_id": rec["user_id"],
                            "platform": platform,
                            "publish_enabled": bool(rec.get("publish_enabled", False)),
                            "collect_enabled": bool(rec.get("collect_enabled", False)),
                            "schedule_type": rec.get("schedule_type") or "immediate",
                            "time_intervals": ti if isinstance(ti, list) else [],
                        })
                # wp: объединяем wp_publish_profile и wp_collect_profile по user_id
                await cur.execute(
                    """
                    SELECT p.user_id, p.publish_enabled, p.schedule_type, p.time_intervals,
                           COALESCE(c.collect_enabled, FALSE) AS collect_enabled
                    FROM wp_publish_profile p
                    LEFT JOIN wp_collect_profile c ON p.user_id = c.user_id
                    """
                )
                wp_rows = await cur.fetchall()
                wp_cols = [c.name for c in cur.description] if cur.description else []
                for row in wp_rows:
                    rec = dict(zip(wp_cols, row))
                    ti = rec.get("time_intervals")
                    if isinstance(ti, str) and ti and len(ti) <= 5 and ":" in ti:
                        ti_list = [{"start": ti, "end": ti}]
                    elif isinstance(ti, str):
                        try:
                            ti_list = json.loads(ti) if ti else []
                            if not isinstance(ti_list, list):
                                ti_list = []
                        except json.JSONDecodeError:
                            ti_list = []
                    else:
                        ti_list = ti if isinstance(ti, list) else []
                    result.append({
                        "user_id": rec["user_id"],
                        "platform": "wp",
                        "publish_enabled": bool(rec.get("publish_enabled", False)),
                        "collect_enabled": bool(rec.get("collect_enabled", False)),
                        "schedule_type": rec.get("schedule_type") or "immediate",
                        "time_intervals": ti_list,
                    })
                # пользователи только из wp_collect_profile без wp_publish_profile
                await cur.execute(
                    """
                    SELECT c.user_id, FALSE AS publish_enabled, c.collect_enabled,
                           'immediate' AS schedule_type, '[]'::jsonb AS time_intervals
                    FROM wp_collect_profile c
                    WHERE NOT EXISTS (SELECT 1 FROM wp_publish_profile p WHERE p.user_id = c.user_id)
                    """
                )
                wp_coll_only = await cur.fetchall()
                wp_coll_cols = [c.name for c in cur.description] if cur.description else []
                for row in wp_coll_only:
                    rec = dict(zip(wp_coll_cols, row))
                    result.append({
                        "user_id": rec["user_id"],
                        "platform": "wp",
                        "publish_enabled": False,
                        "collect_enabled": bool(rec.get("collect_enabled", False)),
                        "schedule_type": "immediate",
                        "time_intervals": [],
                    })
                # url: из curl_settings (collect_enabled + urls); run_once уже выполненные исключаем
                await cur.execute(
                    """
                    SELECT user_id, collect_enabled, urls
                    FROM curl_settings
                    """
                )
                curl_rows = await cur.fetchall()
                curl_cols = [c.name for c in cur.description] if cur.description else []
                for row in curl_rows:
                    rec = dict(zip(curl_cols, row))
                    user_id = rec["user_id"]
                    urls_raw = rec.get("urls")
                    if isinstance(urls_raw, str):
                        try:
                            urls_list = json.loads(urls_raw) if urls_raw else []
                        except json.JSONDecodeError:
                            urls_list = []
                    else:
                        urls_list = urls_raw if isinstance(urls_raw, list) else []
                    if not rec.get("collect_enabled") or not urls_list:
                        continue
                    # Исключаем run_once URL, уже выполненные
                    await cur.execute(
                        "SELECT url, xpath FROM curl_one_time_done WHERE user_id = %s",
                        (user_id,),
                    )
                    done_rows = await cur.fetchall()
                    done_set = {(r[0] or "", r[1] or "") for r in done_rows}
                    filtered_urls = []
                    for u in urls_list:
                        if (u or {}).get("run_once"):
                            url_val = (u or {}).get("url") or ""
                            xpath_val = (u or {}).get("xpath") or ""
                            if (url_val, xpath_val) in done_set:
                                continue
                        filtered_urls.append(u)
                    if not filtered_urls:
                        continue
                    time_intervals = []
                    for u in filtered_urls:
                        st = (u or {}).get("schedule_time")
                        if isinstance(st, str) and st and ":" in st:
                            time_intervals.append({"start": st, "end": st})
                    result.append({
                        "user_id": user_id,
                        "platform": "url",
                        "publish_enabled": False,
                        "collect_enabled": bool(rec.get("collect_enabled", False)),
                        "schedule_type": "immediate",
                        "time_intervals": time_intervals if time_intervals else [],
                        "urls": filtered_urls,
                    })
        finally:
            await release_db_connection(conn)
        return result


schedules_service = SchedulesService()
