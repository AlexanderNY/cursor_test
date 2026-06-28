"""Админ CRUD для узлов иерархического меню."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from deps_game_admin import verify_game_admin_token
from schemas_game import GameMenuNodeCreate, GameMenuNodeOut, GameMenuNodeUpdate
from services.game_repository import game_repository
from services.menu_repository import menu_repository

router = APIRouter(prefix="/admin", tags=["Game Menu Admin"])


@router.get(
    "/modes/{mode_id}/menu-nodes",
    response_model=list[GameMenuNodeOut],
    dependencies=[Depends(verify_game_admin_token)],
)
async def list_menu_nodes(mode_id: int) -> list[GameMenuNodeOut]:
    mode = await game_repository.get_mode(mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    if mode.mode_type != "menu":
        raise HTTPException(status_code=400, detail="Mode is not a menu type")
    rows = await menu_repository.admin_list_nodes(mode_id)
    return [GameMenuNodeOut(**r) for r in rows]


@router.post(
    "/menu-nodes",
    response_model=GameMenuNodeOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def create_menu_node(body: GameMenuNodeCreate) -> GameMenuNodeOut:
    mode = await game_repository.get_mode(body.mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    if mode.mode_type != "menu":
        raise HTTPException(status_code=400, detail="Mode is not a menu type")
    if body.parent_id is not None:
        parent = await menu_repository.get_node(body.parent_id)
        if not parent or parent.mode_id != body.mode_id:
            raise HTTPException(status_code=400, detail="Invalid parent_id")
    node_id = await menu_repository.admin_create_node(
        mode_id=body.mode_id,
        parent_id=body.parent_id,
        title=body.title.strip(),
        body_text=body.body_text,
        image_url=body.image_url,
        sort_order=body.sort_order,
        is_active=body.is_active,
        price=body.price,
    )
    node = await menu_repository.get_node(node_id)
    if not node:
        raise HTTPException(status_code=500, detail="Node not found after create")
    rows = await menu_repository.admin_list_nodes(body.mode_id)
    found = next((r for r in rows if r["id"] == node_id), None)
    if not found:
        raise HTTPException(status_code=500, detail="Node not found after create")
    return GameMenuNodeOut(**found)


@router.patch(
    "/menu-nodes/{node_id}",
    response_model=GameMenuNodeOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def update_menu_node(node_id: int, body: GameMenuNodeUpdate) -> GameMenuNodeOut:
    node = await menu_repository.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if body.parent_id is not None:
        if body.parent_id == node_id:
            raise HTTPException(status_code=400, detail="Node cannot be its own parent")
        parent = await menu_repository.get_node(body.parent_id)
        if not parent or parent.mode_id != node.mode_id:
            raise HTTPException(status_code=400, detail="Invalid parent_id")
    await menu_repository.admin_update_node(
        node_id,
        parent_id=body.parent_id,
        parent_id_set="parent_id" in body.model_fields_set,
        title=body.title.strip() if body.title is not None else None,
        body_text=body.body_text,
        image_url=body.image_url,
        image_url_set="image_url" in body.model_fields_set,
        sort_order=body.sort_order,
        is_active=body.is_active,
        price=body.price,
    )
    rows = await menu_repository.admin_list_nodes(node.mode_id)
    found = next((r for r in rows if r["id"] == node_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Node not found")
    return GameMenuNodeOut(**found)


@router.delete(
    "/menu-nodes/{node_id}",
    dependencies=[Depends(verify_game_admin_token)],
)
async def delete_menu_node(node_id: int) -> dict[str, str]:
    node = await menu_repository.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    deleted = await menu_repository.admin_delete_node(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "ok"}
