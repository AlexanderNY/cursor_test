"""Dzen bot service DDL."""

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

ALL_TABLES: list[str] = [
    DZEN_PROFILES_TABLE,
]
