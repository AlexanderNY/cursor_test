from contextlib import asynccontextmanager
from datetime import datetime
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings, get_cors_origins_list
from services.proxy_service import initialize_proxy_service
from middleware.rate_limiter import RateLimitMiddleware
from middleware.jwt_validator import validate_jwt_middleware
from routers import (
    auth_router,
    core_router,
    wp_router,
    tg_router,
    tw_router,
    vk_router,
    dzen_router,
    instagram_router,
    curl_router,
    cpost_router,
    bot_proxy_router,
    threads_router,
    stubs_router,
)
from utils.exceptions import (
    GatewayException,
    handle_gateway_exception,
    TokenValidationException,
)


@asynccontextmanager
async def manage_lifespan(app: FastAPI):
    """Управляет жизненным циклом приложения.
    
    Startup: инициализация HTTP клиента для проксирования.
    Shutdown: закрытие HTTP клиента.
    """
    # Startup
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        follow_redirects=True
    )
    app.state.http_client = http_client
    initialize_proxy_service(http_client)
    
    yield
    
    # Shutdown
    await http_client.aclose()


app = FastAPI(
    title="API Gateway",
    description="Gateway для маршрутизации запросов между микросервисами",
    version="1.0.0",
    lifespan=manage_lifespan
)


def configure_cors(application: FastAPI) -> None:
    """Настраивает CORS middleware.
    
    Args:
        application: FastAPI приложение
    """
    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins_list(),
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOWED_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )


def register_routers(application: FastAPI) -> None:
    """Регистрирует роутеры приложения.
    
    Args:
        application: FastAPI приложение
    """
    application.include_router(auth_router)
    application.include_router(core_router)
    application.include_router(wp_router)
    application.include_router(tg_router)
    application.include_router(tw_router)
    application.include_router(vk_router)
    application.include_router(dzen_router)
    application.include_router(instagram_router)
    application.include_router(curl_router)
    application.include_router(cpost_router)
    application.include_router(bot_proxy_router)
    application.include_router(threads_router)
    application.include_router(stubs_router)


def register_exception_handlers(application: FastAPI) -> None:
    """Регистрирует обработчики исключений.
    
    Args:
        application: FastAPI приложение
    """
    @application.exception_handler(GatewayException)
    async def gateway_exception_handler(request: Request, exc: GatewayException):
        return handle_gateway_exception(request, exc)
    
    @application.exception_handler(TokenValidationException)
    async def token_validation_exception_handler(request: Request, exc: TokenValidationException):
        return handle_gateway_exception(request, exc)


# Настройка CORS (должен быть первым middleware)
configure_cors(app)

# Rate Limiting middleware
app.add_middleware(RateLimitMiddleware)

# Регистрация роутеров
register_routers(app)

# Регистрация обработчиков исключений
register_exception_handlers(app)


@app.get("/")
async def root():
    """Корневой endpoint API Gateway."""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def check_health():
    """Проверяет здоровье сервиса.
    
    Returns:
        Статус здоровья gateway
    """
    return {
        "status": "healthy",
        "service": "api-gateway",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/routes")
async def list_routes():
    """Возвращает список всех доступных маршрутов.
    
    Полезно для отладки и документации.
    """
    routes_list = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes_list.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name
            })
    return {"routes": routes_list}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


