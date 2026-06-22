"""Публичные и пользовательские эндпоинты биллинга."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

import stripe

from billing.plan_definitions import PLAN_DEFINITIONS, get_plan_by_code
from config import settings
from database import get_db_connection
from dependencies import get_current_user
from services.billing_service import process_stripe_webhook_payload

router = APIRouter(tags=["billing"])


@router.get("/billing/plans")
async def list_plans() -> dict[str, Any]:
    """Продуктовая матрица тарифов (без авторизации)."""
    return {"plans": PLAN_DEFINITIONS}


@router.get("/billing/me")
async def billing_me(current_user: Dict = Depends(get_current_user)) -> dict[str, Any]:
    """Текущий тариф, лимиты плана и поля подписки."""
    tariff = current_user.get("tariff") or "free"
    plan = get_plan_by_code(tariff)
    return {
        "tariff": tariff,
        "plan": plan,
        "billing_provider": current_user.get("billing_provider"),
        "billing_customer_id": current_user.get("billing_customer_id"),
        "billing_subscription_id": current_user.get("billing_subscription_id"),
        "subscription_status": current_user.get("subscription_status"),
        "subscription_current_period_end": current_user.get("subscription_current_period_end"),
        "stripe_portal_available": bool(settings.STRIPE_SECRET_KEY and current_user.get("billing_customer_id")),
    }


@router.post("/billing/customer-portal")
async def create_customer_portal_session(current_user: Dict = Depends(get_current_user)) -> dict[str, Any]:
    """Stripe Customer Portal (управление подпиской). Требует STRIPE_SECRET_KEY и billing_customer_id."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )
    cid = current_user.get("billing_customer_id")
    if not cid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer linked to this account",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.billing_portal.Session.create(
        customer=cid,
        return_url=settings.BILLING_PORTAL_RETURN_URL,
    )
    return {"url": session.url}


@router.get("/billing/events", response_model=List[dict[str, Any]])
async def list_my_billing_events(
    current_user: Dict = Depends(get_current_user),
    limit: int = 50,
) -> List[dict[str, Any]]:
    """Read-only история событий биллинга для текущего пользователя."""
    uid = int(current_user["id"])
    lim = max(1, min(limit, 200))
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, provider, event_type, created_at
                FROM billing_events
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (uid, lim),
            )
            rows = await cur.fetchall()
    return [
        {
            "id": r[0],
            "provider": r[1],
            "event_type": r[2],
            "created_at": r[3],
        }
        for r in rows
    ]


@router.post("/billing/webhooks/stripe")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Stripe webhook (сырое тело, подпись Stripe-Signature)."""
    body = await request.body()
    sig = request.headers.get("stripe-signature")
    result = await process_stripe_webhook_payload(body, sig)
    if not result.get("ok"):
        return JSONResponse(result, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(result)
