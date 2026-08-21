"""Unified post row contract for collector, distribute, analytics, and DDL generation."""

from __future__ import annotations

POST_STATUS_VALUES: tuple[str, ...] = (
    "created",
    "collected",
    "processing",
    "ready",
    "review",
    "publishing",
    "published",
    "distributed",
    "deleted",
)

POST_STATUS_CHECK = (
    "CHECK (status IN ("
    + ", ".join(f"'{value}'" for value in POST_STATUS_VALUES)
    + "))"
)

# Column order used by collector/distribute when copying rows between tables.
POST_BASE_COLUMNS: tuple[str, ...] = (
    "user_id",
    "domain",
    "url",
    "title",
    "author",
    "avatar",
    "post_date",
    "post_text",
    "screenshot",
    "images",
    "image_over_text",
    "comments",
    "reposts",
    "likes",
    "views",
    "is_ad",
    "status",
    "post_type",
    "to_tg",
    "to_tw",
    "to_wp",
    "to_vk",
    "to_dzen",
    "to_instagram",
    "to_threads",
    "target_channels",
    "target_groups",
)

# SQL column definitions for CREATE TABLE generation.
POST_BASE_COLUMN_DEFS: dict[str, str] = {
    "user_id": "INTEGER NOT NULL",
    "domain": "VARCHAR(255)",
    "url": "TEXT",
    "title": "VARCHAR(500)",
    "author": "VARCHAR(255)",
    "avatar": "TEXT",
    "post_date": "TIMESTAMPTZ",
    "post_text": "TEXT",
    "screenshot": "TEXT",
    "images": "JSONB DEFAULT '[]'",
    "image_over_text": "TEXT",
    "comments": "INTEGER DEFAULT 0",
    "reposts": "INTEGER DEFAULT 0",
    "likes": "INTEGER DEFAULT 0",
    "views": "INTEGER DEFAULT 0",
    "is_ad": "BOOLEAN DEFAULT FALSE",
    "status": f"VARCHAR(50) DEFAULT 'collected' {POST_STATUS_CHECK}",
    "post_type": "VARCHAR(50)",
    "to_tg": "BOOLEAN DEFAULT FALSE",
    "to_tw": "BOOLEAN DEFAULT FALSE",
    "to_wp": "BOOLEAN DEFAULT FALSE",
    "to_vk": "BOOLEAN DEFAULT FALSE",
    "to_dzen": "BOOLEAN DEFAULT FALSE",
    "to_instagram": "BOOLEAN DEFAULT FALSE",
    "to_threads": "BOOLEAN DEFAULT FALSE",
    "target_channels": "JSONB DEFAULT '[]'",
    "target_groups": "JSONB DEFAULT '[]'",
}

# Tables counted by quota_service (must stay in sync with quota logic).
QUOTA_POST_TABLES: tuple[str, ...] = (
    "posts",
    "tg_posts",
    "tw_posts",
    "wp_posts",
    "vk_posts",
    "url_posts",
    "cpost_posts",
    "threads_posts",
    "dzen_posts",
    "instagram_posts",
)
