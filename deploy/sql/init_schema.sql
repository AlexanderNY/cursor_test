-- Greenfield PostgreSQL schema for db_bot (destroys existing public schema).
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'guest' NOT NULL
        CHECK (role IN ('guest', 'user', 'admin', 'manager', 'author')),
    tariff VARCHAR(50) DEFAULT 'free' NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE NOT NULL,
    billing_provider VARCHAR(32),
    billing_customer_id VARCHAR(255),
    billing_subscription_id VARCHAR(255),
    subscription_status VARCHAR(40),
    subscription_current_period_end TIMESTAMPTZ,
    utm_source VARCHAR(64),
    utm_medium VARCHAR(64),
    utm_campaign VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_source VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_medium VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE users ADD COLUMN utm_campaign VARCHAR(128);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklisted_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_role_tariff_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    role_old VARCHAR(20) NULL,
    role_new VARCHAR(20) NULL,
    tariff_old VARCHAR(50) NULL,
    tariff_new VARCHAR(50) NULL
);

CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_in_group VARCHAR(20) NOT NULL
        CHECK (role_in_group IN ('owner', 'editor', 'approver', 'viewer')),
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (group_id, user_id)
);

CREATE TABLE IF NOT EXISTS group_invites (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    email VARCHAR(255),
    role_in_group VARCHAR(20) NOT NULL
        CHECK (role_in_group IN ('owner', 'editor', 'approver', 'viewer')),
    token VARCHAR(64) UNIQUE NOT NULL,
    invited_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'revoked', 'expired')),
    accepted_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_group_invites_token ON group_invites(token);
CREATE INDEX IF NOT EXISTS idx_group_invites_group_status ON group_invites(group_id, status);
CREATE INDEX IF NOT EXISTS idx_group_invites_email
    ON group_invites(email) WHERE email IS NOT NULL;

ALTER TABLE group_members DROP CONSTRAINT IF EXISTS group_members_role_in_group_check;
ALTER TABLE group_invites DROP CONSTRAINT IF EXISTS group_invites_role_in_group_check;

UPDATE group_members gm
SET role_in_group = 'owner'
FROM groups g
WHERE gm.group_id = g.id
  AND gm.role_in_group IN ('admin', 'manager')
  AND g.created_by_user_id IS NOT NULL
  AND gm.user_id = g.created_by_user_id;

UPDATE group_members
SET role_in_group = 'editor'
WHERE role_in_group IN ('admin', 'manager', 'author');

UPDATE group_members
SET role_in_group = 'viewer'
WHERE role_in_group = 'analyst';

UPDATE group_invites
SET role_in_group = 'editor'
WHERE role_in_group IN ('admin', 'manager', 'author');

UPDATE group_invites
SET role_in_group = 'viewer'
WHERE role_in_group = 'analyst';

-- Ensure each group with a creator has exactly one owner row when possible.
UPDATE group_members gm
SET role_in_group = 'owner'
FROM groups g
WHERE gm.group_id = g.id
  AND g.created_by_user_id IS NOT NULL
  AND gm.user_id = g.created_by_user_id
  AND gm.role_in_group <> 'owner'
  AND NOT EXISTS (
      SELECT 1 FROM group_members gm2
      WHERE gm2.group_id = gm.group_id AND gm2.role_in_group = 'owner'
  );

DO $$ BEGIN
  ALTER TABLE group_members
    ADD CONSTRAINT group_members_role_in_group_check
    CHECK (role_in_group IN ('owner', 'editor', 'approver', 'viewer'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE group_invites
    ADD CONSTRAINT group_invites_role_in_group_check
    CHECK (role_in_group IN ('owner', 'editor', 'approver', 'viewer'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE users ADD COLUMN active_group_id INTEGER
    REFERENCES groups(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_users_active_group_id
    ON users(active_group_id) WHERE active_group_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS plan_definitions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    description TEXT,
    limits_json JSONB NOT NULL DEFAULT '{}',
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS billing_events (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    event_id VARCHAR(255),
    event_type VARCHAR(120) NOT NULL,
    payload_json JSONB,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS growth_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    utm_source VARCHAR(64),
    utm_medium VARCHAR(64),
    utm_campaign VARCHAR(128),
    meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_growth_events_campaign
    ON growth_events (utm_campaign, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_growth_events_type_created
    ON growth_events (event_type, created_at DESC);

CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(80),
    details_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS promo_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(40) UNIQUE NOT NULL,
    description TEXT,
    discount_percent INTEGER NULL CHECK (discount_percent IS NULL OR (discount_percent >= 1 AND discount_percent <= 100)),
    discount_amount INTEGER NULL CHECK (discount_amount IS NULL OR discount_amount >= 0),
    applies_to_tariff VARCHAR(50) NULL,
    max_redemptions INTEGER NULL,
    redeemed_count INTEGER NOT NULL DEFAULT 0,
    valid_from TIMESTAMPTZ NULL,
    valid_until TIMESTAMPTZ NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_promo_codes_code ON promo_codes (code);

CREATE TABLE IF NOT EXISTS billing_plan_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_tariff VARCHAR(50) NOT NULL,
    requested_tariff VARCHAR(50) NOT NULL,
    promo_code VARCHAR(40) NULL,
    list_price INTEGER NOT NULL DEFAULT 0,
    discount_amount INTEGER NOT NULL DEFAULT 0,
    final_price INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(8) NOT NULL DEFAULT 'RUB',
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'invoiced', 'applied', 'rejected', 'cancelled')),
    invoice_sent_at TIMESTAMPTZ NULL,
    invoice_smtp_sent BOOLEAN NOT NULL DEFAULT FALSE,
    invoice_body TEXT NULL,
    admin_comment TEXT NULL,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    processed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_billing_plan_requests_user_status
    ON billing_plan_requests (user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_plan_requests_status
    ON billing_plan_requests (status, created_at DESC);

CREATE TABLE IF NOT EXISTS promo_code_redemptions (
    id SERIAL PRIMARY KEY,
    promo_code_id INTEGER NOT NULL REFERENCES promo_codes(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id INTEGER NULL REFERENCES billing_plan_requests(id) ON DELETE SET NULL,
    used_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (promo_code_id, user_id)
);

CREATE TABLE IF NOT EXISTS user_app_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_session_id VARCHAR(64) NOT NULL,
    tariff VARCHAR(50) NOT NULL DEFAULT 'free',
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active_seconds INTEGER NOT NULL DEFAULT 0,
    is_open BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_blacklisted_tokens_token ON blacklisted_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_user_role_tariff_history_user_id ON user_role_tariff_history(user_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_events_user_id ON billing_events(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_events_created_at ON billing_events(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_events_provider_event_id
    ON billing_events (provider, event_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created_at ON admin_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_admin_user_id ON admin_audit_log(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_user_app_sessions_user_heartbeat
    ON user_app_sessions(user_id, last_heartbeat_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_app_sessions_heartbeat
    ON user_app_sessions(last_heartbeat_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_app_sessions_open
    ON user_app_sessions(user_id, client_session_id)
    WHERE is_open;

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    channel_id INTEGER,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMPTZ,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('collected', 'created', 'processing', 'ready', 'review', 'deleted')),
    post_type VARCHAR(50),
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    source_platform VARCHAR(10),
    source_id INTEGER,
    source_native_id TEXT,
    platform_texts JSONB DEFAULT '{}',
    videos JSONB DEFAULT '[]',
    extras JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cpost_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    default_platforms JSONB DEFAULT '{"tg": false, "tw": false, "wp": false, "vk": false}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

DO $$ BEGIN
  ALTER TABLE posts ADD COLUMN brand_id INTEGER;
EXCEPTION
  WHEN duplicate_column THEN NULL;
  WHEN undefined_table THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE posts ADD COLUMN channel_id INTEGER;
EXCEPTION
  WHEN duplicate_column THEN NULL;
  WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE posts ADD COLUMN source_native_id TEXT;
EXCEPTION
  WHEN duplicate_column THEN NULL;
  WHEN undefined_table THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE posts ADD COLUMN extras JSONB DEFAULT '{}';
EXCEPTION
  WHEN duplicate_column THEN NULL;
  WHEN undefined_table THEN NULL;
END $$;

WITH ranked AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY user_id, COALESCE(source_platform, ''), source_native_id
           ORDER BY id DESC
         ) AS rn
  FROM posts
  WHERE source_native_id IS NOT NULL
)
UPDATE posts SET source_native_id = NULL
WHERE id IN (SELECT id FROM ranked WHERE rn > 1);

DO $$ BEGIN
  ALTER TABLE posts ADD COLUMN brand_id INTEGER;
EXCEPTION
  WHEN duplicate_column THEN NULL;
  WHEN undefined_table THEN NULL;
END $$;
DO $$ BEGIN
  ALTER TABLE posts ADD COLUMN channel_id INTEGER;
EXCEPTION
  WHEN duplicate_column THEN NULL;
  WHEN undefined_table THEN NULL;
END $$;
CREATE INDEX IF NOT EXISTS idx_posts_user_created ON posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_brand_id ON posts(brand_id) WHERE brand_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_posts_channel_id ON posts(channel_id) WHERE channel_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source ON posts(source_platform, source_id)
    WHERE source_platform IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source_native
    ON posts(user_id, source_platform, source_native_id)
    WHERE source_native_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS post_targets (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('tg', 'vk', 'wp', 'tw', 'threads', 'instagram', 'dzen')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'publishing', 'published', 'failed', 'skipped', 'deleted')),
    publish_at TIMESTAMPTZ,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    result JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_post_targets_post_platform UNIQUE (post_id, platform)
);

CREATE INDEX IF NOT EXISTS idx_post_targets_user_status ON post_targets(user_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_post_targets_claim ON post_targets(platform, status, publish_at) WHERE status IN ('ready', 'publishing');
CREATE INDEX IF NOT EXISTS idx_post_targets_post_id ON post_targets(post_id);

UPDATE posts SET status = 'ready'
 WHERE status IN ('distributed', 'published', 'publishing');
UPDATE posts SET status = 'review'
 WHERE status IS NULL OR status NOT IN ('collected', 'created', 'processing', 'ready', 'review', 'deleted');

DELETE FROM post_targets WHERE platform IN ('url', 'cpost');

UPDATE post_targets AS t
SET status = 'ready', updated_at = CURRENT_TIMESTAMP
FROM posts AS p
WHERE t.post_id = p.id
  AND t.status = 'pending'
  AND p.status = 'ready'
  AND t.platform IN ('tg', 'vk', 'wp', 'tw', 'threads', 'instagram', 'dzen');

ALTER TABLE posts
    DROP COLUMN IF EXISTS to_tg,
    DROP COLUMN IF EXISTS to_tw,
    DROP COLUMN IF EXISTS to_wp,
    DROP COLUMN IF EXISTS to_vk,
    DROP COLUMN IF EXISTS to_dzen,
    DROP COLUMN IF EXISTS to_instagram,
    DROP COLUMN IF EXISTS to_threads;

DO $$
DECLARE rec RECORD;
BEGIN
  FOR rec IN
    SELECT c.conname
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
    WHERE c.conrelid = 'posts'::regclass
      AND c.contype = 'c'
      AND a.attname = 'status'
  LOOP
    EXECUTE 'ALTER TABLE posts DROP CONSTRAINT IF EXISTS ' || quote_ident(rec.conname);
  END LOOP;
END $$;
ALTER TABLE posts DROP CONSTRAINT IF EXISTS posts_status_check;
DO $$ BEGIN
  ALTER TABLE posts ADD CONSTRAINT posts_status_check
    CHECK (status IN ('collected', 'created', 'processing', 'ready', 'review', 'deleted'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
DECLARE rec RECORD;
BEGIN
  FOR rec IN
    SELECT c.conname
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
    WHERE c.conrelid = 'post_targets'::regclass
      AND c.contype = 'c'
      AND a.attname = 'platform'
  LOOP
    EXECUTE 'ALTER TABLE post_targets DROP CONSTRAINT IF EXISTS ' || quote_ident(rec.conname);
  END LOOP;
END $$;
ALTER TABLE post_targets DROP CONSTRAINT IF EXISTS post_targets_platform_check;
DO $$ BEGIN
  ALTER TABLE post_targets ADD CONSTRAINT post_targets_platform_check
    CHECK (platform IN ('tg', 'vk', 'wp', 'tw', 'threads', 'instagram', 'dzen'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DROP TABLE IF EXISTS migration_post_id_map;
DROP FUNCTION IF EXISTS copyparse_notify_collect() CASCADE;
DROP FUNCTION IF EXISTS copyparse_notify_distribute() CASCADE;

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

CREATE TABLE IF NOT EXISTS curl_one_time_done (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    xpath TEXT NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url, xpath)
);
CREATE INDEX IF NOT EXISTS idx_curl_one_time_done_user ON curl_one_time_done(user_id);

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

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    user_id INTEGER,
    type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('bug_report', 'suggestion', 'contact_author')),
    text TEXT NOT NULL,
    email VARCHAR(255),
    user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);

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

DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN created_by_user_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
UPDATE smm_publish_jobs
SET created_by_user_id = COALESCE(assigned_to, user_id)
WHERE created_by_user_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_smm_jobs_created_by
    ON smm_publish_jobs(created_by_user_id)
    WHERE created_by_user_id IS NOT NULL;

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

CREATE INDEX IF NOT EXISTS idx_smm_brands_user_id ON smm_brands(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_brand_channels_brand_id ON smm_brand_channels(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_user_id ON smm_inbox_items(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_brand_status ON smm_inbox_items(brand_id, status);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_brand ON smm_publish_jobs(user_id, brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_automations_user ON smm_automations(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_channel ON smm_competitor_snapshots(channel_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_posted_at
    ON smm_competitor_snapshots (channel_id, posted_at DESC NULLS LAST);

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

CREATE TABLE IF NOT EXISTS smm_ai_usage (
    user_id INTEGER NOT NULL,
    month CHAR(7) NOT NULL,
    calls INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, month)
);

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

DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN tone_of_voice TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN style_notes TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN prompt_snippets JSONB NOT NULL DEFAULT '[]'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE smm_brands ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

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

CREATE TABLE IF NOT EXISTS learn_progress (
    user_id INTEGER NOT NULL,
    slug VARCHAR(128) NOT NULL REFERENCES learn_posts(slug) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_learn_progress_user
    ON learn_progress (user_id);

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

CREATE OR REPLACE FUNCTION copyparse_notify_process() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('copyparse_process', TG_TABLE_NAME);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
;

CREATE OR REPLACE FUNCTION copyparse_notify_publish() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('copyparse_publish', NEW.platform);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
;
DROP TRIGGER IF EXISTS trg_copyparse_notify_process ON posts;

CREATE TRIGGER trg_copyparse_notify_process
AFTER INSERT OR UPDATE OF status ON posts
FOR EACH ROW
WHEN (NEW.status = 'collected')
EXECUTE FUNCTION copyparse_notify_process()
;
DROP TRIGGER IF EXISTS trg_copyparse_notify_collect ON posts;
DROP TRIGGER IF EXISTS trg_copyparse_notify_distribute ON posts;
DROP TRIGGER IF EXISTS trg_copyparse_notify_publish ON post_targets;

CREATE TRIGGER trg_copyparse_notify_publish
AFTER INSERT OR UPDATE OF status ON post_targets
FOR EACH ROW
WHEN (NEW.status = 'ready')
EXECUTE FUNCTION copyparse_notify_publish()
;

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
    proxy_url VARCHAR(512),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

DO $$ BEGIN
  ALTER TABLE tg_profiles ADD COLUMN batch_enrichment_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE tg_profiles ADD COLUMN proxy_url VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

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

CREATE TABLE IF NOT EXISTS tg_summary_cache (
    id SERIAL PRIMARY KEY,
    text_hash VARCHAR(64) NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_summary_cache_expires ON tg_summary_cache(expires_at);

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

CREATE TABLE IF NOT EXISTS vk_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    owner_id VARCHAR(50),
    friends_only BOOLEAN DEFAULT FALSE,
    from_group BOOLEAN DEFAULT FALSE,
    message TEXT,
    attachments TEXT,
    signed BOOLEAN DEFAULT FALSE,
    mark_as_ads BOOLEAN DEFAULT FALSE,
    access_token TEXT,
    user_access_token TEXT,
    groups_to_read JSONB DEFAULT '[]',
    users_to_read JSONB DEFAULT '[]',
    group_to_post VARCHAR(50),
    process_enabled BOOLEAN DEFAULT FALSE,
    processing_description TEXT,
    remove_emojis BOOLEAN DEFAULT FALSE,
    remove_images BOOLEAN DEFAULT FALSE,
    clean_html BOOLEAN DEFAULT FALSE,
    process_services JSONB,
    status_review_after_process BOOLEAN DEFAULT FALSE,
    add_static_html BOOLEAN DEFAULT FALSE,
    static_html_content TEXT,
    post_to_own_wall BOOLEAN DEFAULT FALSE,
    vk_user_id BIGINT,
    vk_app_id VARCHAR(32),
    vk_app_secret VARCHAR(512),
    vk_app_service_key VARCHAR(512),
    vk_frontend_url VARCHAR(512),
    vk_public_gateway_url VARCHAR(512),
    vk_callback_confirmation VARCHAR(64),
    vk_callback_secret VARCHAR(256),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

DO $$ BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_callback_confirmation VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_callback_secret VARCHAR(256);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_app_service_key VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE vk_profiles ALTER COLUMN access_token TYPE TEXT;
EXCEPTION WHEN others THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE vk_profiles ALTER COLUMN user_access_token TYPE TEXT;
EXCEPTION WHEN others THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS wp_publish_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(50) DEFAULT 'on_new_messages',
    time_intervals JSONB DEFAULT '[]',
    site_url TEXT,
    username VARCHAR(255),
    app_password VARCHAR(255),
    publish_all_ready BOOLEAN DEFAULT TRUE,
    publish_limit INTEGER,
    publish_interval_minutes INTEGER,
    process_before_publish BOOLEAN DEFAULT FALSE,
    process_description TEXT,
    remove_emojis BOOLEAN DEFAULT FALSE,
    remove_images BOOLEAN DEFAULT FALSE,
    clean_html BOOLEAN DEFAULT FALSE,
    process_services JSONB,
    status_review_after_process BOOLEAN DEFAULT FALSE,
    add_static_html BOOLEAN DEFAULT FALSE,
    static_html_content TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wp_collect_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    collect_enabled BOOLEAN DEFAULT FALSE,
    collect_all_available BOOLEAN DEFAULT TRUE,
    collect_limit INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wp_collect_sites (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES wp_collect_profile(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    site_url TEXT,
    schedule_type VARCHAR(50) DEFAULT 'on_new_messages',
    time_intervals VARCHAR(5),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_wp_collect_sites_user_id ON wp_collect_sites(user_id);
CREATE INDEX IF NOT EXISTS idx_wp_collect_sites_profile_id ON wp_collect_sites(profile_id);

CREATE TABLE IF NOT EXISTS tw_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    use_proxy BOOLEAN DEFAULT FALSE,
    proxy_user VARCHAR(100),
    proxy_pass VARCHAR(100),
    proxy_host VARCHAR(255),
    proxy_port INTEGER,
    twitter_username VARCHAR(100),
    twitter_password VARCHAR(255),
    twitter_oauth_access_token TEXT,
    twitter_oauth_refresh_token TEXT,
    twitter_oauth_expires_at TIMESTAMPTZ,
    twitter_rest_id VARCHAR(32),
    oauth_pkce_verifier VARCHAR(128),
    oauth_pkce_expires_at TIMESTAMPTZ,
    take_screenshot_collect BOOLEAN DEFAULT FALSE,
    screenshot_xpath TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS instagram_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    username VARCHAR(255),
    password VARCHAR(512),
    usernames_to_read JSONB DEFAULT '[]',
    process_enabled BOOLEAN DEFAULT FALSE,
    processing_description TEXT,
    remove_emojis BOOLEAN DEFAULT FALSE,
    remove_images BOOLEAN DEFAULT FALSE,
    clean_html BOOLEAN DEFAULT FALSE,
    process_services JSONB,
    status_review_after_process BOOLEAN DEFAULT FALSE,
    add_static_html BOOLEAN DEFAULT FALSE,
    static_html_content TEXT,
    instagrapi_session JSONB,
    instagram_verification_code VARCHAR(64),
    instagram_last_auth_error TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS threads_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    access_token VARCHAR(512),
    refresh_token VARCHAR(512),
    token_expires_at TIMESTAMPTZ,
    threads_user_id VARCHAR(100),
    instagram_handle VARCHAR(255),
    process_enabled BOOLEAN DEFAULT FALSE,
    processing_description TEXT,
    remove_emojis BOOLEAN DEFAULT FALSE,
    remove_images BOOLEAN DEFAULT FALSE,
    clean_html BOOLEAN DEFAULT FALSE,
    process_services JSONB,
    status_review_after_process BOOLEAN DEFAULT FALSE,
    add_static_html BOOLEAN DEFAULT FALSE,
    static_html_content TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS threads_selenium_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(40) NOT NULL,
    detail_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_threads_selenium_sessions_user_id ON threads_selenium_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_selenium_sessions_created_at
    ON threads_selenium_sessions(created_at DESC);

CREATE TABLE IF NOT EXISTS schedule_snapshots (
    user_id INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, platform)
);
CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_platform ON schedule_snapshots(platform);

CREATE TABLE IF NOT EXISTS schedule_snapshots_wp (
    user_id INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, platform)
);
CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_wp_user_id ON schedule_snapshots_wp(user_id);
