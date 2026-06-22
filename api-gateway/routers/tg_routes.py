from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/tg", tags=["Telegram"])


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
async def get_tg_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает профиль Telegram из core сервиса.
    
    GET /tg/profile -> GET /tg/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tg/profile", request)


@router.post("/profile")
async def save_tg_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Сохраняет профиль Telegram в core сервисе.
    
    POST /tg/profile -> POST /tg/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tg/profile", request)


@router.get("/profiles")
async def get_all_tg_profiles(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает все профили Telegram из core сервиса.
    
    GET /tg/profiles -> GET /tg/profiles на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tg/profiles", request)


@router.post("/post")
async def create_tg_post(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Создает пост Telegram в core сервисе.
    
    POST /tg/post -> POST /tg/post на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tg/post", request)


@router.get("/posts")
async def get_tg_posts(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает список постов Telegram из core сервиса.
    
    GET /tg/posts -> GET /tg/posts на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/tg/posts", request)


@router.get("/post/{post_id}")
async def get_tg_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает один пост Telegram из core сервиса.
    
    GET /tg/post/{post_id} -> GET /tg/post/{post_id} на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core(f"/tg/post/{post_id}", request)


@router.put("/post/{post_id}")
async def update_tg_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обновляет пост Telegram в core сервисе.
    
    PUT /tg/post/{post_id} -> PUT /tg/post/{post_id} на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core(f"/tg/post/{post_id}", request)


@router.delete("/post/{post_id}")
async def delete_tg_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Удаляет пост Telegram в core сервисе.
    
    DELETE /tg/post/{post_id} -> DELETE /tg/post/{post_id} на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core(f"/tg/post/{post_id}", request)


@router.get("/uploads/{filename}")
async def get_tg_upload(
    filename: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Отдаёт файл из uploads/tg (core) для превью в UI.
    
    GET /tg/uploads/{filename} -> GET /tg/uploads/{filename} на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core(f"/tg/uploads/{filename}", request)
