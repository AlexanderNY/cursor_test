from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter(tags=["Stubs"])


# Шаблон ответа для заглушек
STUB_RESPONSE_TEMPLATE: dict = {
    "status": "stub",
    "message": "Service not implemented yet"
}


def create_stub_response(service_name: str) -> JSONResponse:
    """Создает JSON ответ заглушки для сервиса.
    
    Args:
        service_name: Название сервиса
    
    Returns:
        JSONResponse с информацией о заглушке
    """
    return JSONResponse(
        status_code=501,
        content={
            **STUB_RESPONSE_TEMPLATE,
            "service": service_name
        }
    )


# ============== Scheduler Service ==============
@router.api_route(
    "/scheduler/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def handle_scheduler_stub(path: str) -> JSONResponse:
    """Заглушка для scheduler сервиса.
    
    Все запросы к /scheduler/* возвращают 501 Not Implemented.
    """
    return create_stub_response("scheduler")


@router.api_route("/scheduler", methods=["GET", "POST"])
async def handle_scheduler_root_stub() -> JSONResponse:
    """Заглушка для корневого endpoint scheduler сервиса."""
    return create_stub_response("scheduler")


# ============== Telegram Bot Service ==============
@router.api_route(
    "/tg-bot/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def handle_tg_bot_stub(path: str) -> JSONResponse:
    """Заглушка для tg-bot сервиса.
    
    Все запросы к /tg-bot/* возвращают 501 Not Implemented.
    """
    return create_stub_response("tg-bot")


@router.api_route("/tg-bot", methods=["GET", "POST"])
async def handle_tg_bot_root_stub() -> JSONResponse:
    """Заглушка для корневого endpoint tg-bot сервиса."""
    return create_stub_response("tg-bot")


# ============== VK Bot Service ==============
@router.api_route(
    "/vk-bot/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def handle_vk_bot_stub(path: str) -> JSONResponse:
    """Заглушка для vk-bot сервиса.
    
    Все запросы к /vk-bot/* возвращают 501 Not Implemented.
    """
    return create_stub_response("vk-bot")


@router.api_route("/vk-bot", methods=["GET", "POST"])
async def handle_vk_bot_root_stub() -> JSONResponse:
    """Заглушка для корневого endpoint vk-bot сервиса."""
    return create_stub_response("vk-bot")


# ============== WordPress Bot Service ==============
@router.api_route(
    "/wp-bot/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def handle_wp_bot_stub(path: str) -> JSONResponse:
    """Заглушка для wp-bot сервиса.
    
    Все запросы к /wp-bot/* возвращают 501 Not Implemented.
    """
    return create_stub_response("wp-bot")


@router.api_route("/wp-bot", methods=["GET", "POST"])
async def handle_wp_bot_root_stub() -> JSONResponse:
    """Заглушка для корневого endpoint wp-bot сервиса."""
    return create_stub_response("wp-bot")


# ============== URL Bot Service ==============
@router.api_route(
    "/url-bot/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def handle_url_bot_stub(path: str) -> JSONResponse:
    """Заглушка для url-bot сервиса.
    
    Все запросы к /url-bot/* возвращают 501 Not Implemented.
    """
    return create_stub_response("url-bot")


@router.api_route("/url-bot", methods=["GET", "POST"])
async def handle_url_bot_root_stub() -> JSONResponse:
    """Заглушка для корневого endpoint url-bot сервиса."""
    return create_stub_response("url-bot")


