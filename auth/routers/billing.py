"""Публичные и пользовательские эндпоинты биллинга."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

import stripe

from billing.plan_definitions import PLAN_DEFINITIONS, get_plan_by_code
from config import settings
from database import get_db_connection
from dependencies import get_admin_user, get_current_user
from schemas import (
    CheckoutSessionRequest,
    PlanRequestCreate,
    PlanRequestInvoiceBody,
    PlanRequestRejectBody,
    PromoCodeCreate,
    PromoCodeUpdate,
)
from services.billing_service import create_checkout_session, process_stripe_webhook_payload
from services import billing_requests_service as plan_requests
from services.billing_requests_service import BillingRequestError

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
    pending = await plan_requests.get_open_request(int(current_user["id"]))
    return {
        "tariff": tariff,
        "plan": plan,
        "pending_request": pending,
        "billing_provider": current_user.get("billing_provider"),
        "billing_customer_id": current_user.get("billing_customer_id"),
        "billing_subscription_id": current_user.get("billing_subscription_id"),
        "subscription_status": current_user.get("subscription_status"),
        "subscription_current_period_end": current_user.get("subscription_current_period_end"),
        "stripe_portal_available": bool(settings.STRIPE_SECRET_KEY and current_user.get("billing_customer_id")),
        "stripe_checkout_available": bool(
            settings.STRIPE_SECRET_KEY
            and (
                (settings.STRIPE_PRICE_STANDARD or settings.STRIPE_PRICE_BASIC)
                or (settings.STRIPE_PRICE_FULL or settings.STRIPE_PRICE_PREMIUM)
            )
        ),
    }


@router.post("/billing/checkout-session")
async def create_billing_checkout_session(
    body: CheckoutSessionRequest,
    current_user: Dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Self-serve Stripe Checkout → URL для Standard/Full."""
    try:
        return await create_checkout_session(
            user_id=int(current_user["id"]),
            email=str(current_user.get("email") or ""),
            plan=body.plan,
            billing_customer_id=current_user.get("billing_customer_id"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {exc.user_message or str(exc)}",
        ) from exc


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


def _http_from_billing(exc: BillingRequestError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/billing/requests")
async def create_my_plan_request(
    body: PlanRequestCreate,
    current_user: Dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Пользователь запрашивает смену тарифа (заявка в админку)."""
    if body.plan not in ("standard", "full"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Можно запросить только Standard или Full",
        )
    try:
        return await plan_requests.create_or_update_request(
            user_id=int(current_user["id"]),
            requested_tariff=body.plan,
            promo_code=body.promo_code,
            created_by_user_id=int(current_user["id"]),
        )
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.get("/billing/requests")
async def list_my_plan_requests(
    current_user: Dict = Depends(get_current_user),
) -> dict[str, Any]:
    items = await plan_requests.list_my_requests(int(current_user["id"]))
    return {"requests": items}


@router.get("/billing/promo/preview")
async def preview_promo_code(
    code: str,
    plan: str,
    current_user: Dict = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return await plan_requests.preview_promo(code, plan, int(current_user["id"]))
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.get("/billing/admin/requests")
async def admin_list_plan_requests(
    admin_user: Dict = Depends(get_admin_user),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> dict[str, Any]:
    _ = admin_user
    items = await plan_requests.list_admin_requests(status=status_filter)
    return {"requests": items}


@router.post("/billing/admin/requests")
async def admin_create_plan_request(
    body: PlanRequestCreate,
    admin_user: Dict = Depends(get_admin_user),
) -> dict[str, Any]:
    if not body.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        return await plan_requests.create_or_update_request(
            user_id=int(body.user_id),
            requested_tariff=body.plan,
            promo_code=body.promo_code,
            created_by_user_id=int(admin_user["id"]),
            allow_free=True,
        )
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.post("/billing/admin/requests/{request_id}/invoice")
async def admin_send_invoice(
    request_id: int,
    admin_user: Dict = Depends(get_admin_user),
    body: Optional[PlanRequestInvoiceBody] = None,
) -> dict[str, Any]:
    try:
        return await plan_requests.send_invoice(
            request_id,
            int(admin_user["id"]),
            payment_note=body.payment_note if body else None,
        )
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.post("/billing/admin/requests/{request_id}/apply")
async def admin_apply_plan_request(
    request_id: int,
    admin_user: Dict = Depends(get_admin_user),
) -> dict[str, Any]:
    try:
        return await plan_requests.apply_request(request_id, int(admin_user["id"]))
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.post("/billing/admin/requests/{request_id}/reject")
async def admin_reject_plan_request(
    request_id: int,
    admin_user: Dict = Depends(get_admin_user),
    body: Optional[PlanRequestRejectBody] = None,
) -> dict[str, Any]:
    try:
        return await plan_requests.reject_request(
            request_id,
            int(admin_user["id"]),
            comment=body.comment if body else None,
        )
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.get("/billing/admin/promo-codes")
async def admin_list_promo_codes(admin_user: Dict = Depends(get_admin_user)) -> dict[str, Any]:
    _ = admin_user
    return {"promo_codes": await plan_requests.list_promo_codes()}


@router.post("/billing/admin/promo-codes")
async def admin_create_promo_code(
    body: PromoCodeCreate,
    admin_user: Dict = Depends(get_admin_user),
) -> dict[str, Any]:
    try:
        return await plan_requests.create_promo_code(body.model_dump(), int(admin_user["id"]))
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc


@router.patch("/billing/admin/promo-codes/{promo_id}")
async def admin_update_promo_code(
    promo_id: int,
    body: PromoCodeUpdate,
    admin_user: Dict = Depends(get_admin_user),
) -> dict[str, Any]:
    try:
        return await plan_requests.update_promo_code(
            promo_id,
            body.model_dump(exclude_unset=True),
            int(admin_user["id"]),
        )
    except BillingRequestError as exc:
        raise _http_from_billing(exc) from exc
