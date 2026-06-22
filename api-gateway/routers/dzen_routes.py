"""Маршруты API Gateway для Дзен (проксирование на Core)."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/dzen", tags=["Dzen"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    """Перенаправляет запрос на core сервис."""
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
    )


@router.get("/profile")
async def get_dzen_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /dzen/profile -> Core."""
    return await forward_to_core("/dzen/profile", request)


@router.post("/profile")
async def save_dzen_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen/profile -> Core."""
    return await forward_to_core("/dzen/profile", request)


@router.get("/profiles")
async def get_all_dzen_profiles(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /dzen/profiles -> Core."""
    return await forward_to_core("/dzen/profiles", request)


@router.get("/posts")
async def get_dzen_posts(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /dzen/posts -> Core."""
    return await forward_to_core("/dzen/posts", request)


@router.get("/post/{post_id}")
async def get_dzen_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /dzen/post/{post_id} -> Core."""
    return await forward_to_core(f"/dzen/post/{post_id}", request)


@router.put("/post/{post_id}")
async def update_dzen_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """PUT /dzen/post/{post_id} -> Core."""
    return await forward_to_core(f"/dzen/post/{post_id}", request)


@router.delete("/post/{post_id}")
async def delete_dzen_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """DELETE /dzen/post/{post_id} -> Core."""
    return await forward_to_core(f"/dzen/post/{post_id}", request)


@router.post("/post")
async def create_dzen_post(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /dzen/post -> Core."""
    return await forward_to_core("/dzen/post", request)


@router.get("/rss/{user_id}")
async def get_dzen_rss(
    user_id: int,
    request: Request,
) -> Response:
    """GET /dzen/rss/{user_id} -> Core. Публичный эндпоинт для робота Дзена (без JWT)."""
    return await forward_to_core(f"/dzen/rss/{user_id}", request)
