"""Aggregate DDL from all services for monolithic bootstrap and init scripts."""

from __future__ import annotations

from shared.db.schemas import (
    auth,
    core,
    dzen_bot,
    instagram_bot,
    scheduler,
    tg_bot,
    th_bot,
    tw_bot,
    url_bot,
    vk_bot,
    wp_bot,
)

PLATFORM_SCHEMAS: list[str] = (
    tg_bot.ALL_TABLES
    + vk_bot.ALL_TABLES
    + wp_bot.ALL_TABLES
    + tw_bot.ALL_TABLES
    + dzen_bot.ALL_TABLES
    + instagram_bot.ALL_TABLES
    + th_bot.ALL_TABLES
    + url_bot.ALL_TABLES
)

ALL_SCHEMAS: list[str] = (
    auth.ALL_TABLES
    + core.ALL_TABLES
    + PLATFORM_SCHEMAS
    + scheduler.ALL_TABLES
)


def get_platform_schemas() -> list[str]:
    return list(PLATFORM_SCHEMAS)


def get_all_schemas() -> list[str]:
    return list(ALL_SCHEMAS)
