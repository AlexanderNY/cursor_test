"""Gateway proxy for Learn (9to18) → Core."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/learn", tags=["Learn"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
    )


@router.get("/posts")
async def list_posts(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/posts", request)


@router.get("/posts/{slug}")
async def get_post(
    slug: str,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    return await forward_to_core(f"/learn/posts/{slug}", request)


@router.get("/promo")
async def get_promo(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    """Публичный рекламный пост главной 9to18.ru."""
    return await forward_to_core("/learn/promo", request)


@router.put("/admin/promo")
async def put_promo(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/admin/promo", request)


@router.get("/admin/posts")
async def admin_list(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/admin/posts", request)


@router.post("/admin/posts")
async def admin_upsert(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/admin/posts", request)


@router.patch("/admin/posts/{slug}")
async def admin_patch(
    slug: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core(f"/learn/admin/posts/{slug}", request)


@router.delete("/admin/posts/{slug}")
async def admin_delete(
    slug: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core(f"/learn/admin/posts/{slug}", request)


@router.post("/admin/reset-to-seed")
async def admin_reset(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/admin/reset-to-seed", request)


@router.post("/admin/schedule")
async def admin_schedule(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/admin/schedule", request)


@router.post("/contact")
async def submit_contact(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    """Публичная форма обратной связи 9to18.ru."""
    return await forward_to_core("/learn/contact", request)


@router.get("/progress")
async def get_progress(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/progress", request)


@router.put("/progress")
async def put_progress(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    return await forward_to_core("/learn/progress", request)
