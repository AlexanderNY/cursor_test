"""Сервис для проверки здоровья всех сервисов."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

import httpx

from config import settings
from shared.circuit_breaker import CircuitBreaker


@dataclass
class _CacheEntry:
    results: List[Dict]
    expires_at: float


# Боты/воркеры и AI могут быть не подняты — error не означает «весь стек мёртв».
_OPTIONAL_SERVICES: Set[str] = {
    "tg-bot",
    "vk-bot",
    "wp-bot",
    "url-bot",
    "tw-bot",
    "instagram-bot",
    "th-bot",
    "dzen-bot",
    "tg-game",
    "collector",
    "processor",
    "ollama",
}


class HealthcheckService:
    """Опрос /health микросервисов: parallel + cache + circuit breaker."""

    def __init__(self) -> None:
        self.services = {
            "auth": settings.AUTH_SERVICE_URL,
            "core": None,  # self — без HTTP
            "api-gateway": settings.API_GATEWAY_URL,
            "tg-bot": settings.TG_BOT_SERVICE_URL,
            "vk-bot": settings.VK_BOT_SERVICE_URL,
            "wp-bot": settings.WP_BOT_SERVICE_URL,
            "url-bot": settings.URL_BOT_SERVICE_URL,
            "tw-bot": settings.TW_BOT_SERVICE_URL,
            "scheduler": settings.SCHEDULER_SERVICE_URL,
            "collector": settings.COLLECTOR_SERVICE_URL,
            "processor": settings.PROCESSOR_SERVICE_URL,
            "ollama": os.getenv("AI_SERVICE_URL", "http://ollama:11434"),
        }
        self._circuits: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker(
                name=f"health:{name}",
                failure_threshold=settings.HEALTHCHECK_CIRCUIT_FAILURE_THRESHOLD,
                recovery_timeout_sec=settings.HEALTHCHECK_CIRCUIT_RECOVERY_SECONDS,
            )
            for name in self.services
            if name != "core"
        }
        self._cache: Optional[_CacheEntry] = None
        self._cache_lock = asyncio.Lock()
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=settings.HEALTHCHECK_REQUEST_TIMEOUT_SECONDS
            )
        return self._http_client

    @staticmethod
    def _is_optional(name: str) -> bool:
        return name in _OPTIONAL_SERVICES

    def _core_local_result(self) -> Dict:
        return {
            "service_name": "core",
            "status": "ok",
            "error": None,
            "server_time": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "optional": False,
        }

    async def check_service(self, name: str, url: Optional[str]) -> Dict:
        """Проверяет здоровье одного сервиса."""
        optional = self._is_optional(name)
        if name == "core" or not url:
            return self._core_local_result()

        circuit = self._circuits[name]
        if not circuit.allow_request():
            return {
                "service_name": name,
                "status": "error",
                "error": "Circuit open",
                "server_time": None,
                "optional": optional,
            }

        try:
            client = self._get_client()
            # Ollama не имеет /health — используем /api/tags.
            path = "/api/tags" if name == "ollama" else "/health"
            response = await client.get(f"{url.rstrip('/')}{path}")
            if response.status_code == 200:
                data = response.json() if response.content else {}
                server_time = data.get("server_time") if isinstance(data, dict) else None
                circuit.record_success()
                return {
                    "service_name": name,
                    "status": "ok",
                    "error": None,
                    "server_time": server_time,
                    "optional": optional,
                }

            circuit.record_failure()
            return {
                "service_name": name,
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "server_time": None,
                "optional": optional,
            }
        except httpx.ConnectError:
            circuit.record_failure()
            return {
                "service_name": name,
                "status": "error",
                "error": "Connection refused",
                "server_time": None,
                "optional": optional,
            }
        except httpx.TimeoutException:
            circuit.record_failure()
            return {
                "service_name": name,
                "status": "error",
                "error": "Timeout",
                "server_time": None,
                "optional": optional,
            }
        except Exception as e:
            circuit.record_failure()
            return {
                "service_name": name,
                "status": "error",
                "error": str(e),
                "server_time": None,
                "optional": optional,
            }

    async def _fetch_all_services(self) -> List[Dict]:
        """Параллельный опрос всех сервисов."""
        tasks = [
            self.check_service(name, url) for name, url in self.services.items()
        ]
        return list(await asyncio.gather(*tasks))

    async def check_all_services(self) -> List[Dict]:
        """Проверяет здоровье всех сервисов (с кэшем TTL)."""
        now = time.monotonic()
        cached = self._cache
        if cached is not None and now < cached.expires_at:
            return cached.results

        async with self._cache_lock:
            cached = self._cache
            now = time.monotonic()
            if cached is not None and now < cached.expires_at:
                return cached.results

            results = await self._fetch_all_services()
            self._cache = _CacheEntry(
                results=results,
                expires_at=time.monotonic() + settings.HEALTHCHECK_CACHE_TTL_SECONDS,
            )
            return results


healthcheck_service = HealthcheckService()
