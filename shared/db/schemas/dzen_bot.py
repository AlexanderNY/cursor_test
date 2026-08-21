"""Dzen bot service DDL."""

from shared.db.generate_ddl import build_post_indexes, build_post_table_ddl

DZEN_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS dzen_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    rss_feed_url TEXT,
    channel_name VARCHAR(255),
    channels_to_read JSONB DEFAULT '[]',
    rss_token VARCHAR(255),
    yandex_login VARCHAR(255),
    yandex_password TEXT,
    dzen_studio_url TEXT,
    collect_source VARCHAR(20) DEFAULT 'rss',
    last_auth_error TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

DZEN_POSTS_TABLE = build_post_table_ddl(
    "dzen_posts",
    extra_columns={"videos": "JSONB DEFAULT '[]'"},
    column_overrides={"to_dzen": "BOOLEAN DEFAULT TRUE"},
)

DZEN_POSTS_INDEXES = build_post_indexes("dzen_posts")

ALL_TABLES: list[str] = [
    DZEN_PROFILES_TABLE,
    DZEN_POSTS_TABLE,
    DZEN_POSTS_INDEXES,
]
