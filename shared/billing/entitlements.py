"""Правила повышенного тарифа: ранг, окно 30 дней, выбор действующего гранта.

Грант создаёт ручная отметка об оплате или промокод бесплатного доступа.
Групповой инвайт тариф не меняет. Пользователи без строк грантов
(старый тариф или будущий провайдер оплаты) этим модулем не понижаются.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from shared.billing.plan_definitions import normalize_tariff_code

PAID_GRANT_DAYS = 30
PAID_TARIFFS = ("standard", "full")
PROMO_KIND_DISCOUNT = "discount"
PROMO_KIND_GRANT = "grant"

_TARIFF_RANK = {"free": 0, "standard": 1, "full": 2}


def tariff_rank(code: Optional[str]) -> int:
    return _TARIFF_RANK.get(normalize_tariff_code(code), 0)


def allows_paid_mark(current: Optional[str], requested: Optional[str]) -> bool:
    """Ручная отметка: тот же платный тариф (продление) или более высокий."""
    requested_code = normalize_tariff_code(requested)
    if requested_code not in PAID_TARIFFS:
        return False
    return tariff_rank(requested_code) >= tariff_rank(current)


def grant_expires_at(marked_at: datetime, days: int = PAID_GRANT_DAYS) -> datetime:
    if days < 1:
        raise ValueError("Срок гранта должен быть не меньше 1 дня")
    return marked_at + timedelta(days=days)


def pick_effective_grant(grants: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Старший активный тариф. При равенстве — тот, что заканчивается позже."""
    active = [grant for grant in grants if grant.get("status", "active") == "active"]
    if not active:
        return None
    return max(
        active,
        key=lambda grant: (tariff_rank(str(grant.get("tariff") or "")), grant.get("expires_at")),
    )


def resolve_effective_tariff(grants: list[dict[str, Any]]) -> tuple[str, Optional[datetime]]:
    winner = pick_effective_grant(grants)
    if not winner:
        return "free", None
    expires_at = winner.get("expires_at")
    if expires_at is not None and not isinstance(expires_at, datetime):
        expires_at = None
    return normalize_tariff_code(str(winner.get("tariff") or "free")), expires_at


def normalize_promo_kind_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Поля промокода: скидка на счёт или бесплатный доступ к тарифу."""
    kind = str(payload.get("kind") or PROMO_KIND_DISCOUNT).strip().lower()
    if kind not in (PROMO_KIND_DISCOUNT, PROMO_KIND_GRANT):
        raise ValueError("Тип промокода: discount или grant")
    if kind == PROMO_KIND_GRANT:
        tariff = normalize_tariff_code(payload.get("applies_to_tariff"))
        if tariff not in PAID_TARIFFS:
            raise ValueError("Для бесплатного доступа укажите тариф standard или full")
        raw_days = payload.get("grant_days")
        days = PAID_GRANT_DAYS if raw_days in (None, "") else int(raw_days)
        if days < 1 or days > 366:
            raise ValueError("Срок бесплатного доступа — от 1 до 366 дней")
        return {
            "kind": PROMO_KIND_GRANT,
            "discount_percent": None,
            "discount_amount": None,
            "applies_to_tariff": tariff,
            "grant_days": days,
        }
    percent = payload.get("discount_percent")
    amount = payload.get("discount_amount")
    if bool(percent) == bool(amount):
        raise ValueError("Укажите либо процент, либо фиксированную скидку")
    applies = payload.get("applies_to_tariff")
    tariff = normalize_tariff_code(applies) if applies else None
    if tariff == "free":
        tariff = None
    if tariff and tariff not in PAID_TARIFFS:
        raise ValueError("Скидка применяется к standard или full")
    return {
        "kind": PROMO_KIND_DISCOUNT,
        "discount_percent": int(percent) if percent else None,
        "discount_amount": int(amount) if amount else None,
        "applies_to_tariff": tariff,
        "grant_days": None,
    }
