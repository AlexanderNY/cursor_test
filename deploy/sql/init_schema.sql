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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

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
        CHECK (role_in_group IN ('admin', 'editor', 'analyst')),
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (group_id, user_id)
);

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

CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(80),
    details_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
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

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    source_platform VARCHAR(10),
    source_id INTEGER,
    platform_texts JSONB DEFAULT '{}',
    videos JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source ON posts(source_platform, source_id)
    WHERE source_platform IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_posts_user_created ON posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);

CREATE TABLE IF NOT EXISTS cpost_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    default_platforms JSONB DEFAULT '{"tg": false, "tw": false, "wp": false, "vk": false}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cpost_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cpost_posts_user_created ON cpost_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cpost_posts_status_created ON cpost_posts(status, created_at);

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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

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
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    posted_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_smm_brands_user_id ON smm_brands(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_brand_channels_brand_id ON smm_brand_channels(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_user_id ON smm_inbox_items(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_brand_status ON smm_inbox_items(brand_id, status);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_brand ON smm_publish_jobs(user_id, brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_automations_user ON smm_automations(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_channel ON smm_competitor_snapshots(channel_id);

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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tg_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    publish_at TIMESTAMPTZ,
    telegram_message_id BIGINT,
    telegram_chat_id TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tg_posts_user_created ON tg_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_posts_status_created ON tg_posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_posts_publish_at ON tg_posts(publish_at);
CREATE INDEX IF NOT EXISTS idx_tg_posts_status_publish_at ON tg_posts(status, publish_at);

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
    access_token VARCHAR(512),
    user_access_token VARCHAR(512),
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
    vk_frontend_url VARCHAR(512),
    vk_public_gateway_url VARCHAR(512),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vk_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    vk_source_id INTEGER,
    attachments JSONB DEFAULT '[]',
    publish_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vk_posts_user_created ON vk_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_vk_posts_status_created ON vk_posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_vk_posts_publish_at ON vk_posts(publish_at);
CREATE INDEX IF NOT EXISTS idx_vk_posts_status_publish_at ON vk_posts(status, publish_at);
CREATE INDEX IF NOT EXISTS idx_vk_posts_user_domain ON vk_posts(user_id, domain);

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

CREATE TABLE IF NOT EXISTS wp_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wp_posts_user_created ON wp_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_wp_posts_status_created ON wp_posts(status, created_at);

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

CREATE TABLE IF NOT EXISTS tw_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tw_posts_user_created ON tw_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tw_posts_status_created ON tw_posts(status, created_at);

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

CREATE TABLE IF NOT EXISTS dzen_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT TRUE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    videos JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dzen_posts_user_created ON dzen_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_dzen_posts_status_created ON dzen_posts(status, created_at);

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

CREATE TABLE IF NOT EXISTS instagram_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT TRUE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    instagram_source_id VARCHAR(100),
    videos JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_instagram_posts_user_created ON instagram_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_instagram_posts_status_created ON instagram_posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_instagram_posts_user_domain ON instagram_posts(user_id, domain);
CREATE UNIQUE INDEX IF NOT EXISTS idx_instagram_posts_source ON instagram_posts(user_id, instagram_source_id) WHERE instagram_source_id IS NOT NULL;

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

CREATE TABLE IF NOT EXISTS threads_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_threads_posts_user_created ON threads_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_threads_posts_status_created ON threads_posts(status, created_at);

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

CREATE TABLE IF NOT EXISTS url_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
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
    status VARCHAR(50) DEFAULT 'collected' CHECK (status IN ('created', 'collected', 'processing', 'ready', 'review', 'publishing', 'published', 'distributed', 'deleted')),
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_url_posts_user_created ON url_posts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_url_posts_status_created ON url_posts(status, created_at);

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
