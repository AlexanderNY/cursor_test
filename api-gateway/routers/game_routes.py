"""Проксирование админ-API игры (tg-game) с проверкой роли admin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from config import settings
from middleware.jwt_validator import get_current_user
from services.proxy_service import get_proxy_service

router = APIRouter(tags=["Game"])


def _require_admin(current_user: dict | None) -> dict:
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def _forward_game_admin(target_path: str, request: Request) -> Response:
    admin_token = (settings.GAME_ADMIN_API_TOKEN or "").strip()
    if not admin_token:
        raise HTTPException(
            status_code=503,
            detail="GAME_ADMIN_API_TOKEN is not configured on API gateway",
        )

    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.TG_GAME_SERVICE_URL, target_path)
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
        extra_headers={"X-Game-Admin-Token": admin_token},
    )


@router.get("/tg/game/admin/bots")
async def list_game_bots(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/bots", request)


@router.post("/tg/game/admin/bots")
async def create_game_bot(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/bots", request)


@router.patch("/tg/game/admin/bots/{bot_id}")
async def update_game_bot(
    bot_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/bots/{bot_id}", request)


@router.delete("/tg/game/admin/bots/{bot_id}")
async def delete_game_bot(
    bot_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/bots/{bot_id}", request)


@router.post("/tg/game/admin/modes")
async def create_game_mode(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/modes", request)


@router.get("/tg/game/admin/modes")
async def list_game_modes(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/modes", request)


@router.patch("/tg/game/admin/modes/{mode_id}")
async def update_game_mode(
    mode_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/modes/{mode_id}", request)


@router.delete("/tg/game/admin/modes/{mode_id}")
async def delete_game_mode(
    mode_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/modes/{mode_id}", request)


@router.get("/tg/game/admin/modes/{mode_id}/questions")
async def list_game_questions(
    mode_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/modes/{mode_id}/questions", request)


@router.get("/tg/game/admin/modes/{mode_id}/menu-nodes")
async def list_game_menu_nodes(
    mode_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/modes/{mode_id}/menu-nodes", request)


@router.post("/tg/game/admin/menu-nodes")
async def create_game_menu_node(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/menu-nodes", request)


@router.patch("/tg/game/admin/menu-nodes/{node_id}")
async def update_game_menu_node(
    node_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/menu-nodes/{node_id}", request)


@router.delete("/tg/game/admin/menu-nodes/{node_id}")
async def delete_game_menu_node(
    node_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/menu-nodes/{node_id}", request)


@router.get("/tg/game/admin/orders")
async def list_game_orders(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/orders", request)


@router.get("/tg/game/admin/orders/{order_id}")
async def get_game_order(
    order_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/orders/{order_id}", request)


@router.get("/tg/game/admin/questions/{question_id}")
async def get_game_question(
    question_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/questions/{question_id}", request)


@router.post("/tg/game/admin/questions")
async def create_game_question(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/questions", request)


@router.patch("/tg/game/admin/questions/{question_id}")
async def update_game_question(
    question_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/questions/{question_id}", request)


@router.delete("/tg/game/admin/questions/{question_id}")
async def delete_game_question(
    question_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/questions/{question_id}", request)


@router.put("/tg/game/admin/questions/{question_id}/options")
async def replace_game_question_options(
    question_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(
        f"/tg/game/admin/questions/{question_id}/options",
        request,
    )


@router.get("/tg/game/admin/media")
async def list_game_media(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/media", request)


@router.post("/tg/game/admin/media")
async def upload_game_media(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/media", request)


@router.patch("/tg/game/admin/media/{asset_id}")
async def update_game_media(
    asset_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/media/{asset_id}", request)


@router.delete("/tg/game/admin/media/{asset_id}")
async def delete_game_media(
    asset_id: int,
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin(f"/tg/game/admin/media/{asset_id}", request)


@router.get("/tg/game/admin/rating")
async def get_game_admin_rating(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/rating", request)


@router.get("/tg/game/admin/sessions")
async def get_game_admin_sessions(
    request: Request,
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    return await _forward_game_admin("/tg/game/admin/sessions", request)


@router.api_route("/tg/game/media/{filename}", methods=["GET", "HEAD"])
async def get_game_media_public(filename: str, request: Request) -> Response:
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(
        settings.TG_GAME_SERVICE_URL,
        f"/tg/game/media/{filename}",
    )
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
    )
