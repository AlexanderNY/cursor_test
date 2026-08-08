"""Продуктовая матрица тарифов: лимиты и возможности (единый источник для API /billing/plans)."""

from typing import Any

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
        "description": "Старт: один бренд, до 3 own-каналов, чтение инбокса без reply.",
        "monthly_posts_limit": 300,
        "storage_gb_limit": 1,
        "max_connected_platforms": 3,
        "max_own_channels": 3,
        "max_brands": 1,
        "max_targets_per_job": 1,
        "max_automations": 0,
        "max_team_seats": 1,
        "ai_calls_month": 0,
        "schedule_horizon_days": 7,
        "stats_retention_days": 7,
        "csv_import_rows": 20,
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
        },
        "sort_order": 0,
    },
    {
        "code": "standard",
        "display_name": "Standard",
        "description": "Команда до 5, multi-send, reply/redirect, AI и automations.",
        "monthly_posts_limit": 3000,
        "storage_gb_limit": 10,
        "max_connected_platforms": 8,
        "max_own_channels": 10,
        "max_brands": 5,
        "max_targets_per_job": 5,
        "max_automations": 5,
        "max_team_seats": 5,
        "ai_calls_month": 100,
        "schedule_horizon_days": 30,
        "stats_retention_days": 90,
        "csv_import_rows": 200,
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
        },
        "sort_order": 10,
    },
    {
        "code": "full",
        "display_name": "Full",
        "description": "Максимум: 20 каналов, competitors, webhooks, best-times, SLA.",
        "monthly_posts_limit": 50000,
        "storage_gb_limit": 100,
        "max_connected_platforms": 20,
        "max_own_channels": 20,
        "max_brands": 20,
        "max_targets_per_job": 20,
        "max_automations": 50,
        "max_team_seats": 20,
        "ai_calls_month": 2000,
        "schedule_horizon_days": 90,
        "stats_retention_days": 365,
        "csv_import_rows": 2000,
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
        },
        "sort_order": 20,
    },
]


def normalize_tariff_code(code: str | None) -> str:
    c = (code or "free").strip().lower()
    return _TARIFF_ALIASES.get(c, c)


def get_plan_by_code(code: str) -> dict[str, Any] | None:
    c = normalize_tariff_code(code)
    for p in PLAN_DEFINITIONS:
        if p["code"] == c:
            return p
    return None


def monthly_posts_limit_for_tariff(tariff: str) -> int:
    p = get_plan_by_code(tariff)
    if p:
        return int(p["monthly_posts_limit"])
    return int(PLAN_DEFINITIONS[0]["monthly_posts_limit"])


def plan_limit(tariff: str, key: str, default: int = 0) -> int:
    p = get_plan_by_code(tariff)
    if not p:
        return default
    return int(p.get(key, default))


def plan_feature(tariff: str, key: str, default: bool = False) -> bool:
    p = get_plan_by_code(tariff)
    if not p:
        return default
    features = p.get("features") or {}
    return bool(features.get(key, default))
