import time
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config import RATE_LIMITS_CONFIG
from utils.exceptions import RateLimitExceededException, create_error_response


class RateLimiter:
    """In-memory хранилище для rate limiting.
    
    Использует скользящее окно для отслеживания количества запросов.
    Ключ: комбинация IP клиента и endpoint path.
    """
    
    def __init__(self):
        # Структура: {key: {"count": int, "window_start": float}}
        self.request_counts: dict[str, dict] = {}
    
    def get_rate_limit_key(self, client_ip: str, endpoint_path: str) -> str:
        """Формирует ключ для rate limit счетчика.
        
        Args:
            client_ip: IP адрес клиента
            endpoint_path: Путь endpoint'а
        
        Returns:
            Уникальный ключ для хранилища
        """
        return f"{client_ip}:{endpoint_path}"
    
    def get_limit_config(self, endpoint_path: str) -> dict[str, int]:
        """Получает конфигурацию лимита для endpoint.
        
        Args:
            endpoint_path: Путь endpoint'а
        
        Returns:
            Словарь с requests и window_seconds
        """
        # Ищем точное совпадение
        if endpoint_path in RATE_LIMITS_CONFIG:
            return RATE_LIMITS_CONFIG[endpoint_path]
        
        # Для путей с параметрами ищем по префиксу
        # Например, /core/schedule/42 -> /core/schedule
        path_parts = endpoint_path.rstrip('/').split('/')
        if len(path_parts) > 1:
            # Пробуем найти конфиг по префиксу (без последнего сегмента)
            prefix_path = '/'.join(path_parts[:-1])
            if prefix_path in RATE_LIMITS_CONFIG:
                return RATE_LIMITS_CONFIG[prefix_path]
        
        # Используем default
        return RATE_LIMITS_CONFIG["default"]
    
    def check_rate_limit(self, client_ip: str, endpoint_path: str) -> bool:
        """Проверяет, не превышен ли лимит запросов.
        
        Args:
            client_ip: IP адрес клиента
            endpoint_path: Путь endpoint'а
        
        Returns:
            True если запрос разрешен, False если лимит превышен
        """
        key = self.get_rate_limit_key(client_ip, endpoint_path)
        limit_config = self.get_limit_config(endpoint_path)
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window_seconds"]
        
        current_time = time.time()
        
        if key not in self.request_counts:
            return True
        
        record = self.request_counts[key]
        window_start = record["window_start"]
        
        # Если окно истекло, разрешаем запрос
        if current_time - window_start >= window_seconds:
            return True
        
        # Проверяем количество запросов в текущем окне
        return record["count"] < max_requests
    
    def increment_counter(self, client_ip: str, endpoint_path: str) -> None:
        """Увеличивает счетчик запросов для клиента.
        
        Args:
            client_ip: IP адрес клиента
            endpoint_path: Путь endpoint'а
        """
        key = self.get_rate_limit_key(client_ip, endpoint_path)
        limit_config = self.get_limit_config(endpoint_path)
        window_seconds = limit_config["window_seconds"]
        
        current_time = time.time()
        
        if key not in self.request_counts:
            self.request_counts[key] = {
                "count": 1,
                "window_start": current_time
            }
            return
        
        record = self.request_counts[key]
        
        # Если окно истекло, начинаем новое
        if current_time - record["window_start"] >= window_seconds:
            self.request_counts[key] = {
                "count": 1,
                "window_start": current_time
            }
        else:
            record["count"] += 1
    
    def reset_expired_counters(self) -> int:
        """Сбрасывает истекшие счетчики для освобождения памяти.
        
        Returns:
            Количество удаленных записей
        """
        current_time = time.time()
        keys_to_delete = []
        
        for key, record in self.request_counts.items():
            # Получаем endpoint из ключа для определения window
            endpoint_path = key.split(":", 1)[1] if ":" in key else "default"
            limit_config = self.get_limit_config(endpoint_path)
            window_seconds = limit_config["window_seconds"]
            
            if current_time - record["window_start"] >= window_seconds:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.request_counts[key]
        
        return len(keys_to_delete)
    
    def get_remaining_requests(self, client_ip: str, endpoint_path: str) -> int:
        """Получает оставшееся количество запросов.
        
        Args:
            client_ip: IP адрес клиента
            endpoint_path: Путь endpoint'а
        
        Returns:
            Количество оставшихся запросов
        """
        key = self.get_rate_limit_key(client_ip, endpoint_path)
        limit_config = self.get_limit_config(endpoint_path)
        max_requests = limit_config["requests"]
        
        if key not in self.request_counts:
            return max_requests
        
        record = self.request_counts[key]
        current_time = time.time()
        window_seconds = limit_config["window_seconds"]
        
        # Если окно истекло
        if current_time - record["window_start"] >= window_seconds:
            return max_requests
        
        return max(0, max_requests - record["count"])


# Глобальный экземпляр RateLimiter
rate_limiter = RateLimiter()


def extract_client_ip(request: Request) -> str:
    """Извлекает IP адрес клиента из запроса.
    
    Учитывает X-Forwarded-For header для работы за прокси/балансировщиком.
    
    Args:
        request: FastAPI Request объект
    
    Returns:
        IP адрес клиента
    """
    # Проверяем X-Forwarded-For (для прокси)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Берем первый IP из списка (оригинальный клиент)
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IP (альтернативный header)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Fallback на client host
    if request.client:
        return request.client.host
    
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для применения rate limiting к запросам."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Обрабатывает запрос и применяет rate limiting.
        
        Args:
            request: Входящий запрос
            call_next: Следующий обработчик в цепочке
        
        Returns:
            Response от следующего обработчика или ошибка 429
        """
        client_ip = extract_client_ip(request)
        endpoint_path = request.url.path
        
        # Пропускаем rate limiting для health endpoint
        if endpoint_path == "/health":
            return await call_next(request)
        
        # Проверяем лимит
        if not rate_limiter.check_rate_limit(client_ip, endpoint_path):
            return create_error_response(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Увеличиваем счетчик
        rate_limiter.increment_counter(client_ip, endpoint_path)
        
        # Добавляем headers с информацией о лимитах
        response = await call_next(request)
        
        limit_config = rate_limiter.get_limit_config(endpoint_path)
        remaining = rate_limiter.get_remaining_requests(client_ip, endpoint_path)
        
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(limit_config["window_seconds"])
        
        return response


# Функция для использования как middleware (альтернативный вариант)
async def apply_rate_limit(request: Request, call_next) -> Response:
    """Применяет rate limiting к запросу (функциональный стиль).
    
    Args:
        request: Входящий запрос
        call_next: Следующий обработчик
    
    Returns:
        Response
    """
    middleware = RateLimitMiddleware(app=None)
    return await middleware.dispatch(request, call_next)


