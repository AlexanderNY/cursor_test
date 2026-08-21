"""Core service DDL (hub posts, SMM, ops)."""

from shared.db.generate_ddl import build_post_indexes, build_post_table_ddl

POSTS_TABLE = build_post_table_ddl(
    "posts",
    extra_columns={
        "source_platform": "VARCHAR(10)",
        "source_id": "INTEGER",
        "platform_texts": "JSONB DEFAULT '{}'",
        "videos": "JSONB DEFAULT '[]'",
    },
    table_constraints=[
        "CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
    ],
)

POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source ON posts(source_platform, source_id)
    WHERE source_platform IS NOT NULL;
""" + build_post_indexes("posts")

CPOST_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS cpost_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    default_platforms JSONB DEFAULT '{"tg": false, "tw": false, "wp": false, "vk": false}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CPOST_POSTS_TABLE = build_post_table_ddl("cpost_posts")
CPOST_POSTS_INDEXES = build_post_indexes("cpost_posts")

CURL_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS curl_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'standard',
    time_intervals JSONB DEFAULT '[]',
    url TEXT,
    xpath TEXT,
    take_screenshot BOOLEAN DEFAULT FALSE,
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    urls JSONB DEFAULT '[]',
    process_before_publish BOOLEAN DEFAULT FALSE,
    process_description TEXT,
    remove_emojis BOOLEAN DEFAULT FALSE,
    remove_images BOOLEAN DEFAULT FALSE,
    clean_html BOOLEAN DEFAULT FALSE,
    process_services JSONB,
    status_review_after_process BOOLEAN DEFAULT FALSE,
    add_static_html BOOLEAN DEFAULT FALSE,
    static_html_content TEXT,
    screenshot_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

CURL_ONE_TIME_DONE_TABLE = """
CREATE TABLE IF NOT EXISTS curl_one_time_done (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    xpath TEXT NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url, xpath)
);
CREATE INDEX IF NOT EXISTS idx_curl_one_time_done_user ON curl_one_time_done(user_id);
"""

SERVICE_CYCLE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS service_cycle_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    cycle_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ok',
    detail TEXT,
    items_processed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_service_cycle_log_created ON service_cycle_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service_cycle_log_service_created
    ON service_cycle_log(service_name, created_at DESC);
"""

AI_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS ai_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payload JSONB DEFAULT '{}',
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_ai_tasks_status_created ON ai_tasks(status, created_at);
"""

NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    user_id INTEGER,
    type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
"""

FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('bug_report', 'suggestion', 'contact_author')),
    text TEXT NOT NULL,
    email VARCHAR(255),
    user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);
"""

SYSTEM_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO system_settings (key, value)
VALUES ('ai_enabled', 'true'::jsonb)
ON CONFLICT (key) DO NOTHING;
"""

GUIDE_BLOCKS_TABLE = """
CREATE TABLE IF NOT EXISTS guide_blocks (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(64) NOT NULL UNIQUE,
    toc_label VARCHAR(128) NOT NULL DEFAULT '',
    title VARCHAR(255) NOT NULL DEFAULT '',
    subtitle TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    style JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_guide_blocks_sort ON guide_blocks(sort_order);
"""

SMM_BRANDS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_brands (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

SMM_BRAND_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_brand_channels (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    network VARCHAR(10) NOT NULL CHECK (network IN ('tg', 'vk')),
    external_id VARCHAR(128) NOT NULL,
    title VARCHAR(255),
    kind VARCHAR(20) NOT NULL DEFAULT 'channel'
        CHECK (kind IN ('channel', 'group', 'public')),
    role VARCHAR(20) NOT NULL DEFAULT 'own'
        CHECK (role IN ('own', 'competitor', 'source')),
    color_override VARCHAR(7),
    publish_enabled BOOLEAN DEFAULT TRUE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    discussion_external_id VARCHAR(128),
    discussion_title VARCHAR(255),
    comments_collect_enabled BOOLEAN DEFAULT FALSE,
    alert_enabled BOOLEAN DEFAULT FALSE,
    save_conditions JSONB DEFAULT '[]'::jsonb,
    processing JSONB DEFAULT '{}'::jsonb,
    alert_delivery JSONB DEFAULT '{}'::jsonb,
    alert_rules JSONB DEFAULT '[]'::jsonb,
    conditions_mode VARCHAR(20) DEFAULT 'any_of',
    publish_targets JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brand_id, network, external_id)
);
CREATE INDEX IF NOT EXISTS idx_smm_channels_discussion
    ON smm_brand_channels (network, discussion_external_id)
    WHERE discussion_external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_smm_channels_tg_external
    ON smm_brand_channels (network, external_id)
    WHERE network = 'tg';
"""

SMM_INBOX_TABLE = """
CREATE TABLE IF NOT EXISTS smm_inbox_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER REFERENCES smm_brands(id) ON DELETE SET NULL,
    network VARCHAR(10) NOT NULL CHECK (network IN ('tg', 'vk')),
    channel_id INTEGER REFERENCES smm_brand_channels(id) ON DELETE SET NULL,
    thread_id VARCHAR(128),
    type VARCHAR(20) NOT NULL CHECK (type IN ('dm', 'comment', 'reaction')),
    author VARCHAR(255),
    text TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'read', 'replied', 'archived', 'reply_failed', 'in_progress')),
    external_msg_id VARCHAR(128),
    edited_text TEXT,
    meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_smm_inbox_dedup
    ON smm_inbox_items (user_id, network, external_msg_id)
    WHERE external_msg_id IS NOT NULL;
"""

SMM_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_publish_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER REFERENCES smm_brands(id) ON DELETE SET NULL,
    source_text TEXT NOT NULL,
    media JSONB DEFAULT '[]',
    targets JSONB DEFAULT '[]',
    adapters_result JSONB DEFAULT '{}',
    publish_at TIMESTAMPTZ,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_status_publish ON smm_publish_jobs(status, publish_at);
"""

SMM_AUTOMATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_automations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER REFERENCES smm_brands(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('rss', 'tg_repost', 'mention')),
    config JSONB NOT NULL DEFAULT '{}',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

SMM_COMPETITOR_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_competitor_snapshots (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES smm_brand_channels(id) ON DELETE CASCADE,
    external_post_id VARCHAR(128),
    post_text TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    posted_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

SMM_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_smm_brands_user_id ON smm_brands(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_brand_channels_brand_id ON smm_brand_channels(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_user_id ON smm_inbox_items(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_brand_status ON smm_inbox_items(brand_id, status);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_brand ON smm_publish_jobs(user_id, brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_automations_user ON smm_automations(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_channel ON smm_competitor_snapshots(channel_id);
"""

SMM_CHANNEL_COUNTERS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_channel_counters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL REFERENCES smm_brand_channels(id) ON DELETE CASCADE,
    day DATE NOT NULL,
    sent INTEGER DEFAULT 0,
    received INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    UNIQUE (channel_id, day)
);
CREATE INDEX IF NOT EXISTS idx_smm_channel_counters_user_day ON smm_channel_counters(user_id, day);
"""

SMM_AI_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS smm_ai_usage (
    user_id INTEGER NOT NULL,
    month CHAR(7) NOT NULL,
    calls INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, month)
);
"""

ALL_TABLES: list[str] = [
    POSTS_TABLE,
    POSTS_INDEXES,
    CPOST_PROFILES_TABLE,
    CPOST_POSTS_TABLE,
    CPOST_POSTS_INDEXES,
    CURL_SETTINGS_TABLE,
    CURL_ONE_TIME_DONE_TABLE,
    SERVICE_CYCLE_LOG_TABLE,
    AI_TASKS_TABLE,
    NOTIFICATIONS_TABLE,
    FEEDBACK_TABLE,
    SYSTEM_SETTINGS_TABLE,
    GUIDE_BLOCKS_TABLE,
    SMM_BRANDS_TABLE,
    SMM_BRAND_CHANNELS_TABLE,
    SMM_INBOX_TABLE,
    SMM_JOBS_TABLE,
    SMM_AUTOMATIONS_TABLE,
    SMM_COMPETITOR_SNAPSHOTS_TABLE,
    SMM_INDEXES,
    SMM_CHANNEL_COUNTERS_TABLE,
    SMM_AI_USAGE_TABLE,
]
