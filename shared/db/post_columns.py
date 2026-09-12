"""Unified post row contract for collector, distribute, analytics, and DDL generation."""

from __future__ import annotations

POST_STATUS_VALUES: tuple[str, ...] = (
    "collected",
    "created",
    "processing",
    "ready",
    "review",
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
    "brand_id",
    "channel_id",
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
    "target_channels",
    "target_groups",
)

# SQL column definitions for CREATE TABLE generation.
POST_BASE_COLUMN_DEFS: dict[str, str] = {
    "user_id": "INTEGER NOT NULL",
    "brand_id": "INTEGER",
    "channel_id": "INTEGER",
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
    "target_channels": "JSONB DEFAULT '[]'",
    "target_groups": "JSONB DEFAULT '[]'",
}

# All post-like tables that need brand_id / channel_id migration.
POST_TENANCY_TABLES: tuple[str, ...] = (
    "posts",
)

# Tables counted by quota_service (must stay in sync with quota logic).
QUOTA_POST_TABLES: tuple[str, ...] = (
    "posts",
)
