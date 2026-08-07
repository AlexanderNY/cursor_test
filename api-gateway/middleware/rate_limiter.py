import time
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config import RATE_LIMITS_CONFIG
from utils.exceptions import create_error_response


# Порог и периодичность cleanup; hard cap на число ключей
CLEANUP_LEN_THRESHOLD = 500
CLEANUP_EVERY_N_OPS = 100
MAX_KEYS = 10_000


class RateLimiter:
    """In-memory хранилище для rate limiting.
    
    Fixed window: IP + нормализованный path (конфиг лимита).
    Истекшие ключи чистятся периодически; размер словаря ограничен MAX_KEYS.
    """

    # Разделитель ключа (не конфликтует с IPv6 ':')
    _KEY_SEP = "|"

    def __init__(self) -> None:
        # Структура: {key: {"count": int, "window_start": float}}
        self.request_counts: dict[str, dict] = {}
        self._ops: int = 0

    def normalize_endpoint_path(self, endpoint_path: str) -> str:
        """Путь для ключа/конфига: точное совпадение, префикс или default."""
        if endpoint_path in RATE_LIMITS_CONFIG:
            return endpoint_path

        path_parts = endpoint_path.rstrip("/").split("/")
        if len(path_parts) > 1:
            prefix_path = "/".join(path_parts[:-1])
            if prefix_path in RATE_LIMITS_CONFIG:
                return prefix_path

        return "default"

    def get_rate_limit_key(self, client_ip: str, endpoint_path: str) -> str:
        """Ключ: IP + нормализованный path лимита."""
        limit_path = self.normalize_endpoint_path(endpoint_path)
        return f"{client_ip}{self._KEY_SEP}{limit_path}"

    def get_limit_config(self, endpoint_path: str) -> dict[str, int]:
        """Конфигурация лимита для endpoint (requests, window_seconds)."""
        limit_path = self.normalize_endpoint_path(endpoint_path)
        return RATE_LIMITS_CONFIG[limit_path]

    def _limit_path_from_key(self, key: str) -> str:
        """Извлекает нормализованный path из ключа."""
        if self._KEY_SEP in key:
            return key.split(self._KEY_SEP, 1)[1]
        # Совместимость со старым форматом ip:path
        if ":/" in key:
            return key[key.index(":/") + 1 :]
        if key.endswith(":default"):
            return "default"
        return "default"

    def check_rate_limit(self, client_ip: str, endpoint_path: str) -> bool:
        """True если запрос разрешён, False если лимит превышен."""
        key = self.get_rate_limit_key(client_ip, endpoint_path)
        limit_config = self.get_limit_config(endpoint_path)
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window_seconds"]

        current_time = time.time()

        if key not in self.request_counts:
            return True

        record = self.request_counts[key]
        window_start = record["window_start"]

        if current_time - window_start >= window_seconds:
            return True

        return record["count"] < max_requests

    def increment_counter(self, client_ip: str, endpoint_path: str) -> None:
        """Увеличивает счётчик запросов и при необходимости чистит память."""
        key = self.get_rate_limit_key(client_ip, endpoint_path)
        limit_config = self.get_limit_config(endpoint_path)
        window_seconds = limit_config["window_seconds"]

        current_time = time.time()

        if key not in self.request_counts:
            self.request_counts[key] = {
                "count": 1,
                "window_start": current_time,
            }
        else:
            record = self.request_counts[key]
            if current_time - record["window_start"] >= window_seconds:
                self.request_counts[key] = {
                    "count": 1,
                    "window_start": current_time,
                }
            else:
                record["count"] += 1

        self._ops += 1
        self.maybe_cleanup()

    def reset_expired_counters(self) -> int:
        """Удаляет записи с истёкшим окном. Возвращает число удалённых."""
        current_time = time.time()
        keys_to_delete: list[str] = []

        for key, record in self.request_counts.items():
            limit_path = self._limit_path_from_key(key)
            limit_config = RATE_LIMITS_CONFIG.get(
                limit_path, RATE_LIMITS_CONFIG["default"]
            )
            window_seconds = limit_config["window_seconds"]

            if current_time - record["window_start"] >= window_seconds:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.request_counts[key]

        return len(keys_to_delete)

    def evict_oldest(self, target_size: int = MAX_KEYS) -> int:
        """Удаляет самые старые по window_start записи, пока len > target_size."""
        overflow = len(self.request_counts) - target_size
        if overflow <= 0:
            return 0

        oldest = sorted(
            self.request_counts.items(),
            key=lambda item: item[1]["window_start"],
        )[:overflow]

        for key, _ in oldest:
            del self.request_counts[key]

        return overflow

    def maybe_cleanup(self) -> None:
        """Cleanup по порогу длины или каждые N операций; затем hard cap."""
        should_cleanup = (
            len(self.request_counts) >= CLEANUP_LEN_THRESHOLD
            or self._ops % CLEANUP_EVERY_N_OPS == 0
        )
        if not should_cleanup:
            return

        self.reset_expired_counters()
        if len(self.request_counts) > MAX_KEYS:
            self.evict_oldest(MAX_KEYS)

    def get_remaining_requests(self, client_ip: str, endpoint_path: str) -> int:
        """Оставшееся число запросов в текущем окне."""
        key = self.get_rate_limit_key(client_ip, endpoint_path)
        limit_config = self.get_limit_config(endpoint_path)
        max_requests = limit_config["requests"]

        if key not in self.request_counts:
            return max_requests

        record = self.request_counts[key]
        current_time = time.time()
        window_seconds = limit_config["window_seconds"]

        if current_time - record["window_start"] >= window_seconds:
            return max_requests

        return max(0, max_requests - record["count"])


# Глобальный экземпляр RateLimiter
rate_limiter = RateLimiter()


def extract_client_ip(request: Request) -> str:
    """Извлекает IP клиента (X-Forwarded-For / X-Real-IP / client.host)."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для применения rate limiting к запросам."""

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = extract_client_ip(request)
        endpoint_path = request.url.path

        if endpoint_path == "/health":
            return await call_next(request)

        if not rate_limiter.check_rate_limit(client_ip, endpoint_path):
            return create_error_response(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )

        rate_limiter.increment_counter(client_ip, endpoint_path)

        response = await call_next(request)

        limit_config = rate_limiter.get_limit_config(endpoint_path)
        remaining = rate_limiter.get_remaining_requests(client_ip, endpoint_path)

        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(limit_config["window_seconds"])

        return response


async def apply_rate_limit(request: Request, call_next) -> Response:
    """Применяет rate limiting к запросу (функциональный стиль)."""
    middleware = RateLimitMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
