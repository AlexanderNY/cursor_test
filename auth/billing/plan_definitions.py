"""Продуктовая матрица тарифов: лимиты и возможности (единый источник для API /billing/plans)."""

from typing import Any

# Код тарифа совпадает с users.tariff
PLAN_DEFINITIONS: list[dict[str, Any]] = [
    {
        "code": "free",
        "display_name": "Free",
        "description": "Старт работы с пайплайном постов и одной-двумя платформами.",
        "monthly_posts_limit": 300,
        "storage_gb_limit": 1,
        "max_connected_platforms": 3,
        "features": {
            "ai_processing": False,
            "review_queue": True,
            "priority_queues": False,
            "webhooks": False,
            "sla_support": False,
        },
        "sort_order": 0,
    },
    {
        "code": "basic",
        "display_name": "Basic",
        "description": "Расширенные лимиты и больше платформ для регулярного контента.",
        "monthly_posts_limit": 3000,
        "storage_gb_limit": 10,
        "max_connected_platforms": 8,
        "features": {
            "ai_processing": True,
            "review_queue": True,
            "priority_queues": False,
            "webhooks": False,
            "sla_support": False,
        },
        "sort_order": 10,
    },
    {
        "code": "premium",
        "display_name": "Premium",
        "description": "Максимальные лимиты, приоритет очередей и функции для команд.",
        "monthly_posts_limit": 50000,
        "storage_gb_limit": 100,
        "max_connected_platforms": 20,
        "features": {
            "ai_processing": True,
            "review_queue": True,
            "priority_queues": True,
            "webhooks": True,
            "sla_support": True,
        },
        "sort_order": 20,
    },
]


def get_plan_by_code(code: str) -> dict[str, Any] | None:
    c = (code or "free").strip().lower()
    for p in PLAN_DEFINITIONS:
        if p["code"] == c:
            return p
    return None


def monthly_posts_limit_for_tariff(tariff: str) -> int:
    p = get_plan_by_code(tariff)
    if p:
        return int(p["monthly_posts_limit"])
    return int(PLAN_DEFINITIONS[0]["monthly_posts_limit"])
