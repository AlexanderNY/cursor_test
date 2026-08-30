"""Telegram bot service DDL."""

from shared.db.generate_ddl import build_post_indexes, build_post_table_ddl

TG_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS tg_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    api_id VARCHAR(50),
    api_hash VARCHAR(100),
    chats_to_read JSONB DEFAULT '[]',
    save_conditions JSONB DEFAULT '[]',
    channel_to_post VARCHAR(50),
    channels_to_post JSONB DEFAULT '[]',
    alert_enabled BOOLEAN DEFAULT FALSE,
    alert_rules JSONB DEFAULT '[]',
    process_enabled BOOLEAN DEFAULT FALSE,
    processing_description TEXT,
    remove_emojis BOOLEAN DEFAULT FALSE,
    remove_images BOOLEAN DEFAULT FALSE,
    clean_html BOOLEAN DEFAULT FALSE,
    process_services JSONB,
    status_review_after_process BOOLEAN DEFAULT FALSE,
    add_static_html BOOLEAN DEFAULT FALSE,
    static_html_content TEXT,
    telegram_username VARCHAR(255),
    auth_state VARCHAR(50) DEFAULT 'authorized',
    auth_phone_code_hash VARCHAR(255),
    auth_phone_number VARCHAR(50),
    summarize_enabled BOOLEAN DEFAULT FALSE,
    summarize_min_length INTEGER DEFAULT 500,
    digest_interval_min INTEGER DEFAULT 30,
    digest_channel VARCHAR(50),
    classification_enabled BOOLEAN DEFAULT FALSE,
    classification_categories JSONB DEFAULT '["новости", "реклама", "технологии", "финансы", "другое"]',
    batch_enrichment_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

TG_PROFILES_BATCH_ENRICH_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE tg_profiles ADD COLUMN batch_enrichment_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
"""

TG_POSTS_TABLE = build_post_table_ddl(
    "tg_posts",
    extra_columns={
        "metadata": "JSONB DEFAULT '{}'",
        "publish_at": "TIMESTAMPTZ",
        "telegram_message_id": "BIGINT",
        "telegram_chat_id": "TEXT",
    },
)

TG_POSTS_INDEXES = build_post_indexes("tg_posts", with_publish_at=True)

TG_POST_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS tg_post_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    hashtags TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_post_templates_user ON tg_post_templates(user_id);
"""

TG_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS tg_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chat_id BIGINT,
    message_id BIGINT,
    event_type VARCHAR(50) NOT NULL,
    rule_id VARCHAR(64),
    matched_conditions JSONB DEFAULT '[]',
    text_hash VARCHAR(64),
    text_preview TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_events_user_created ON tg_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_events_type_created ON tg_events(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_events_hash_chat ON tg_events(text_hash, chat_id);
CREATE INDEX IF NOT EXISTS idx_tg_events_rule_created ON tg_events(rule_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_events_chat_created ON tg_events(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_events_user_type_created
    ON tg_events(user_id, event_type, created_at);
"""

TG_DEDUP_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS tg_dedup_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    chat_id BIGINT NOT NULL,
    rule_id VARCHAR(64),
    channel_to_post VARCHAR(50),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_dedup_user_hash_chat
    ON tg_dedup_cache(user_id, text_hash, chat_id);
CREATE INDEX IF NOT EXISTS idx_tg_dedup_expires ON tg_dedup_cache(expires_at);
"""

TG_SUMMARY_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS tg_summary_cache (
    id SERIAL PRIMARY KEY,
    text_hash VARCHAR(64) NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_summary_cache_expires ON tg_summary_cache(expires_at);
"""

TG_DIGESTS_TABLE = """
CREATE TABLE IF NOT EXISTS tg_digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chat_id BIGINT NOT NULL,
    digest_text TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_digests_user_created ON tg_digests(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_digests_user_chat_created
    ON tg_digests(user_id, chat_id, created_at DESC);
"""

ALL_TABLES: list[str] = [
    TG_PROFILES_TABLE,
    TG_PROFILES_BATCH_ENRICH_MIGRATION,
    TG_POSTS_TABLE,
    TG_POSTS_INDEXES,
    TG_POST_TEMPLATES_TABLE,
    TG_EVENTS_TABLE,
    TG_DEDUP_CACHE_TABLE,
    TG_SUMMARY_CACHE_TABLE,
    TG_DIGESTS_TABLE,
]
