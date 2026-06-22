from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/cpost", tags=["Custom Post"])


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
async def get_cpost_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает профиль custom post из core сервиса.
    
    GET /cpost/profile -> GET /cpost/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/cpost/profile", request)


@router.post("/profile")
async def save_cpost_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Сохраняет профиль custom post в core сервисе.
    
    POST /cpost/profile -> POST /cpost/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/cpost/profile", request)


@router.get("/posts")
async def get_cpost_posts(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Список ручных постов пользователя."""
    return await forward_to_core("/cpost/posts", request)


@router.get("/post/{post_id}")
async def get_cpost_post(
    request: Request,
    post_id: int,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получить один ручной пост по id."""
    return await forward_to_core(f"/cpost/post/{post_id}", request)


@router.post("/post")
async def create_cpost_post(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Создает пост custom post в core сервисе.
    
    POST /cpost/post -> POST /cpost/post на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/cpost/post", request)


@router.put("/post/{post_id}")
async def update_cpost_post(
    request: Request,
    post_id: int,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обновить ручной пост."""
    return await forward_to_core(f"/cpost/post/{post_id}", request)


@router.delete("/post/{post_id}")
async def delete_cpost_post(
    request: Request,
    post_id: int,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Удалить ручной пост."""
    return await forward_to_core(f"/cpost/post/{post_id}", request)
