"""Core service DDL (hub posts, SMM, ops)."""

from shared.db.generate_ddl import (
    build_post_indexes,
    build_post_table_ddl,
    build_post_tenancy_migration,
)
from shared.db.queue_notify import QUEUE_NOTIFY_TRIGGERS
from shared.db.schemas.posts import (
    POST_TARGETS_INDEXES,
    POST_TARGETS_TABLE,
    POSTS_CONTRACT_CLEANUP,
    POSTS_SOURCE_NATIVE_DEDUPE,
    POSTS_UNIFIED_MIGRATION,
)

POSTS_TABLE = build_post_table_ddl(
    "posts",
    extra_columns={
        "source_platform": "VARCHAR(10)",
        "source_id": "INTEGER",
        "source_native_id": "TEXT",
        "platform_texts": "JSONB DEFAULT '{}'",
        "videos": "JSONB DEFAULT '[]'",
        "extras": "JSONB DEFAULT '{}'",
    },
    table_constraints=[
        "CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
    ],
)

POSTS_INDEXES = build_post_indexes("posts") + """
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source ON posts(source_platform, source_id)
    WHERE source_platform IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source_native
    ON posts(user_id, source_platform, source_native_id)
    WHERE source_native_id IS NOT NULL;
"""

CPOST_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS cpost_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    default_platforms JSONB DEFAULT '{"tg": false, "tw": false, "wp": false, "vk": false}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

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

ROADMAP_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS roadmap_items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_roadmap_items_active_created
    ON roadmap_items (is_active, created_at DESC);
"""

ROADMAP_VOTES_TABLE = """
CREATE TABLE IF NOT EXISTS roadmap_votes (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES roadmap_items(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (item_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_roadmap_votes_item_id ON roadmap_votes(item_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_votes_user_id ON roadmap_votes(user_id);
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

INSERT INTO system_settings (key, value)
VALUES (
    'site_9to18_promo',
    '{
      "enabled": true,
      "serviceSlug": "copyparse",
      "eyebrow": "Спотлайт · взаимное продвижение",
      "title": "CopyParse: SaaS кросспостинга как живой стенд",
      "body": "9to18 — площадка взаимного продвижения проектов. Сейчас в фокусе CopyParse: бренды, каналы, календарь и inbox — тот же стек, который разбираем в Learn. Поддержите развитие сервиса и загляните на стенд.",
      "ctaLabel": "Открыть copyparse.ru",
      "ctaHref": "https://www.copyparse.ru"
    }'::jsonb
)
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
    tone_of_voice TEXT,
    style_notes TEXT,
    prompt_snippets JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

SMM_BRANDS_DEMO_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
"""

# Existing post tables predate brand_id / channel_id; CREATE TABLE IF NOT EXISTS
# will not add them. Must run before any CREATE INDEX on those columns.
POST_TENANCY_MIGRATION = build_post_tenancy_migration()

SMM_BRAND_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_brand_channels (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    network VARCHAR(20) NOT NULL CHECK (network IN (
        'tg', 'vk', 'url',
        'instagram', 'threads', 'tw', 'dzen', 'wp'
    )),
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
    network VARCHAR(20) NOT NULL CHECK (network IN (
        'tg', 'vk', 'url',
        'instagram', 'threads', 'tw', 'dzen', 'wp'
    )),
    channel_id INTEGER REFERENCES smm_brand_channels(id) ON DELETE SET NULL,
    thread_id VARCHAR(128),
    type VARCHAR(20) NOT NULL CHECK (type IN ('dm', 'comment', 'reaction', 'competitor_post')),
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
    assigned_to INTEGER,
    rejection_comment TEXT,
    created_by_user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_status_publish ON smm_publish_jobs(status, publish_at);
"""

SMM_JOBS_APPROVAL_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN assigned_to INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN rejection_comment TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_assigned_to
    ON smm_publish_jobs(assigned_to)
    WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_status
    ON smm_publish_jobs(user_id, status);
"""

SMM_JOBS_CREATED_BY_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN created_by_user_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
UPDATE smm_publish_jobs
SET created_by_user_id = COALESCE(assigned_to, user_id)
WHERE created_by_user_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_created_by
    ON smm_publish_jobs(created_by_user_id)
    WHERE created_by_user_id IS NOT NULL;
"""

SMM_JOB_COMMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_job_comments (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES smm_publish_jobs(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    parent_id INTEGER NULL REFERENCES smm_job_comments(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    anchor JSONB,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_job_comments_job
    ON smm_job_comments(job_id, created_at);
"""

SMM_JOB_REVISIONS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_job_revisions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES smm_publish_jobs(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    source_text TEXT,
    media JSONB DEFAULT '[]',
    targets JSONB DEFAULT '[]',
    publish_at TIMESTAMPTZ,
    status VARCHAR(30),
    change_summary VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_job_revisions_job
    ON smm_job_revisions(job_id, created_at DESC);
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
    post_url TEXT,
    text_hash VARCHAR(64),
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    posted_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
DO $$ BEGIN
  ALTER TABLE smm_competitor_snapshots ADD COLUMN post_url TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_competitor_snapshots ADD COLUMN text_hash VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE UNIQUE INDEX IF NOT EXISTS idx_smm_competitor_external_post
    ON smm_competitor_snapshots (channel_id, external_post_id)
    WHERE external_post_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_smm_competitor_text_hash
    ON smm_competitor_snapshots (channel_id, text_hash)
    WHERE text_hash IS NOT NULL;
"""

SMM_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_smm_brands_user_id ON smm_brands(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_brand_channels_brand_id ON smm_brand_channels(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_user_id ON smm_inbox_items(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_brand_status ON smm_inbox_items(brand_id, status);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_brand ON smm_publish_jobs(user_id, brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_automations_user ON smm_automations(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_channel ON smm_competitor_snapshots(channel_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_posted_at
    ON smm_competitor_snapshots (channel_id, posted_at DESC NULLS LAST);
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

SMM_ANALYTICS_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_channel_counters ADD COLUMN alerts_sent INTEGER DEFAULT 0;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE TABLE IF NOT EXISTS smm_message_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    channel_id INTEGER REFERENCES smm_brand_channels(id) ON DELETE SET NULL,
    direction VARCHAR(20) NOT NULL
        CHECK (direction IN ('collected', 'published', 'alert', 'failed')),
    platform VARCHAR(10) NOT NULL CHECK (platform IN ('tg', 'vk')),
    post_id INTEGER,
    external_msg_id VARCHAR(128),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_message_events_channel_created
    ON smm_message_events(channel_id, created_at);
CREATE INDEX IF NOT EXISTS idx_smm_message_events_user_created
    ON smm_message_events(user_id, created_at);
CREATE TABLE IF NOT EXISTS smm_post_metric_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    platform VARCHAR(10) NOT NULL CHECK (platform IN ('tg', 'vk')),
    post_id INTEGER NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    captured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_post_metric_snapshots_post
    ON smm_post_metric_snapshots(platform, post_id, captured_at);
CREATE TABLE IF NOT EXISTS smm_channel_metric_snapshots (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES smm_brand_channels(id) ON DELETE CASCADE,
    subscribers INTEGER DEFAULT 0,
    captured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_channel_metric_channel
    ON smm_channel_metric_snapshots(channel_id, captured_at);
"""

SMM_CHANNEL_AUTH_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN auth_status VARCHAR(20) DEFAULT 'unknown';
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN auth_checked_at TIMESTAMPTZ;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN auth_error TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN auth_capabilities JSONB DEFAULT '{}'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
"""

SMM_BRANDS_AI_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN tone_of_voice TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN style_notes TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN prompt_snippets JSONB NOT NULL DEFAULT '[]'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
"""

SMM_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS smm_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('prompt', 'cta', 'utm', 'post_body')),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_templates_brand
    ON smm_templates(brand_id, kind);
CREATE INDEX IF NOT EXISTS idx_smm_templates_user
    ON smm_templates(user_id);
"""

SMM_CONTENT_SERIES_TABLE = """
CREATE TABLE IF NOT EXISTS smm_content_series (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#8B5CF6',
    body TEXT NOT NULL DEFAULT '',
    template_id INTEGER REFERENCES smm_templates(id) ON DELETE SET NULL,
    targets JSONB NOT NULL DEFAULT '[]'::jsonb,
    weekdays JSONB NOT NULL DEFAULT '[]'::jsonb,
    publish_time VARCHAR(5) NOT NULL DEFAULT '10:00',
    cadence VARCHAR(20) NOT NULL DEFAULT 'weekly'
        CHECK (cadence IN ('weekly', 'biweekly')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    starts_on DATE,
    ends_on DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_content_series_brand
    ON smm_content_series(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_content_series_user
    ON smm_content_series(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_content_series_active
    ON smm_content_series(brand_id, is_active)
    WHERE is_active = TRUE;
"""

SMM_JOBS_SERIES_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs
    ADD COLUMN series_id INTEGER REFERENCES smm_content_series(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_series
    ON smm_publish_jobs(series_id)
    WHERE series_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_series_publish
    ON smm_publish_jobs(series_id, publish_at)
    WHERE series_id IS NOT NULL;
"""

SMM_MEDIA_PACKS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_media_packs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL REFERENCES smm_brands(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    object_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    caption TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smm_media_packs_brand
    ON smm_media_packs(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_media_packs_user
    ON smm_media_packs(user_id);
"""

LEARN_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS learn_posts (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(128) UNIQUE NOT NULL,
    episode VARCHAR(32) NOT NULL DEFAULT '',
    title VARCHAR(512) NOT NULL,
    short_title VARCHAR(128) NOT NULL DEFAULT '',
    rubric_id VARCHAR(64) NOT NULL DEFAULT 'architecture',
    sort_order INTEGER NOT NULL DEFAULT 0,
    theory TEXT NOT NULL DEFAULT '',
    lab TEXT NOT NULL DEFAULT '',
    cheatsheet TEXT NOT NULL DEFAULT '',
    diagram TEXT NOT NULL DEFAULT '',
    links JSONB NOT NULL DEFAULT '[]'::jsonb,
    structured JSONB NOT NULL DEFAULT '{}'::jsonb,
    theory_format VARCHAR(16) NOT NULL DEFAULT 'markdown'
        CHECK (theory_format IN ('markdown', 'html')),
    lab_format VARCHAR(16) NOT NULL DEFAULT 'markdown'
        CHECK (lab_format IN ('markdown', 'html')),
    cheatsheet_format VARCHAR(16) NOT NULL DEFAULT 'markdown'
        CHECK (cheatsheet_format IN ('markdown', 'html')),
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_learn_posts_order
    ON learn_posts (sort_order ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_learn_posts_published
    ON learn_posts (published_at);
"""

LEARN_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS learn_progress (
    user_id INTEGER NOT NULL,
    slug VARCHAR(128) NOT NULL REFERENCES learn_posts(slug) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_learn_progress_user
    ON learn_progress (user_id);
"""

POST_LIFECYCLE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS post_lifecycle_events (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    post_id INTEGER NOT NULL,
    user_id INTEGER,
    job_id INTEGER,
    from_status VARCHAR(40),
    to_status VARCHAR(40) NOT NULL,
    actor VARCHAR(80) NOT NULL DEFAULT 'system',
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_post_lifecycle_post
    ON post_lifecycle_events (platform, post_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_lifecycle_job
    ON post_lifecycle_events (job_id, created_at DESC)
    WHERE job_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_post_lifecycle_created
    ON post_lifecycle_events (created_at DESC);
"""

ALL_TABLES: list[str] = [
    POSTS_TABLE,
    CPOST_PROFILES_TABLE,
    POST_TENANCY_MIGRATION,
    POSTS_UNIFIED_MIGRATION,
    POSTS_SOURCE_NATIVE_DEDUPE,
    POSTS_INDEXES,
    POST_TARGETS_TABLE,
    POST_TARGETS_INDEXES,
    POSTS_CONTRACT_CLEANUP,
    CURL_SETTINGS_TABLE,
    CURL_ONE_TIME_DONE_TABLE,
    SERVICE_CYCLE_LOG_TABLE,
    AI_TASKS_TABLE,
    NOTIFICATIONS_TABLE,
    FEEDBACK_TABLE,
    ROADMAP_ITEMS_TABLE,
    ROADMAP_VOTES_TABLE,
    SYSTEM_SETTINGS_TABLE,
    GUIDE_BLOCKS_TABLE,
    SMM_BRANDS_TABLE,
    SMM_BRAND_CHANNELS_TABLE,
    SMM_INBOX_TABLE,
    SMM_JOBS_TABLE,
    SMM_JOBS_APPROVAL_MIGRATION,
    SMM_JOBS_CREATED_BY_MIGRATION,
    SMM_JOB_COMMENTS_TABLE,
    SMM_JOB_REVISIONS_TABLE,
    SMM_AUTOMATIONS_TABLE,
    SMM_COMPETITOR_SNAPSHOTS_TABLE,
    SMM_INDEXES,
    SMM_CHANNEL_COUNTERS_TABLE,
    SMM_AI_USAGE_TABLE,
    SMM_ANALYTICS_MIGRATION,
    SMM_CHANNEL_AUTH_MIGRATION,
    SMM_BRANDS_AI_MIGRATION,
    SMM_BRANDS_DEMO_MIGRATION,
    SMM_TEMPLATES_TABLE,
    SMM_CONTENT_SERIES_TABLE,
    SMM_JOBS_SERIES_MIGRATION,
    SMM_MEDIA_PACKS_TABLE,
    LEARN_POSTS_TABLE,
    LEARN_PROGRESS_TABLE,
    POST_LIFECYCLE_EVENTS_TABLE,
    QUEUE_NOTIFY_TRIGGERS,
]
