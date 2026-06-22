from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/tw", tags=["Twitter"])


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


@router.get("/profile")
async def get_tw_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает профиль Twitter из core сервиса.
    
    GET /tw/profile -> GET /tw/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tw/profile", request)


@router.post("/profile")
async def save_tw_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Сохраняет профиль Twitter в core сервисе.
    
    POST /tw/profile -> POST /tw/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tw/profile", request)


@router.get("/profiles")
async def get_all_tw_profiles(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает все профили Twitter из core сервиса.
    
    GET /tw/profiles -> GET /tw/profiles на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tw/profiles", request)


@router.post("/post")
async def create_tw_post(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Создает пост Twitter в core сервисе.
    
    POST /tw/post -> POST /tw/post на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tw/post", request)


@router.get("/following")
async def get_tw_following(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Список подписок X (following) из core."""
    return await forward_to_core("/tw/following", request)
