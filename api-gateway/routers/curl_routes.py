from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/curl", tags=["Curl"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    """Перенаправляет запрос на core сервис.
    
    Args:
        target_path: Путь на core сервисе
        request: FastAPI Request объект
    
    Returns:
        Response от core сервиса
    """
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request
    )


@router.get("/settings")
async def get_curl_settings(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает настройки curl из core сервиса.
    
    GET /curl/settings -> GET /curl/settings на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/curl/settings", request)


@router.get("/posts")
async def get_curl_posts(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает список постов из url_posts (собранные по URL).
    
    GET /curl/posts -> GET /curl/posts на core сервисе.
    """
    return await forward_to_core("/curl/posts", request)


@router.post("/settings")
async def save_curl_settings(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Сохраняет настройки curl в core сервисе.
    
    POST /curl/settings -> POST /curl/settings на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/curl/settings", request)


@router.post("/url-posts")
async def save_url_posts(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Сохраняет пакет постов из url-bot в url_posts (Core).
    
    POST /curl/url-posts -> POST /curl/url-posts на core сервисе.
    Вызывается scheduler после ответа url-bot /schedule.
    """
    return await forward_to_core("/curl/url-posts", request)


@router.post("/one-time-done")
async def curl_one_time_done(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Отмечает одноразовые URL как выполненные (Core).
    
    POST /curl/one-time-done -> POST /curl/one-time-done на core сервисе.
    Вызывается scheduler после успешного выполнения run_once URL.
    """
    return await forward_to_core("/curl/one-time-done", request)
