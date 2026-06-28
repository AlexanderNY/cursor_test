"""Админ API заказов из режима menu."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from deps_game_admin import verify_game_admin_token
from schemas_game import GameMenuOrderItemOut, GameMenuOrderOut
from services.order_repository import order_repository

router = APIRouter(prefix="/admin", tags=["Game Orders Admin"])


@router.get(
    "/orders",
    response_model=list[GameMenuOrderOut],
    dependencies=[Depends(verify_game_admin_token)],
)
async def list_orders(
    mode_id: Optional[int] = None,
    bot_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[GameMenuOrderOut]:
    rows = await order_repository.admin_list_orders(
        mode_id=mode_id,
        bot_id=bot_id,
        limit=limit,
    )
    return [
        GameMenuOrderOut(
            **{k: v for k, v in r.items() if k != "items"},
            items=[],
        )
        for r in rows
    ]


@router.get(
    "/orders/{order_id}",
    response_model=GameMenuOrderOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def get_order(order_id: int) -> GameMenuOrderOut:
    row = await order_repository.admin_get_order(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    items = [GameMenuOrderItemOut(**i) for i in row.pop("items", [])]
    total_qty = sum(i.quantity for i in items)
    return GameMenuOrderOut(**row, total_quantity=total_qty, items=items)
