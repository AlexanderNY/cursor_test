"""Plan-change requests, promo codes, and invoice email."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from billing.plan_definitions import get_plan_by_code, normalize_tariff_code
from config import settings
from database import get_db_connection
from services.admin_audit_service import log_admin_audit
from services.auth_service import get_user_by_id, update_user_role_tariff
from services.email_service import send_plain_email, smtp_configured

PAID_PLANS = ("standard", "full")
OPEN_STATUSES = ("pending", "invoiced")


class BillingRequestError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_code(raw: Optional[str]) -> Optional[str]:
    code = (raw or "").strip().upper()
    return code or None


def format_money(amount: int, currency: str = "RUB") -> str:
    cur = (currency or "RUB").upper()
    formatted = f"{int(amount):,}".replace(",", " ")
    if cur == "RUB":
        return f"{formatted} ₽"
    return f"{formatted} {cur}"


def _as_naive(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    return None


def _row_request(row: tuple, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    data = {
        "id": row[0],
        "user_id": row[1],
        "current_tariff": row[2],
        "requested_tariff": row[3],
        "promo_code": row[4],
        "list_price": int(row[5] or 0),
        "discount_amount": int(row[6] or 0),
        "final_price": int(row[7] or 0),
        "currency": row[8] or "RUB",
        "status": row[9],
        "invoice_sent_at": row[10],
        "invoice_smtp_sent": bool(row[11]),
        "invoice_body": row[12],
        "admin_comment": row[13],
        "created_by_user_id": row[14],
        "processed_by_user_id": row[15],
        "created_at": row[16],
        "updated_at": row[17],
    }
    if extra:
        data.update(extra)
    return data


def _plan_price(tariff: str) -> tuple[int, str]:
    plan = get_plan_by_code(tariff) or {}
    return int(plan.get("price_monthly") or 0), str(plan.get("currency") or "RUB")


def compute_pricing(
    tariff: str, promo: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    list_price, currency = _plan_price(tariff)
    discount = 0
    if promo:
        if promo.get("discount_percent"):
            discount = min(list_price, round(list_price * int(promo["discount_percent"]) / 100))
        elif promo.get("discount_amount"):
            discount = min(list_price, int(promo["discount_amount"]))
    return {
        "list_price": list_price,
        "discount_amount": discount,
        "final_price": max(0, list_price - discount),
        "currency": currency,
    }


async def get_promo_by_code(code: str) -> Optional[dict[str, Any]]:
    normalized = _normalize_code(code)
    if not normalized:
        return None
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, code, description, discount_percent, discount_amount,
                       applies_to_tariff, max_redemptions, redeemed_count,
                       valid_from, valid_until, is_active
                FROM promo_codes
                WHERE code = %s
                """,
                (normalized,),
            )
            row = await cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "code": row[1],
        "description": row[2],
        "discount_percent": row[3],
        "discount_amount": row[4],
        "applies_to_tariff": row[5],
        "max_redemptions": row[6],
        "redeemed_count": int(row[7] or 0),
        "valid_from": row[8],
        "valid_until": row[9],
        "is_active": bool(row[10]),
    }


async def _promo_already_used(promo_id: int, user_id: int) -> bool:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM promo_code_redemptions
                WHERE promo_code_id = %s AND user_id = %s
                LIMIT 1
                """,
                (promo_id, user_id),
            )
            return await cur.fetchone() is not None


async def validate_promo_for_user(
    *, code: Optional[str], tariff: str, user_id: int
) -> Optional[dict[str, Any]]:
    normalized = _normalize_code(code)
    if not normalized:
        return None
    promo = await get_promo_by_code(normalized)
    if not promo or not promo["is_active"]:
        raise BillingRequestError("Промокод не найден или отключён")
    now = _now()
    valid_from = _as_naive(promo["valid_from"])
    valid_until = _as_naive(promo["valid_until"])
    if valid_from and valid_from > now:
        raise BillingRequestError("Промокод ещё не действует")
    if valid_until and valid_until < now:
        raise BillingRequestError("Срок действия промокода истёк")
    applies = (promo["applies_to_tariff"] or "").strip().lower()
    if applies and applies != tariff:
        raise BillingRequestError("Промокод не действует на этот тариф")
    if promo["max_redemptions"] is not None and promo["redeemed_count"] >= int(promo["max_redemptions"]):
        raise BillingRequestError("Промокод исчерпан")
    if await _promo_already_used(int(promo["id"]), user_id):
        raise BillingRequestError("Вы уже использовали этот промокод")
    return promo


def _build_invoice_body(request: dict[str, Any], user: dict[str, Any]) -> str:
    plan = get_plan_by_code(request["requested_tariff"]) or {}
    seller = (settings.BILLING_INVOICE_SELLER or "CopyParse").strip()
    instructions = (settings.BILLING_PAYMENT_INSTRUCTIONS or "").strip()
    lines = [
        f"Счёт на оплату — {seller}",
        "",
        f"Получатель: {user.get('username')} <{user.get('email')}>",
        f"Заявка №{request['id']}",
        f"Тариф: {plan.get('display_name') or request['requested_tariff']}",
        f"Период: 1 месяц",
        f"Сумма: {format_money(request['list_price'], request['currency'])}",
    ]
    if int(request["discount_amount"] or 0) > 0:
        promo = request.get("promo_code") or ""
        lines.append(
            f"Скидка{f' ({promo})' if promo else ''}: −{format_money(request['discount_amount'], request['currency'])}"
        )
    lines.append(f"К оплате: {format_money(request['final_price'], request['currency'])}")
    if instructions:
        lines.extend(["", "Реквизиты / способ оплаты:", instructions])
    else:
        lines.extend(
            [
                "",
                "Оплата по счёту. После поступления платежа тариф будет включён вручную.",
            ]
        )
    frontend = (settings.FRONTEND_URL or "").rstrip("/")
    if frontend:
        lines.extend(["", f"Кабинет: {frontend}/profile?tab=billing"])
    return "\n".join(lines)


async def preview_promo(code: str, plan: str, user_id: int) -> dict[str, Any]:
    tariff = normalize_tariff_code(plan)
    if tariff not in PAID_PLANS:
        raise BillingRequestError("Промокод применяется к Standard или Full")
    promo = await validate_promo_for_user(code=code, tariff=tariff, user_id=user_id)
    pricing = compute_pricing(tariff, promo)
    return {
        "code": promo["code"] if promo else None,
        "discount_percent": promo.get("discount_percent") if promo else None,
        "discount_amount": pricing["discount_amount"],
        "list_price": pricing["list_price"],
        "final_price": pricing["final_price"],
        "currency": pricing["currency"],
        "description": promo.get("description") if promo else None,
    }


async def create_or_update_request(
    *,
    user_id: int,
    requested_tariff: str,
    promo_code: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    allow_free: bool = False,
) -> dict[str, Any]:
    tariff = normalize_tariff_code(requested_tariff)
    allowed = PAID_PLANS + (("free",) if allow_free else ())
    if tariff not in allowed:
        raise BillingRequestError("Можно запросить только Standard или Full")
    user = await get_user_by_id(user_id)
    if not user:
        raise BillingRequestError("Пользователь не найден", 404)
    current = normalize_tariff_code(user.get("tariff"))
    if current == tariff:
        raise BillingRequestError("Этот тариф уже активен")
    promo = await validate_promo_for_user(code=promo_code, tariff=tariff, user_id=user_id)
    pricing = compute_pricing(tariff, promo)
    promo_value = promo["code"] if promo else None

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM billing_plan_requests
                WHERE user_id = %s AND status IN ('pending', 'invoiced')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            existing = await cur.fetchone()
            if existing:
                await cur.execute(
                    """
                    UPDATE billing_plan_requests SET
                        current_tariff = %s,
                        requested_tariff = %s,
                        promo_code = %s,
                        list_price = %s,
                        discount_amount = %s,
                        final_price = %s,
                        currency = %s,
                        status = 'pending',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, user_id, current_tariff, requested_tariff, promo_code,
                              list_price, discount_amount, final_price, currency, status,
                              invoice_sent_at, invoice_smtp_sent, invoice_body, admin_comment,
                              created_by_user_id, processed_by_user_id, created_at, updated_at
                    """,
                    (
                        current,
                        tariff,
                        promo_value,
                        pricing["list_price"],
                        pricing["discount_amount"],
                        pricing["final_price"],
                        pricing["currency"],
                        int(existing[0]),
                    ),
                )
            else:
                await cur.execute(
                    """
                    INSERT INTO billing_plan_requests (
                        user_id, current_tariff, requested_tariff, promo_code,
                        list_price, discount_amount, final_price, currency,
                        created_by_user_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, current_tariff, requested_tariff, promo_code,
                              list_price, discount_amount, final_price, currency, status,
                              invoice_sent_at, invoice_smtp_sent, invoice_body, admin_comment,
                              created_by_user_id, processed_by_user_id, created_at, updated_at
                    """,
                    (
                        user_id,
                        current,
                        tariff,
                        promo_value,
                        pricing["list_price"],
                        pricing["discount_amount"],
                        pricing["final_price"],
                        pricing["currency"],
                        created_by_user_id or user_id,
                    ),
                )
            row = await cur.fetchone()
    result = _row_request(row, extra={"username": user.get("username"), "email": user.get("email")})
    if created_by_user_id:
        await log_admin_audit(
            created_by_user_id,
            "billing_request_created",
            target_type="billing_plan_request",
            target_id=str(result["id"]),
            details={"user_id": user_id, "requested_tariff": tariff, "promo_code": promo_value},
        )
    return result


async def list_my_requests(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    lim = max(1, min(limit, 100))
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, current_tariff, requested_tariff, promo_code,
                       list_price, discount_amount, final_price, currency, status,
                       invoice_sent_at, invoice_smtp_sent, invoice_body, admin_comment,
                       created_by_user_id, processed_by_user_id, created_at, updated_at
                FROM billing_plan_requests
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, lim),
            )
            rows = await cur.fetchall()
    return [_row_request(r) for r in rows]


async def get_open_request(user_id: int) -> Optional[dict[str, Any]]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, current_tariff, requested_tariff, promo_code,
                       list_price, discount_amount, final_price, currency, status,
                       invoice_sent_at, invoice_smtp_sent, invoice_body, admin_comment,
                       created_by_user_id, processed_by_user_id, created_at, updated_at
                FROM billing_plan_requests
                WHERE user_id = %s AND status IN ('pending', 'invoiced')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = await cur.fetchone()
    return _row_request(row) if row else None


async def list_admin_requests(
    status: Optional[str] = None, limit: int = 100
) -> list[dict[str, Any]]:
    lim = max(1, min(limit, 300))
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            if status:
                await cur.execute(
                    """
                    SELECT r.id, r.user_id, r.current_tariff, r.requested_tariff, r.promo_code,
                           r.list_price, r.discount_amount, r.final_price, r.currency, r.status,
                           r.invoice_sent_at, r.invoice_smtp_sent, r.invoice_body, r.admin_comment,
                           r.created_by_user_id, r.processed_by_user_id, r.created_at, r.updated_at,
                           u.username, u.email
                    FROM billing_plan_requests r
                    JOIN users u ON u.id = r.user_id
                    WHERE r.status = %s
                    ORDER BY r.created_at DESC
                    LIMIT %s
                    """,
                    (status, lim),
                )
            else:
                await cur.execute(
                    """
                    SELECT r.id, r.user_id, r.current_tariff, r.requested_tariff, r.promo_code,
                           r.list_price, r.discount_amount, r.final_price, r.currency, r.status,
                           r.invoice_sent_at, r.invoice_smtp_sent, r.invoice_body, r.admin_comment,
                           r.created_by_user_id, r.processed_by_user_id, r.created_at, r.updated_at,
                           u.username, u.email
                    FROM billing_plan_requests r
                    JOIN users u ON u.id = r.user_id
                    ORDER BY
                        CASE r.status
                            WHEN 'pending' THEN 0
                            WHEN 'invoiced' THEN 1
                            ELSE 2
                        END,
                        r.created_at DESC
                    LIMIT %s
                    """,
                    (lim,),
                )
            rows = await cur.fetchall()
    return [_row_request(r[:18], extra={"username": r[18], "email": r[19]}) for r in rows]


async def _get_request(request_id: int) -> dict[str, Any]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT r.id, r.user_id, r.current_tariff, r.requested_tariff, r.promo_code,
                       r.list_price, r.discount_amount, r.final_price, r.currency, r.status,
                       r.invoice_sent_at, r.invoice_smtp_sent, r.invoice_body, r.admin_comment,
                       r.created_by_user_id, r.processed_by_user_id, r.created_at, r.updated_at,
                       u.username, u.email
                FROM billing_plan_requests r
                JOIN users u ON u.id = r.user_id
                WHERE r.id = %s
                """,
                (request_id,),
            )
            row = await cur.fetchone()
    if not row:
        raise BillingRequestError("Заявка не найдена", 404)
    return _row_request(row[:18], extra={"username": row[18], "email": row[19]})


async def send_invoice(request_id: int, admin_user_id: int, payment_note: Optional[str] = None) -> dict[str, Any]:
    req = await _get_request(request_id)
    if req["status"] not in OPEN_STATUSES:
        raise BillingRequestError("Счёт можно отправить только по открытой заявке")
    user = {"username": req["username"], "email": req["email"]}
    body = _build_invoice_body(req, user)
    if payment_note and payment_note.strip():
        body = f"{body}\n\nКомментарий:\n{payment_note.strip()}"
    smtp_sent = False
    if smtp_configured():
        smtp_sent = await send_plain_email(
            to_email=str(req["email"]),
            subject=f"Счёт на тариф {req['requested_tariff']} — CopyParse",
            body=body,
        )
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE billing_plan_requests SET
                    status = 'invoiced',
                    invoice_sent_at = CURRENT_TIMESTAMP,
                    invoice_smtp_sent = %s,
                    invoice_body = %s,
                    admin_comment = COALESCE(%s, admin_comment),
                    processed_by_user_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (smtp_sent, body, payment_note.strip() if payment_note else None, admin_user_id, request_id),
            )
    await log_admin_audit(
        admin_user_id,
        "billing_invoice_sent",
        target_type="billing_plan_request",
        target_id=str(request_id),
        details={"smtp_sent": smtp_sent, "email": req["email"]},
    )
    updated = await _get_request(request_id)
    updated["smtp_configured"] = smtp_configured()
    return updated


async def apply_request(request_id: int, admin_user_id: int) -> dict[str, Any]:
    req = await _get_request(request_id)
    if req["status"] not in OPEN_STATUSES:
        raise BillingRequestError("Заявку уже закрыли")
    await update_user_role_tariff(
        user_id=int(req["user_id"]),
        tariff=req["requested_tariff"],
        changed_by_user_id=admin_user_id,
    )
    promo = await get_promo_by_code(req["promo_code"] or "")
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            if promo:
                await cur.execute(
                    """
                    INSERT INTO promo_code_redemptions (promo_code_id, user_id, request_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (promo_code_id, user_id) DO NOTHING
                    RETURNING id
                    """,
                    (promo["id"], req["user_id"], request_id),
                )
                redeemed = await cur.fetchone()
                if redeemed:
                    await cur.execute(
                        """
                        UPDATE promo_codes
                        SET redeemed_count = redeemed_count + 1
                        WHERE id = %s
                        """,
                        (promo["id"],),
                    )
            await cur.execute(
                """
                UPDATE billing_plan_requests SET
                    status = 'applied',
                    processed_by_user_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (admin_user_id, request_id),
            )
    await log_admin_audit(
        admin_user_id,
        "billing_request_applied",
        target_type="billing_plan_request",
        target_id=str(request_id),
        details={"user_id": req["user_id"], "tariff": req["requested_tariff"]},
    )
    return await _get_request(request_id)


async def reject_request(
    request_id: int, admin_user_id: int, comment: Optional[str] = None
) -> dict[str, Any]:
    req = await _get_request(request_id)
    if req["status"] not in OPEN_STATUSES:
        raise BillingRequestError("Заявку уже закрыли")
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE billing_plan_requests SET
                    status = 'rejected',
                    admin_comment = COALESCE(%s, admin_comment),
                    processed_by_user_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (comment.strip() if comment else None, admin_user_id, request_id),
            )
    await log_admin_audit(
        admin_user_id,
        "billing_request_rejected",
        target_type="billing_plan_request",
        target_id=str(request_id),
        details={"comment": comment},
    )
    return await _get_request(request_id)


def _row_promo(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "code": row[1],
        "description": row[2],
        "discount_percent": row[3],
        "discount_amount": row[4],
        "applies_to_tariff": row[5],
        "max_redemptions": row[6],
        "redeemed_count": int(row[7] or 0),
        "valid_from": row[8],
        "valid_until": row[9],
        "is_active": bool(row[10]),
        "created_at": row[11],
    }


async def list_promo_codes() -> list[dict[str, Any]]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, code, description, discount_percent, discount_amount,
                       applies_to_tariff, max_redemptions, redeemed_count,
                       valid_from, valid_until, is_active, created_at
                FROM promo_codes
                ORDER BY created_at DESC
                """
            )
            rows = await cur.fetchall()
    return [_row_promo(r) for r in rows]


async def create_promo_code(payload: dict[str, Any], admin_user_id: int) -> dict[str, Any]:
    code = _normalize_code(payload.get("code"))
    if not code or len(code) < 3:
        raise BillingRequestError("Код должен быть не короче 3 символов")
    percent = payload.get("discount_percent")
    amount = payload.get("discount_amount")
    if bool(percent) == bool(amount):
        raise BillingRequestError("Укажите либо процент, либо фиксированную скидку")
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    """
                    INSERT INTO promo_codes (
                        code, description, discount_percent, discount_amount,
                        applies_to_tariff, max_redemptions, valid_from, valid_until,
                        is_active, created_by_user_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, code, description, discount_percent, discount_amount,
                              applies_to_tariff, max_redemptions, redeemed_count,
                              valid_from, valid_until, is_active, created_at
                    """,
                    (
                        code,
                        payload.get("description"),
                        int(percent) if percent else None,
                        int(amount) if amount else None,
                        (payload.get("applies_to_tariff") or None),
                        int(payload["max_redemptions"]) if payload.get("max_redemptions") else None,
                        payload.get("valid_from"),
                        payload.get("valid_until"),
                        bool(payload.get("is_active", True)),
                        admin_user_id,
                    ),
                )
            except Exception as exc:
                raise BillingRequestError("Такой промокод уже есть") from exc
            row = await cur.fetchone()
    await log_admin_audit(
        admin_user_id,
        "promo_code_created",
        target_type="promo_code",
        target_id=code,
        details={"percent": percent, "amount": amount},
    )
    return _row_promo(row)


async def update_promo_code(promo_id: int, payload: dict[str, Any], admin_user_id: int) -> dict[str, Any]:
    fields = []
    params: list[Any] = []
    mapping = {
        "description": "description",
        "discount_percent": "discount_percent",
        "discount_amount": "discount_amount",
        "applies_to_tariff": "applies_to_tariff",
        "max_redemptions": "max_redemptions",
        "valid_from": "valid_from",
        "valid_until": "valid_until",
        "is_active": "is_active",
    }
    for key, column in mapping.items():
        if key in payload:
            fields.append(f"{column} = %s")
            params.append(payload[key])
    if "code" in payload and payload["code"]:
        fields.append("code = %s")
        params.append(_normalize_code(payload["code"]))
    if not fields:
        raise BillingRequestError("Нечего обновлять")
    params.append(promo_id)
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE promo_codes SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id, code, description, discount_percent, discount_amount,
                          applies_to_tariff, max_redemptions, redeemed_count,
                          valid_from, valid_until, is_active, created_at
                """,
                params,
            )
            row = await cur.fetchone()
    if not row:
        raise BillingRequestError("Промокод не найден", 404)
    await log_admin_audit(
        admin_user_id,
        "promo_code_updated",
        target_type="promo_code",
        target_id=str(promo_id),
        details=payload,
    )
    return _row_promo(row)
