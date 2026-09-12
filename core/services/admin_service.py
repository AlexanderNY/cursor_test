"""Сервис для админ-эндпоинтов: статус сервисов и обзор таблиц постов."""

import json
import os
import socket
import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from config import settings
from database import get_db_connection, release_db_connection
from services.healthcheck_service import healthcheck_service


class AdminService:
    """Агрегирует данные от collector, processor, scheduler и healthcheck."""

    async def get_services_status(self) -> Dict[str, Any]:
        """Собирает healthcheck всех сервисов и детальный статус collector, processor, scheduler."""
        healthchecks = await healthcheck_service.check_all_services()

        collector_status: Optional[Dict[str, Any]] = None
        processor_status: Optional[Dict[str, Any]] = None
        scheduler_status: Optional[Dict[str, Any]] = None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.COLLECTOR_SERVICE_URL}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    collector_status = {
                        "service": data.get("service", "collector"),
                        "version": data.get("version", "1.0.0"),
                        "collect_interval_sec": data.get("collect_interval_sec"),
                        "distribute_interval_sec": data.get("distribute_interval_sec"),
                        "collect_batch_size": data.get("collect_batch_size"),
                        "distribute_batch_size": data.get("distribute_batch_size"),
                        "collector": _parse_loop_status(data.get("collector")),
                        "distributor": _parse_loop_status(data.get("distributor")),
                        "current_time": data.get("current_time"),
                        "started_at": data.get("started_at"),
                        "collect_functions": data.get("collect_functions") or [],
                        "error": None,
                    }
                else:
                    collector_status = {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            collector_status = {"error": str(e)}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.PROCESSOR_SERVICE_URL}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    processor_status = {
                        "service": data.get("service", "processor"),
                        "version": data.get("version", "1.0.0"),
                        "process_interval_sec": data.get("process_interval_sec"),
                        "process_batch_size": data.get("process_batch_size"),
                        "processor": _parse_loop_status(data.get("processor")),
                        "current_time": data.get("current_time"),
                        "started_at": data.get("started_at"),
                        "processing_options": data.get("processing_options") or [],
                        "error": None,
                    }
                else:
                    processor_status = {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            processor_status = {"error": str(e)}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.SCHEDULER_SERVICE_URL}/status")
                if resp.status_code == 200:
                    data = resp.json()
                    scheduler_status = {
                        "service": data.get("service", "scheduler"),
                        "version": data.get("version", "1.0.0"),
                        "poll_interval_sec": data.get("poll_interval_sec"),
                        "notify_on_change_only": data.get("notify_on_change_only"),
                        "last_poll_at": data.get("last_poll_at"),
                        "current_time": data.get("current_time"),
                        "started_at": data.get("started_at"),
                        "schedule_functions": data.get("schedule_functions") or [],
                        "error": None,
                    }
                else:
                    scheduler_status = {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            scheduler_status = {"error": str(e)}

        return {
            "healthchecks": [
                {"service_name": h["service_name"], "status": h["status"], "error": h.get("error"), "server_time": h.get("server_time")}
                for h in healthchecks
            ],
            "collector": collector_status,
            "processor": processor_status,
            "scheduler": scheduler_status,
        }

    async def get_posts_tables_overview(self) -> Dict[str, Any]:
        """Собирает метрики таблиц постов из collector и processor."""
        platforms: List[Dict[str, Any]] = []
        posts_table_collector: Optional[Dict[str, int]] = None
        posts_table_processor: Optional[Dict[str, int]] = None
        collector_error: Optional[str] = None
        processor_error: Optional[str] = None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.COLLECTOR_SERVICE_URL}/metrics")
                if resp.status_code == 200:
                    data = resp.json()
                    for p in data.get("platforms") or []:
                        platforms.append({
                            "platform": p.get("platform", ""),
                            "table": p.get("table", ""),
                            "collected_count": p.get("collected_count", 0),
                            "created_count": p.get("created_count", 0),
                            "ready_count": p.get("ready_count", 0),
                            "processing_count": p.get("processing_count", 0),
                            "status_counts": p.get("status_counts") or {},
                        })
                    pt = data.get("posts_table")
                    if isinstance(pt, dict):
                        posts_table_collector = {k: int(v) for k, v in pt.items() if isinstance(v, (int, float))}
                else:
                    collector_error = f"HTTP {resp.status_code}"
        except Exception as e:
            collector_error = str(e)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.PROCESSOR_SERVICE_URL}/metrics")
                if resp.status_code == 200:
                    data = resp.json()
                    pt = data.get("posts_table")
                    if isinstance(pt, dict):
                        posts_table_processor = {k: int(v) for k, v in pt.items() if isinstance(v, (int, float))}
                else:
                    processor_error = f"HTTP {resp.status_code}"
        except Exception as e:
            processor_error = str(e)

        return {
            "platforms": platforms,
            "posts_table_collector": posts_table_collector,
            "posts_table_processor": posts_table_processor,
            "collector_error": collector_error,
            "processor_error": processor_error,
        }

    async def run_processor_cycle(self) -> Dict[str, Any]:
        """Запускает один цикл обработки на processor. Проксирует POST /process/run."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{settings.PROCESSOR_SERVICE_URL}/process/run")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": data.get("status", "success"),
                        "message": data.get("message", ""),
                        "count": int(data.get("count", 0)),
                    }
                return {
                    "status": "error",
                    "message": f"Processor returned HTTP {resp.status_code}",
                    "count": 0,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "count": 0,
            }

    async def run_collect_cycle(self) -> Dict[str, Any]:
        """Будит processor: входящие посты уже в posts (ETL collect убран)."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{settings.COLLECTOR_SERVICE_URL}/collect/run")
                if resp.status_code == 200:
                    data = resp.json()
                    result = {
                        "status": data.get("status", "success"),
                        "message": data.get("message", ""),
                        "count": int(data.get("count", 0)),
                    }
                    if data.get("errors"):
                        result["errors"] = data["errors"]
                    return result
                return {
                    "status": "error",
                    "message": f"Collector returned HTTP {resp.status_code}",
                    "count": 0,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "count": 0,
            }

    async def run_distribute_cycle(self) -> Dict[str, Any]:
        """No-op proxy: distribute ETL убран, публикация из post_targets."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{settings.COLLECTOR_SERVICE_URL}/distribute/run")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": data.get("status", "success"),
                        "message": data.get("message", ""),
                        "count": int(data.get("count", 0)),
                    }
                return {
                    "status": "error",
                    "message": f"Collector returned HTTP {resp.status_code}",
                    "count": 0,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "count": 0,
            }

    async def run_posting_diagnostics(self) -> Dict[str, Any]:
        """Запускает цикл диагностики постинга: сводки post_targets (tg) и posts."""
        result: Dict[str, Any] = {
            "tg_targets_by_status": [],
            "tg_posts_by_status": [],
            "posts_by_status": [],
            "ready_for_telegram": 0,
            "profiles_with_channel": 0,
            "hints": [],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT status, COUNT(*) AS cnt
                        FROM post_targets
                        WHERE platform = 'tg'
                        GROUP BY status
                        ORDER BY status
                        """
                    )
                    rows = await cur.fetchall()
                    result["tg_targets_by_status"] = [
                        {"status": r[0], "count": r[1]} for r in rows
                    ]
                    result["tg_posts_by_status"] = result["tg_targets_by_status"]

                    await cur.execute(
                        """
                        SELECT status, source_platform, COUNT(*) AS cnt
                        FROM posts
                        GROUP BY status, source_platform
                        ORDER BY status, source_platform
                        """
                    )
                    rows = await cur.fetchall()
                    result["posts_by_status"] = [
                        {
                            "status": r[0],
                            "source_platform": r[1],
                            "count": r[2],
                        }
                        for r in rows
                    ]

                    await cur.execute(
                        """
                        SELECT COUNT(*) FROM post_targets t
                        JOIN tg_profiles pr ON t.user_id = pr.user_id
                        WHERE t.platform = 'tg' AND t.status = 'ready'
                          AND pr.channel_to_post IS NOT NULL
                          AND pr.channel_to_post != ''
                        """
                    )
                    (result["ready_for_telegram"],) = (await cur.fetchone()) or (0,)

                    await cur.execute(
                        """
                        SELECT COUNT(*) FROM tg_profiles
                        WHERE channel_to_post IS NOT NULL AND channel_to_post != ''
                        """
                    )
                    (result["profiles_with_channel"],) = (await cur.fetchone()) or (0,)

            finally:
                await release_db_connection(conn)

            # Подсказки на основе данных
            hints: List[str] = []
            tg_by_status = {r["status"]: r["count"] for r in result["tg_targets_by_status"]}
            posts_list = result["posts_by_status"]

            collected_tg = tg_by_status.get("collected", 0)
            if collected_tg > 0:
                hints.append(
                    f"В post_targets (tg) {collected_tg} постов со статусом collected. "
                    "Для очереди публикации ожидаются pending/ready; collected относится к таблице posts."
                )
            processing_tg = tg_by_status.get("processing", 0)
            ready_tg = tg_by_status.get("ready", 0)
            if processing_tg > 0 and ready_tg == 0:
                hints.append(
                    f"В post_targets (tg) {processing_tg} publishing и 0 ready. "
                    "Проверьте бота публикации и lease publishing."
                )
            posts_collected = sum(
                r["count"] for r in posts_list if r.get("status") == "collected"
            )
            if posts_collected > 0:
                hints.append(
                    f"В posts {posts_collected} постов в статусе collected. "
                    "Запустите цикл обработки (Processor) или проверьте, что Processor запущен."
                )
            posts_ready = sum(
                r["count"] for r in posts_list if r.get("status") == "ready"
            )
            if posts_ready > 0 and result["ready_for_telegram"] == 0:
                hints.append(
                    f"В posts {posts_ready} постов в статусе ready, но нет ready-целей Telegram в post_targets. "
                    "Проверьте, что processor создал post_targets со статусом ready."
                )
            if result["ready_for_telegram"] > 0 and result["profiles_with_channel"] == 0:
                hints.append(
                    "Есть ready-цели Telegram, но ни у одного профиля не задан channel_to_post. "
                    "Задайте канал для публикации в tg_profiles."
                )
            if not hints:
                hints.append("Явных проблем по сводкам не обнаружено. Проверьте логи сервисов при необходимости.")
            result["hints"] = hints

        except Exception as e:
            result["hints"] = [f"Ошибка при сборе диагностики: {e!s}"]
        return result

    @staticmethod
    def _publishing_channels(
        telegram_chat_id: Any,
        target_channels: Any,
    ) -> List[str]:
        """Список чатов публикации: сохранённые id + fallback на target_channels."""

        def _as_list(raw: Any) -> List[str]:
            if raw is None:
                return []
            if isinstance(raw, list):
                out: List[str] = []
                for item in raw:
                    if isinstance(item, dict):
                        cid = item.get("id") or item.get("channel") or item.get("chat_id")
                        if cid is not None and str(cid).strip():
                            out.append(str(cid).strip())
                    elif item is not None and str(item).strip():
                        out.append(str(item).strip())
                return out
            if isinstance(raw, str):
                s = raw.strip()
                if not s:
                    return []
                if s.startswith("["):
                    try:
                        parsed = json.loads(s)
                        return _as_list(parsed)
                    except Exception:
                        pass
                return [p.strip() for p in s.split(",") if p.strip()]
            return [str(raw).strip()] if str(raw).strip() else []

        stored = _as_list(telegram_chat_id)
        targets = _as_list(target_channels)
        # Старые записи: в telegram_chat_id только последний чат — дополняем из target_channels
        if targets and (not stored or (len(stored) == 1 and len(targets) > 1 and stored[0] in targets)):
            # сохраняем порядок target_channels
            return targets
        return stored or targets

    async def get_pipeline_events(self, limit: int = 50) -> Dict[str, Any]:
        """Списки срабатываний для вкладки Administration → Posts."""
        limit = max(1, min(int(limit or 50), 200))
        result: Dict[str, Any] = {
            "alerting": [],
            "publishing": [],
            "collection": [],
            "custom_url": [],
            "services": [],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                # Alerting
                await cur.execute(
                    """
                    SELECT id, user_id, chat_id, event_type, rule_id, text_preview,
                           metadata, created_at
                    FROM tg_events
                    WHERE event_type IN ('alert_sent', 'alert_matched', 'alert_suppressed')
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                for row in await cur.fetchall():
                    meta = row[6] or {}
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    channel = (meta or {}).get("channel") or (meta or {}).get("channel_title")
                    if not channel and row[2] is not None:
                        channel = f"source:{row[2]}"
                    result["alerting"].append(
                        {
                            "id": row[0],
                            "user_id": row[1],
                            "channel": str(channel) if channel else None,
                            "event_type": row[3],
                            "rule_id": row[4],
                            "summary": (row[5] or "")[:160],
                            "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else row[7],
                        }
                    )

                # Publishing (TG published posts) — по одной строке на каждый целевой чат
                await cur.execute(
                    """
                    SELECT t.id, t.user_id, p.channel_id, t.status, LEFT(COALESCE(p.post_text, ''), 160),
                           t.updated_at, t.created_at, t.target_channels
                    FROM post_targets t
                    JOIN posts p ON p.id = t.post_id
                    WHERE t.platform = 'tg' AND t.status = 'published'
                    ORDER BY COALESCE(updated_at, created_at) DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                for row in await cur.fetchall():
                    channels = self._publishing_channels(row[2], row[7])
                    if not channels:
                        channels = [None]
                    created = row[5] or row[6]
                    created_s = (
                        created.isoformat()
                        if hasattr(created, "isoformat")
                        else created
                    )
                    for channel in channels:
                        result["publishing"].append(
                            {
                                "id": row[0],
                                "user_id": row[1],
                                "channel": str(channel) if channel else None,
                                "event_type": "published",
                                "platform": "tg",
                                "summary": row[4] or "",
                                "created_at": created_s,
                            }
                        )

                # Collection / Parser
                await cur.execute(
                    """
                    SELECT id, user_id, chat_id, event_type, text_preview, metadata, created_at
                    FROM tg_events
                    WHERE event_type = 'collected'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                for row in await cur.fetchall():
                    result["collection"].append(
                        {
                            "id": row[0],
                            "user_id": row[1],
                            "channel": str(row[2]) if row[2] is not None else None,
                            "event_type": row[3],
                            "platform": "tg",
                            "summary": (row[4] or "")[:160],
                            "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
                        }
                    )

                # Custom URL
                await cur.execute(
                    """
                    SELECT id, user_id, url, status, LEFT(COALESCE(post_text, ''), 160), created_at
                    FROM posts
                    WHERE source_platform = 'url'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                for row in await cur.fetchall():
                    result["custom_url"].append(
                        {
                            "id": row[0],
                            "user_id": row[1],
                            "channel": row[2],
                            "event_type": row[3] or "collected",
                            "summary": row[4] or "",
                            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
                        }
                    )

                # Scheduler / collector / processor cycles
                try:
                    await cur.execute(
                        """
                        SELECT id, service_name, cycle_type, status, detail,
                               items_processed, created_at
                        FROM service_cycle_log
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    for row in await cur.fetchall():
                        result["services"].append(
                            {
                                "id": row[0],
                                "service": row[1],
                                "cycle_type": row[2],
                                "status": row[3],
                                "summary": row[4] or "",
                                "items_processed": row[5] or 0,
                                "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
                            }
                        )
                except Exception as e:
                    result["services"] = []
                    result["services_error"] = str(e)
        finally:
            await release_db_connection(conn)
        return result

    async def get_runtime_location(self) -> Dict[str, Any]:
        """Локальный hostname/TZ процесса core, публичный IP (ipify) и гео (ipapi.co, при 429 — ipwho.is)."""
        hostname = socket.gethostname()
        tz_env = os.environ.get("TZ")
        now = datetime.now().astimezone()
        tzinfo = now.tzinfo
        if tzinfo is not None:
            local_tz = getattr(tzinfo, "key", None) or str(tzinfo)
        else:
            local_tz = "UTC"
        offset = now.utcoffset()
        if offset is not None:
            total_sec = int(offset.total_seconds())
            sign = "+" if total_sec >= 0 else "-"
            total_sec = abs(total_sec)
            h, m = total_sec // 3600, (total_sec % 3600) // 60
            local_utc_offset = f"{sign}{h:02d}:{m:02d}"
        else:
            local_utc_offset = "+00:00"
        local_now_iso = now.isoformat(timespec="seconds")

        public_ip: Optional[str] = None
        public_lookup_error: Optional[str] = None
        geo_by_ip: Optional[Dict[str, Any]] = None
        geo_lookup_error: Optional[str] = None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                ip_resp = await client.get("https://api.ipify.org?format=json")
                if ip_resp.status_code == 200:
                    body = ip_resp.json()
                    public_ip = (body.get("ip") or "").strip() or None
                else:
                    public_lookup_error = f"ipify HTTP {ip_resp.status_code}"
                if public_ip:
                    geo_resp = await client.get(f"https://ipapi.co/{public_ip}/json/")
                    ipapi_err: Optional[str] = None
                    if geo_resp.status_code == 200:
                        data = geo_resp.json()
                        if data.get("error"):
                            ipapi_err = str(data.get("reason") or data.get("message") or data.get("error"))
                        else:
                            geo_by_ip = {
                                "country": data.get("country_name") or data.get("country"),
                                "region": data.get("region"),
                                "city": data.get("city"),
                                "timezone": data.get("timezone"),
                                "isp": data.get("org"),
                            }
                    else:
                        ipapi_err = f"ipapi.co HTTP {geo_resp.status_code}"

                    if geo_by_ip is None:
                        wh_resp = await client.get(f"https://ipwho.is/{public_ip}")
                        if wh_resp.status_code == 200:
                            wd = wh_resp.json()
                            if wd.get("success"):
                                tz_raw = wd.get("timezone")
                                if isinstance(tz_raw, dict):
                                    tz_id = tz_raw.get("id")
                                elif isinstance(tz_raw, str):
                                    tz_id = tz_raw
                                else:
                                    tz_id = None
                                conn = wd.get("connection")
                                isp = conn.get("isp") if isinstance(conn, dict) else None
                                geo_by_ip = {
                                    "country": wd.get("country"),
                                    "region": wd.get("region"),
                                    "city": wd.get("city"),
                                    "timezone": tz_id,
                                    "isp": isp,
                                }
                                geo_lookup_error = None
                            else:
                                geo_lookup_error = (
                                    f"{ipapi_err or 'ipapi.co failed'}; ipwho.is: {wd.get('message', 'success=false')}"
                                )
                        else:
                            geo_lookup_error = (
                                f"{ipapi_err or 'ipapi.co failed'}; ipwho.is HTTP {wh_resp.status_code}"
                            )
        except Exception as e:
            if public_ip is None:
                public_lookup_error = str(e)
            else:
                geo_lookup_error = str(e)

        aws_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

        return {
            "hostname": hostname,
            "tz_environment_variable": tz_env,
            "local_timezone": local_tz,
            "local_utc_offset": local_utc_offset,
            "local_now_iso": local_now_iso,
            "public_ip": public_ip,
            "public_lookup_error": public_lookup_error,
            "geo_by_ip": geo_by_ip,
            "geo_lookup_error": geo_lookup_error,
            "cloud_aws_region": aws_region,
        }


def _parse_loop_status(raw: Any) -> Optional[Dict[str, Any]]:
    """Преобразует ответ LoopStatus от collector/processor в словарь."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        last_run = raw.get("last_run_at")
        if isinstance(last_run, str):
            try:
                last_run = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            except Exception:
                pass
        return {
            "last_run_at": last_run,
            "total_processed": int(raw.get("total_processed", 0)),
            "last_cycle_count": int(raw.get("last_cycle_count", 0)),
        }
    return None


admin_service = AdminService()
