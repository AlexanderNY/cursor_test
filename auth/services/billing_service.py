"""Обработка Stripe webhooks и синхронизация подписки с users."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import stripe
from stripe.error import SignatureVerificationError

from config import settings
from database import get_db_connection

logger = logging.getLogger(__name__)

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


def _tariff_from_price_id(price_id: Optional[str]) -> Optional[str]:
    if not price_id:
        return None
    if settings.STRIPE_PRICE_BASIC and price_id == settings.STRIPE_PRICE_BASIC:
        return "basic"
    if settings.STRIPE_PRICE_PREMIUM and price_id == settings.STRIPE_PRICE_PREMIUM:
        return "premium"
    return None


async def _insert_billing_event(
    provider: str,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
    user_id: Optional[int],
) -> bool:
    """Возвращает True если событие новое и вставлено, False если дубликат."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO billing_events (provider, event_id, event_type, payload_json, user_id)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (provider, event_id) DO NOTHING
                RETURNING id
                """,
                (
                    provider,
                    event_id,
                    event_type,
                    json.dumps(payload),
                    user_id,
                ),
            )
            row = await cur.fetchone()
    return row is not None


async def _update_user_subscription_fields(
    user_id: int,
    *,
    billing_customer_id: Optional[str] = None,
    billing_subscription_id: Optional[str] = None,
    subscription_status: Optional[str] = None,
    subscription_current_period_end: Optional[datetime] = None,
    tariff: Optional[str] = None,
) -> None:
    sets: list[str] = []
    params: list[Any] = []
    if billing_customer_id is not None:
        sets.append("billing_customer_id = %s")
        params.append(billing_customer_id)
    if billing_subscription_id is not None:
        sets.append("billing_subscription_id = %s")
        params.append(billing_subscription_id)
    if subscription_status is not None:
        sets.append("subscription_status = %s")
        params.append(subscription_status)
    if subscription_current_period_end is not None:
        sets.append("subscription_current_period_end = %s")
        params.append(subscription_current_period_end)
    if tariff is not None:
        sets.append("tariff = %s")
        params.append(tariff)
    if not sets:
        return
    sets.append("billing_provider = %s")
    params.append("stripe")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            q = f"UPDATE users SET {', '.join(sets)} WHERE id = %s"
            await cur.execute(q, params)


async def _find_user_id_by_customer_id(customer_id: str) -> Optional[int]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM users WHERE billing_customer_id = %s LIMIT 1",
                (customer_id,),
            )
            row = await cur.fetchone()
            return int(row[0]) if row else None


def _parse_period_end(sub: dict[str, Any]) -> Optional[datetime]:
    ts = sub.get("current_period_end")
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return None


def _status_and_tariff_from_subscription(sub: dict[str, Any]) -> tuple[str, Optional[str]]:
    status = str(sub.get("status") or "unknown")
    tariff: Optional[str] = None
    items = sub.get("items") or {}
    data = items.get("data") or []
    if data:
        price = (data[0] or {}).get("price") or {}
        pid = price.get("id")
        tariff = _tariff_from_price_id(pid if isinstance(pid, str) else None)
    return status, tariff


async def process_stripe_webhook_payload(payload: bytes, stripe_signature: Optional[str]) -> dict[str, Any]:
    """Проверяет подпись Stripe, идемпотентно сохраняет событие, обновляет users."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("STRIPE_WEBHOOK_SECRET is not set; webhook rejected")
        return {"ok": False, "error": "webhook_not_configured"}

    if not stripe_signature:
        return {"ok": False, "error": "missing_stripe_signature"}

    try:
        stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.warning("Invalid webhook payload: %s", e)
        return {"ok": False, "error": "invalid_payload"}
    except SignatureVerificationError as e:
        logger.warning("Invalid webhook signature: %s", e)
        return {"ok": False, "error": "invalid_signature"}

    try:
        event_dict = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning("Webhook JSON decode failed: %s", e)
        return {"ok": False, "error": "invalid_payload"}

    event_id = str(event_dict.get("id") or "")
    event_type = str(event_dict.get("type") or "unknown")
    data_obj = (event_dict.get("data") or {}).get("object") or {}

    user_id: Optional[int] = None
    if event_type.startswith("checkout.session"):
        meta = data_obj.get("metadata") or {}
        uid = meta.get("user_id")
        if uid is not None and str(uid).isdigit():
            user_id = int(uid)

    if not event_id:
        return {"ok": False, "error": "missing_event_id"}

    if not await _insert_billing_event(
        "stripe", event_id, event_type, event_dict, user_id
    ):
        return {"ok": True, "duplicate": True}

    # Обработка бизнес-логики (после идемпотентной вставки)
    if event_type == "checkout.session.completed":
        meta = data_obj.get("metadata") or {}
        uid_raw = meta.get("user_id")
        if uid_raw is not None and str(uid_raw).isdigit():
            uid = int(uid_raw)
            customer = data_obj.get("customer")
            subscription = data_obj.get("subscription")
            meta_tariff = meta.get("tariff")
            t = None
            if isinstance(meta_tariff, str) and meta_tariff.lower() in ("free", "basic", "premium"):
                t = meta_tariff.lower()
            await _update_user_subscription_fields(
                uid,
                billing_customer_id=customer if isinstance(customer, str) else None,
                billing_subscription_id=subscription if isinstance(subscription, str) else None,
                subscription_status="active",
                tariff=t,
            )

    elif event_type in (
        "customer.subscription.updated",
        "customer.subscription.created",
    ):
        customer_id = data_obj.get("customer")
        if not isinstance(customer_id, str):
            return {"ok": True, "ignored": True}
        uid = await _find_user_id_by_customer_id(customer_id)
        if uid is None:
            meta = data_obj.get("metadata") or {}
            u = meta.get("user_id")
            if u is not None and str(u).isdigit():
                uid = int(u)
        if uid is None:
            logger.info("subscription event: no user for customer %s", customer_id)
            return {"ok": True, "no_user": True}

        status_s, tariff = _status_and_tariff_from_subscription(data_obj)
        period_end = _parse_period_end(data_obj)
        sub_id = data_obj.get("id")
        await _update_user_subscription_fields(
            uid,
            billing_customer_id=customer_id,
            billing_subscription_id=sub_id if isinstance(sub_id, str) else None,
            subscription_status=status_s,
            subscription_current_period_end=period_end,
            tariff=tariff,
        )

    elif event_type == "customer.subscription.deleted":
        customer_id = data_obj.get("customer")
        if not isinstance(customer_id, str):
            return {"ok": True, "ignored": True}
        uid = await _find_user_id_by_customer_id(customer_id)
        if uid is None:
            return {"ok": True, "no_user": True}
        await _update_user_subscription_fields(
            uid,
            subscription_status="canceled",
            tariff="free",
        )

    return {"ok": True, "event_type": event_type}
