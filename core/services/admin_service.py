"""Сервис для админ-эндпоинтов: статус сервисов и обзор таблиц постов."""

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
        """Запускает один цикл сбора на collector. Проксирует POST /collect/run."""
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
        """Запускает один цикл распределения на collector. Проксирует POST /distribute/run."""
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
        """Запускает цикл диагностики постинга: сводки tg_posts/posts по статусам и подсказки."""
        result: Dict[str, Any] = {
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
                        FROM tg_posts
                        GROUP BY status
                        ORDER BY status
                        """
                    )
                    rows = await cur.fetchall()
                    result["tg_posts_by_status"] = [
                        {"status": r[0], "count": r[1]} for r in rows
                    ]

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
                        SELECT COUNT(*) FROM tg_posts p
                        JOIN tg_profiles pr ON p.user_id = pr.user_id
                        WHERE p.status = 'ready'
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
            tg_by_status = {r["status"]: r["count"] for r in result["tg_posts_by_status"]}
            posts_list = result["posts_by_status"]

            collected_tg = tg_by_status.get("collected", 0)
            if collected_tg > 0:
                hints.append(
                    f"В tg_posts {collected_tg} постов со статусом collected. "
                    "Проверьте, что запущен Collector и цикл collect забирает посты в posts."
                )
            processing_tg = tg_by_status.get("processing", 0)
            ready_tg = tg_by_status.get("ready", 0)
            if processing_tg > 0 and ready_tg == 0:
                hints.append(
                    f"В tg_posts {processing_tg} постов в processing, 0 в ready. "
                    "После обработки в Processor дистрибьютор должен обновить tg_posts до ready. "
                    "Проверьте Collector (distribute) и флаг to_tg у постов."
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
                    f"В posts {posts_ready} постов в статусе ready, но в tg_posts нет постов ready для публикации. "
                    "Проверьте Collector (distribute) и что у постов из TG включён to_tg."
                )
            if result["ready_for_telegram"] > 0 and result["profiles_with_channel"] == 0:
                hints.append(
                    "Есть посты ready в tg_posts, но ни у одного профиля не задан channel_to_post. "
                    "Задайте канал для публикации в tg_profiles."
                )
            if not hints:
                hints.append("Явных проблем по сводкам не обнаружено. Проверьте логи сервисов при необходимости.")
            result["hints"] = hints

        except Exception as e:
            result["hints"] = [f"Ошибка при сборе диагностики: {e!s}"]
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
