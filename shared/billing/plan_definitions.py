"""Продуктовая матрица тарифов — единый источник для auth, core и UI billing API."""

from __future__ import annotations

from typing import Any, Optional

# Aliases: legacy basic→standard, premium→full
_TARIFF_ALIASES: dict[str, str] = {
    "basic": "standard",
    "premium": "full",
}

# Код тарифа совпадает с users.tariff (free | standard | full)
PLAN_DEFINITIONS: list[dict[str, Any]] = [
    {
        "code": "free",
        "display_name": "Free",
        "description": "Старт: 1 бренд, до 3 own-каналов, TG listening (алерты), инбокс без reply, без AI.",
        "monthly_posts_limit": 300,
        "storage_gb_limit": 1,
        "max_connected_platforms": 3,
        "max_own_channels": 3,
        "max_competitor_channels": 0,
        "max_brands": 1,
        "max_targets_per_job": 1,
        "max_automations": 0,
        "max_templates": 5,
        "max_media_packs": 2,
        "max_content_series": 1,
        "max_team_seats": 1,
        "ai_calls_month": 0,
        "schedule_horizon_days": 7,
        "stats_retention_days": 7,
        "csv_import_rows": 20,
        "price_monthly": 0,
        "currency": "RUB",
        "features": {
            "ai_processing": False,
            "review_queue": True,
            "priority_queues": False,
            "webhooks": False,
            "sla_support": False,
            "inbox_read": True,
            "inbox_reply": False,
            "inbox_redirect": False,
            "multi_channel_send": True,
            "schedule": True,
            "automations": False,
            "ai_composer": False,
            "channel_stats": True,
            "competitors": False,
            "approval_workflow": False,
            "best_times": False,
            "auto_moderation": False,
            "tg_listening": True,
        },
        "sort_order": 0,
    },
    {
        "code": "standard",
        "display_name": "Standard",
        "description": "Команда до 5: AI composer, automations, approval, reply/redirect, TG listening.",
        "monthly_posts_limit": 3000,
        "storage_gb_limit": 10,
        "max_connected_platforms": 8,
        "max_own_channels": 10,
        "max_competitor_channels": 0,
        "max_brands": 5,
        "max_targets_per_job": 5,
        "max_automations": 5,
        "max_templates": 50,
        "max_media_packs": 20,
        "max_content_series": 10,
        "max_team_seats": 5,
        "ai_calls_month": 100,
        "schedule_horizon_days": 30,
        "stats_retention_days": 90,
        "csv_import_rows": 200,
        "price_monthly": 2990,
        "currency": "RUB",
        "features": {
            "ai_processing": True,
            "review_queue": True,
            "priority_queues": False,
            "webhooks": False,
            "sla_support": False,
            "inbox_read": True,
            "inbox_reply": True,
            "inbox_redirect": True,
            "multi_channel_send": True,
            "schedule": True,
            "automations": True,
            "ai_composer": True,
            "channel_stats": True,
            "competitors": False,
            "approval_workflow": True,
            "best_times": True,
            "auto_moderation": True,
            "tg_listening": True,
        },
        "sort_order": 10,
    },
    {
        "code": "full",
        "display_name": "Full",
        "description": "Максимум: competitors, высокий AI, webhooks и SLA, до 20 seats.",
        "monthly_posts_limit": 50000,
        "storage_gb_limit": 100,
        "max_connected_platforms": 20,
        "max_own_channels": 20,
        "max_competitor_channels": 10,
        "max_brands": 20,
        "max_targets_per_job": 20,
        "max_automations": 50,
        "max_templates": 500,
        "max_media_packs": 100,
        "max_content_series": 50,
        "max_team_seats": 20,
        "ai_calls_month": 2000,
        "schedule_horizon_days": 90,
        "stats_retention_days": 365,
        "csv_import_rows": 2000,
        "price_monthly": 7990,
        "currency": "RUB",
        "features": {
            "ai_processing": True,
            "review_queue": True,
            "priority_queues": True,
            "webhooks": True,
            "sla_support": True,
            "inbox_read": True,
            "inbox_reply": True,
            "inbox_redirect": True,
            "multi_channel_send": True,
            "schedule": True,
            "automations": True,
            "ai_composer": True,
            "channel_stats": True,
            "competitors": True,
            "approval_workflow": True,
            "best_times": True,
            "auto_moderation": True,
            "tg_listening": True,
        },
        "sort_order": 20,
    },
]


def normalize_tariff_code(code: Optional[str]) -> str:
    c = (code or "free").strip().lower()
    return _TARIFF_ALIASES.get(c, c)


def is_paid_tariff(code: Optional[str]) -> bool:
    plan = get_plan_by_code(code)
    if not plan:
        return False
    return int(plan.get("price_monthly") or 0) > 0


def paid_tariff_codes() -> list[str]:
    return [p["code"] for p in PLAN_DEFINITIONS if int(p.get("price_monthly") or 0) > 0]


def get_plan_by_code(code: Optional[str]) -> dict[str, Any] | None:
    c = normalize_tariff_code(code)
    for p in PLAN_DEFINITIONS:
        if p["code"] == c:
            return p
    return None


def monthly_posts_limit_for_tariff(tariff: Optional[str]) -> int:
    p = get_plan_by_code(tariff)
    if p:
        return int(p["monthly_posts_limit"])
    return int(PLAN_DEFINITIONS[0]["monthly_posts_limit"])


def plan_limit(tariff: Optional[str], key: str, default: int = 0) -> int:
    p = get_plan_by_code(tariff)
    if not p:
        return default
    return int(p.get(key, default))


def plan_feature(tariff: Optional[str], key: str, default: bool = False) -> bool:
    p = get_plan_by_code(tariff)
    if not p:
        return default
    features = p.get("features") or {}
    return bool(features.get(key, default))


def quota_limits_for_tariff(tariff: Optional[str]) -> dict[str, Any]:
    """Shape expected by core quota_service / PlanGate consumers."""
    p = get_plan_by_code(tariff) or PLAN_DEFINITIONS[0]
    return {
        "monthly_posts": int(p["monthly_posts_limit"]),
        "storage_gb": int(p["storage_gb_limit"]),
        "max_own_channels": int(p["max_own_channels"]),
        "max_competitor_channels": int(p.get("max_competitor_channels", 0)),
        "max_brands": int(p["max_brands"]),
        "max_targets_per_job": int(p["max_targets_per_job"]),
        "max_automations": int(p["max_automations"]),
        "max_templates": int(p["max_templates"]),
        "max_media_packs": int(p["max_media_packs"]),
        "max_content_series": int(p.get("max_content_series", 0)),
        "max_team_seats": int(p["max_team_seats"]),
        "ai_calls_month": int(p["ai_calls_month"]),
        "schedule_horizon_days": int(p["schedule_horizon_days"]),
        "stats_retention_days": int(p["stats_retention_days"]),
        "csv_import_rows": int(p["csv_import_rows"]),
        "features": dict(p.get("features") or {}),
    }
