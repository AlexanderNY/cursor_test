"""SQL-определения таблиц для Core сервиса."""

# Таблица posts - общая для всех постов
POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: добавить source_platform и source_id для трассировки collector
POSTS_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN source_platform VARCHAR(10);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN source_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN to_threads BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN platform_texts JSONB DEFAULT '{}';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN videos JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Индексы для posts
POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source ON posts(source_platform, source_id) WHERE source_platform IS NOT NULL;
"""

# Таблица tg_profiles - настройки Telegram по пользователям
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
    alert_enabled BOOLEAN DEFAULT FALSE,
    alert_rules JSONB DEFAULT '[]',
    process_enabled BOOLEAN DEFAULT FALSE,
    processing_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: добавить колонки для обработки в tg_profiles
TG_PROFILES_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN remove_emojis BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN remove_images BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN clean_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN process_services JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN status_review_after_process BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN add_static_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN static_html_content TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN telegram_username VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN auth_state VARCHAR(50) DEFAULT 'authorized';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN auth_phone_code_hash VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN auth_phone_number VARCHAR(50);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN alert_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN alert_rules JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица tw_profiles - настройки Twitter
TW_PROFILES_TABLE = """
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: OAuth X (Twitter), скриншоты при сборе, PKCE
TW_PROFILES_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN twitter_oauth_access_token TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN twitter_oauth_refresh_token TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN twitter_oauth_expires_at TIMESTAMP;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN twitter_rest_id VARCHAR(32);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN oauth_pkce_verifier VARCHAR(128);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN oauth_pkce_expires_at TIMESTAMP;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN take_screenshot_collect BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_profiles ADD COLUMN screenshot_xpath TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица wp_profiles - настройки WordPress (legacy, оставлена для совместимости)
WP_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS wp_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    site_url TEXT,
    username VARCHAR(255),
    app_password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Таблица wp_publish_profile - настройки публикации WordPress
WP_PUBLISH_PROFILE_TABLE = """
CREATE TABLE IF NOT EXISTS wp_publish_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(50) DEFAULT 'on_new_messages',
    time_intervals JSONB DEFAULT '[]',
    site_url TEXT,
    username VARCHAR(255),
    app_password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: добавить колонки publish_all_ready, publish_limit, publish_interval_minutes, process_before_publish, process_description
WP_PUBLISH_PROFILE_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN publish_all_ready BOOLEAN DEFAULT TRUE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN publish_limit INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN publish_interval_minutes INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN process_before_publish BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN process_description TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN remove_emojis BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN remove_images BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN clean_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN process_services JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN status_review_after_process BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN add_static_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_publish_profile ADD COLUMN static_html_content TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица wp_collect_profile - настройки сбора (parser) WordPress
WP_COLLECT_PROFILE_TABLE = """
CREATE TABLE IF NOT EXISTS wp_collect_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    collect_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: добавить колонки collect_all_available, collect_limit
WP_COLLECT_PROFILE_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE wp_collect_profile ADD COLUMN collect_all_available BOOLEAN DEFAULT TRUE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_collect_profile ADD COLUMN collect_limit INTEGER DEFAULT 1;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица wp_collect_sites - сайты сбора по пользователю (столбцы site_url, schedule_type, time_intervals)
WP_COLLECT_SITES_TABLE = """
CREATE TABLE IF NOT EXISTS wp_collect_sites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES wp_collect_profile(user_id) ON DELETE CASCADE,
    site_url TEXT,
    schedule_type VARCHAR(50) DEFAULT 'on_new_messages',
    time_intervals VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
WP_COLLECT_SITES_INDEX = """
CREATE INDEX IF NOT EXISTS idx_wp_collect_sites_user_id ON wp_collect_sites(user_id);
"""

# Таблица wp_posts - посты WordPress (структура аналогична posts)
WP_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS wp_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для wp_posts
WP_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_wp_posts_user_id ON wp_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_wp_posts_status ON wp_posts(status);
CREATE INDEX IF NOT EXISTS idx_wp_posts_created_at ON wp_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_wp_posts_status_created ON wp_posts(status, created_at);
"""

# Таблица tg_posts - посты Telegram (структура аналогична wp_posts)
TG_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS tg_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для tg_posts
TG_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_tg_posts_user_id ON tg_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_tg_posts_status ON tg_posts(status);
CREATE INDEX IF NOT EXISTS idx_tg_posts_created_at ON tg_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_tg_posts_status_created ON tg_posts(status, created_at);
"""

# Миграция: metadata для AI-enrichment в tg_posts
TG_POSTS_TELEGRAM_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN metadata JSONB DEFAULT '{}';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Миграция SMM: отложенный постинг, multi-channel, telegram ids
TG_POSTS_SMM_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN publish_at TIMESTAMPTZ;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN telegram_message_id BIGINT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN telegram_chat_id VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_posts ALTER COLUMN telegram_chat_id TYPE TEXT;
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN target_channels JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
CREATE INDEX IF NOT EXISTS idx_tg_posts_publish_at ON tg_posts(publish_at);
CREATE INDEX IF NOT EXISTS idx_tg_posts_status_publish_at ON tg_posts(status, publish_at);
"""

TG_PROFILES_SMM_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN channels_to_post JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

TG_POST_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS tg_post_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    hashtags TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tg_post_templates_user ON tg_post_templates(user_id);
"""

# Миграция: AI и digest настройки в tg_profiles
TG_PROFILES_TELEGRAM_AI_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN summarize_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN summarize_min_length INTEGER DEFAULT 500;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN digest_interval_min INTEGER DEFAULT 30;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN digest_channel VARCHAR(50);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN classification_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tg_profiles ADD COLUMN classification_categories JSONB DEFAULT '["новости", "реклама", "технологии", "финансы", "другое"]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Журнал событий Telegram (сбор, алерты, подавления)
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

TG_EVENTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_tg_events_user_created ON tg_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_events_type_created ON tg_events(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_tg_events_hash_chat ON tg_events(text_hash, chat_id);
CREATE INDEX IF NOT EXISTS idx_tg_events_rule_created ON tg_events(rule_id, created_at);
"""

# Журнал циклов scheduler / collector / processor (диагностика Administration → Posts)
SERVICE_CYCLE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS service_cycle_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    cycle_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ok',
    detail TEXT,
    items_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SERVICE_CYCLE_LOG_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_service_cycle_log_created ON service_cycle_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service_cycle_log_service_created ON service_cycle_log(service_name, created_at DESC);
"""

# Кэш дедупликации алертов
TG_DEDUP_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS tg_dedup_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    chat_id BIGINT NOT NULL,
    rule_id VARCHAR(64),
    channel_to_post VARCHAR(50),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

TG_DEDUP_CACHE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_tg_dedup_hash_chat ON tg_dedup_cache(text_hash, chat_id);
CREATE INDEX IF NOT EXISTS idx_tg_dedup_expires ON tg_dedup_cache(expires_at);
"""

# Кэш AI-суммаризаций
TG_SUMMARY_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS tg_summary_cache (
    id SERIAL PRIMARY KEY,
    text_hash VARCHAR(64) NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

TG_SUMMARY_CACHE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_tg_summary_cache_expires ON tg_summary_cache(expires_at);
"""

# Дайджесты по каналам
TG_DIGESTS_TABLE = """
CREATE TABLE IF NOT EXISTS tg_digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chat_id BIGINT NOT NULL,
    digest_text TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

TG_DIGESTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_tg_digests_user_created ON tg_digests(user_id, created_at);
"""

# Очередь AI-задач (batch)
AI_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS ai_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payload JSONB DEFAULT '{}',
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
"""

AI_TASKS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_ai_tasks_status_created ON ai_tasks(status, created_at);
"""

# Таблица vk_profiles - настройки VKontakte
VK_PROFILES_TABLE = """
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: access_token, groups_to_read, group_to_post для vk_profiles (сбор и публикация)
VK_PROFILES_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN access_token VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN groups_to_read JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN group_to_post VARCHAR(50);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN process_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN processing_description TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN remove_emojis BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN remove_images BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN clean_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN process_services JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN status_review_after_process BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN add_static_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN static_html_content TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN post_to_own_wall BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN users_to_read JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Пользовательский OAuth-токен для загрузки фото/доков на стену группы (photos.getWallUploadServer недоступен с групповым токеном)
VK_PROFILES_USER_ACCESS_TOKEN_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN user_access_token VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# VK ID пользователя после OAuth (для отображения в UI)
VK_PROFILES_VK_USER_ID_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_user_id BIGINT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

VK_PROFILES_OAUTH_APP_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_app_id VARCHAR(32);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_app_secret VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_frontend_url VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_profiles ADD COLUMN vk_public_gateway_url VARCHAR(512);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица vk_posts - посты VKontakte (структура аналогична tg_posts)
VK_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS vk_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    vk_source_id INTEGER,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для vk_posts
VK_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_vk_posts_user_id ON vk_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_vk_posts_status ON vk_posts(status);
CREATE INDEX IF NOT EXISTS idx_vk_posts_created_at ON vk_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_vk_posts_status_created ON vk_posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_vk_posts_user_domain ON vk_posts(user_id, domain);
"""

# Миграция: vk_source_id для дедупликации постов из VK API; attachments для расширенных вложений
VK_POSTS_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN vk_source_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN attachments JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица url_posts - посты из url-bot (структура как tg_posts)
URL_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS url_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для url_posts
URL_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_url_posts_user_id ON url_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_url_posts_status ON url_posts(status);
CREATE INDEX IF NOT EXISTS idx_url_posts_created_at ON url_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_url_posts_status_created ON url_posts(status, created_at);
"""

# Таблица threads_profiles - настройки Threads (Meta OAuth, публикация, сбор, обработка)
THREADS_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS threads_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    publish_enabled BOOLEAN DEFAULT FALSE,
    collect_enabled BOOLEAN DEFAULT FALSE,
    schedule_type VARCHAR(20) DEFAULT 'immediate',
    time_intervals JSONB DEFAULT '[]',
    access_token VARCHAR(512),
    refresh_token VARCHAR(512),
    token_expires_at TIMESTAMP,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Таблица threads_posts - посты Threads (структура аналогична tg_posts)
THREADS_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS threads_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для threads_posts
THREADS_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_threads_posts_user_id ON threads_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_posts_status ON threads_posts(status);
CREATE INDEX IF NOT EXISTS idx_threads_posts_created_at ON threads_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_threads_posts_status_created ON threads_posts(status, created_at);
"""

# Миграция: to_threads для существующих таблиц постов
TO_THREADS_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN to_threads BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_posts ADD COLUMN to_threads BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN to_threads BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE url_posts ADD COLUMN to_threads BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Миграция: instagram_handle для threads_profiles (отображаемый @username, без пароля)
THREADS_PROFILES_INSTAGRAM_HANDLE_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE threads_profiles ADD COLUMN instagram_handle VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Диагностические сессии Selenium (Meta web login) — не заменяют OAuth Graph token
THREADS_SELENIUM_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS threads_selenium_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(40) NOT NULL,
    detail_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

THREADS_SELENIUM_SESSIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_threads_selenium_sessions_user_id ON threads_selenium_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_selenium_sessions_created_at ON threads_selenium_sessions(created_at DESC);
"""

# Таблица dzen_profiles - настройки Яндекс Дзен
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: rss_token для dzen_profiles (если таблица создана без него)
DZEN_PROFILES_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE dzen_profiles ADD COLUMN rss_token VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Selenium: Яндекс-логин, URL студии, режим сбора (rss / selenium / both)
DZEN_PROFILES_SELENIUM_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE dzen_profiles ADD COLUMN yandex_login VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE dzen_profiles ADD COLUMN yandex_password TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE dzen_profiles ADD COLUMN dzen_studio_url TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE dzen_profiles ADD COLUMN collect_source VARCHAR(20) DEFAULT 'rss';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE dzen_profiles ADD COLUMN last_auth_error TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица dzen_posts - посты Дзен (структура как vk_posts + videos)
DZEN_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS dzen_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    videos JSONB DEFAULT '[]',
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT TRUE,
    to_threads BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для dzen_posts
DZEN_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_dzen_posts_user_id ON dzen_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_dzen_posts_status ON dzen_posts(status);
CREATE INDEX IF NOT EXISTS idx_dzen_posts_created_at ON dzen_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_dzen_posts_status_created ON dzen_posts(status, created_at);
"""

# Миграция: to_dzen для существующих таблиц постов (posts.to_dzen уже в POSTS_MIGRATION)
TO_DZEN_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE url_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE threads_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE cpost_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE instagram_posts ADD COLUMN to_dzen BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица instagram_profiles - настройки Instagram (instagrapi)
INSTAGRAM_PROFILES_TABLE = """
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: сессия instagrapi и код 2FA в instagram_profiles
INSTAGRAM_PROFILES_SESSION_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE instagram_profiles ADD COLUMN instagrapi_session JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE instagram_profiles ADD COLUMN instagram_verification_code VARCHAR(64);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE instagram_profiles ADD COLUMN instagram_last_auth_error TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица instagram_posts - посты Instagram (структура как vk_posts + instagram_source_id, to_instagram, videos)
INSTAGRAM_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS instagram_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    instagram_source_id VARCHAR(100),
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    videos JSONB DEFAULT '[]',
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для instagram_posts
INSTAGRAM_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_instagram_posts_user_id ON instagram_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_instagram_posts_status ON instagram_posts(status);
CREATE INDEX IF NOT EXISTS idx_instagram_posts_created_at ON instagram_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_instagram_posts_status_created ON instagram_posts(status, created_at);
CREATE INDEX IF NOT EXISTS idx_instagram_posts_user_domain ON instagram_posts(user_id, domain);
CREATE UNIQUE INDEX IF NOT EXISTS idx_instagram_posts_source ON instagram_posts(user_id, instagram_source_id) WHERE instagram_source_id IS NOT NULL;
"""

# Миграция: to_instagram для существующих таблиц постов
TO_INSTAGRAM_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE tg_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE wp_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE url_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE dzen_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE threads_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE tw_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE cpost_posts ADD COLUMN to_instagram BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица curl_settings - настройки cURL скрапинга
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Миграция: urls (JSONB) и колонки обработки для curl_settings
CURL_SETTINGS_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN urls JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN process_before_publish BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN process_description TEXT;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN remove_emojis BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN remove_images BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN clean_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN process_services JSONB;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN status_review_after_process BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN add_static_html BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN static_html_content VARCHAR(1000);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE curl_settings ADD COLUMN screenshot_only BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица curl_one_time_done - выполненные одноразовые URL (user_id, url, xpath)
CURL_ONE_TIME_DONE_TABLE = """
CREATE TABLE IF NOT EXISTS curl_one_time_done (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    xpath TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url, xpath)
);
CREATE INDEX IF NOT EXISTS idx_curl_one_time_done_user ON curl_one_time_done(user_id);
"""

# Таблица cpost_profiles - настройки ручных постов
CPOST_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS cpost_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    default_platforms JSONB DEFAULT '{"tg": false, "tw": false, "wp": false, "vk": false}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Таблица cpost_posts - ручные посты (источник до collector -> posts)
CPOST_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS cpost_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CPOST_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_cpost_posts_user_id ON cpost_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_cpost_posts_status ON cpost_posts(status);
CREATE INDEX IF NOT EXISTS idx_cpost_posts_created_at ON cpost_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_cpost_posts_status_created ON cpost_posts(status, created_at);
"""

# Таблица tw_posts - посты Twitter (источник до collector -> posts)
TW_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS tw_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    domain VARCHAR(255),
    url TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    avatar TEXT,
    post_date TIMESTAMP,
    post_text TEXT,
    screenshot TEXT,
    images JSONB DEFAULT '[]',
    image_over_text TEXT,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    is_ad BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'collected',
    post_type VARCHAR(50),
    to_tg BOOLEAN DEFAULT FALSE,
    to_tw BOOLEAN DEFAULT FALSE,
    to_wp BOOLEAN DEFAULT FALSE,
    to_vk BOOLEAN DEFAULT FALSE,
    to_dzen BOOLEAN DEFAULT FALSE,
    to_instagram BOOLEAN DEFAULT FALSE,
    to_threads BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

TW_POSTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_tw_posts_user_id ON tw_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_tw_posts_status ON tw_posts(status);
CREATE INDEX IF NOT EXISTS idx_tw_posts_created_at ON tw_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_tw_posts_status_created ON tw_posts(status, created_at);
"""

# Таблица notifications - уведомления для всех пользователей
NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    user_id INTEGER,
    type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Индексы для notifications
NOTIFICATIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
"""

# Миграция: добавить user_id и type в notifications
NOTIFICATIONS_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE notifications ADD COLUMN user_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE notifications ADD COLUMN type VARCHAR(50) DEFAULT 'general';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Таблица feedback - обратная связь от пользователей
FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('bug_report', 'suggestion', 'contact_author')),
    text TEXT NOT NULL,
    email VARCHAR(255),
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

FEEDBACK_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);
"""

# Глобальные runtime-настройки (ключ → JSON value)
SYSTEM_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SYSTEM_SETTINGS_SEED = """
INSERT INTO system_settings (key, value)
VALUES ('ai_enabled', 'true'::jsonb)
ON CONFLICT (key) DO NOTHING;
"""

# Список всех таблиц для инициализации
# SMM: brands, channels, inbox, publish jobs, automations, competitor snapshots
SMM_BRANDS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_brands (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brand_id, network, external_id)
);
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
        CHECK (status IN ('new', 'read', 'replied', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SMM_AUTOMATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS smm_automations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER REFERENCES smm_brands(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('rss', 'tg_repost', 'mention')),
    config JSONB NOT NULL DEFAULT '{}',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SMM_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_smm_brands_user_id ON smm_brands(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_brand_channels_brand_id ON smm_brand_channels(brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_user_id ON smm_inbox_items(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_inbox_brand_status ON smm_inbox_items(brand_id, status);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_user_brand ON smm_publish_jobs(user_id, brand_id);
CREATE INDEX IF NOT EXISTS idx_smm_jobs_publish_at ON smm_publish_jobs(publish_at);
CREATE INDEX IF NOT EXISTS idx_smm_automations_user ON smm_automations(user_id);
CREATE INDEX IF NOT EXISTS idx_smm_competitor_channel ON smm_competitor_snapshots(channel_id);
"""

SMM_OPS_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN publish_enabled BOOLEAN DEFAULT TRUE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN collect_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_inbox_items ADD COLUMN external_msg_id VARCHAR(128);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_inbox_items ADD COLUMN edited_text TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN retry_count INTEGER DEFAULT 0;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_publish_jobs ADD COLUMN last_error TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE UNIQUE INDEX IF NOT EXISTS idx_smm_inbox_dedup
  ON smm_inbox_items (user_id, network, external_msg_id)
  WHERE external_msg_id IS NOT NULL;
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
CREATE INDEX IF NOT EXISTS idx_smm_channel_counters_user_day
  ON smm_channel_counters(user_id, day);
CREATE TABLE IF NOT EXISTS smm_ai_usage (
    user_id INTEGER NOT NULL,
    month CHAR(7) NOT NULL,
    calls INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, month)
);
"""

SMM_COMMENTS_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN discussion_external_id VARCHAR(128);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN discussion_title VARCHAR(255);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN comments_collect_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_smm_channels_discussion
  ON smm_brand_channels (network, discussion_external_id)
  WHERE discussion_external_id IS NOT NULL;
DO $$ BEGIN
  ALTER TABLE smm_inbox_items ADD COLUMN meta JSONB DEFAULT '{}'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
ALTER TABLE smm_inbox_items DROP CONSTRAINT IF EXISTS smm_inbox_items_status_check;
ALTER TABLE smm_inbox_items ADD CONSTRAINT smm_inbox_items_status_check
  CHECK (status IN ('new', 'read', 'replied', 'archived', 'reply_failed', 'in_progress'));
"""

SMM_CHANNEL_FLOW_MIGRATION = """
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN alert_enabled BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN save_conditions JSONB DEFAULT '[]'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN processing JSONB DEFAULT '{}'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN alert_delivery JSONB DEFAULT '{}'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE smm_brand_channels ADD COLUMN alert_rules JSONB DEFAULT '[]'::jsonb;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_smm_channels_tg_external
  ON smm_brand_channels (network, external_id)
  WHERE network = 'tg';
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_guide_blocks_sort ON guide_blocks(sort_order);
"""

VK_POSTS_PUBLISH_AT_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN publish_at TIMESTAMPTZ;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE vk_posts ADD COLUMN target_groups JSONB DEFAULT '[]';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
CREATE INDEX IF NOT EXISTS idx_vk_posts_publish_at ON vk_posts(publish_at);
"""

# Brand destination overrides: конкретные TG-каналы / VK-группы для публикации
TARGET_DESTINATIONS_MIGRATION = """
DO $$ BEGIN ALTER TABLE posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE cpost_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE cpost_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE tg_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE tg_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE vk_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE vk_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE wp_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE wp_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE tw_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE tw_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE threads_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE threads_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE dzen_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE dzen_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE instagram_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE instagram_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE url_posts ADD COLUMN target_channels JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE url_posts ADD COLUMN target_groups JSONB DEFAULT '[]'; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
"""

ALL_TABLES = [
    POSTS_TABLE,
    POSTS_MIGRATION,
    POSTS_INDEXES,
    TG_PROFILES_TABLE,
    TG_PROFILES_MIGRATION,
    TG_POSTS_TABLE,
    TG_POSTS_INDEXES,
    TG_POSTS_TELEGRAM_MIGRATION,
    TG_POSTS_SMM_MIGRATION,
    TG_PROFILES_TELEGRAM_AI_MIGRATION,
    TG_PROFILES_SMM_MIGRATION,
    TG_POST_TEMPLATES_TABLE,
    TG_EVENTS_TABLE,
    TG_EVENTS_INDEXES,
    SERVICE_CYCLE_LOG_TABLE,
    SERVICE_CYCLE_LOG_INDEXES,
    TG_DEDUP_CACHE_TABLE,
    TG_DEDUP_CACHE_INDEXES,
    TG_SUMMARY_CACHE_TABLE,
    TG_SUMMARY_CACHE_INDEXES,
    TG_DIGESTS_TABLE,
    TG_DIGESTS_INDEXES,
    AI_TASKS_TABLE,
    AI_TASKS_INDEXES,
    TW_PROFILES_TABLE,
    TW_PROFILES_MIGRATION,
    WP_PROFILES_TABLE,
    WP_PUBLISH_PROFILE_TABLE,
    WP_PUBLISH_PROFILE_MIGRATION,
    WP_COLLECT_PROFILE_TABLE,
    WP_COLLECT_PROFILE_MIGRATION,
    WP_COLLECT_SITES_TABLE,
    WP_COLLECT_SITES_INDEX,
    WP_POSTS_TABLE,
    WP_POSTS_INDEXES,
    VK_PROFILES_TABLE,
    VK_PROFILES_MIGRATION,
    VK_PROFILES_USER_ACCESS_TOKEN_MIGRATION,
    VK_PROFILES_VK_USER_ID_MIGRATION,
    VK_PROFILES_OAUTH_APP_MIGRATION,
    VK_POSTS_TABLE,
    VK_POSTS_INDEXES,
    VK_POSTS_MIGRATION,
    URL_POSTS_TABLE,
    URL_POSTS_INDEXES,
    THREADS_PROFILES_TABLE,
    THREADS_POSTS_TABLE,
    THREADS_POSTS_INDEXES,
    TO_THREADS_MIGRATION,
    THREADS_PROFILES_INSTAGRAM_HANDLE_MIGRATION,
    THREADS_SELENIUM_SESSIONS_TABLE,
    THREADS_SELENIUM_SESSIONS_INDEXES,
    DZEN_PROFILES_TABLE,
    DZEN_PROFILES_MIGRATION,
    DZEN_PROFILES_SELENIUM_MIGRATION,
    DZEN_POSTS_TABLE,
    DZEN_POSTS_INDEXES,
    TO_DZEN_MIGRATION,
    INSTAGRAM_PROFILES_TABLE,
    INSTAGRAM_PROFILES_SESSION_MIGRATION,
    INSTAGRAM_POSTS_TABLE,
    INSTAGRAM_POSTS_INDEXES,
    TO_INSTAGRAM_MIGRATION,
    CURL_SETTINGS_TABLE,
    CURL_SETTINGS_MIGRATION,
    CURL_ONE_TIME_DONE_TABLE,
    CPOST_PROFILES_TABLE,
    CPOST_POSTS_TABLE,
    CPOST_POSTS_INDEXES,
    TW_POSTS_TABLE,
    TW_POSTS_INDEXES,
    NOTIFICATIONS_TABLE,
    NOTIFICATIONS_MIGRATION,
    NOTIFICATIONS_INDEXES,
    FEEDBACK_TABLE,
    FEEDBACK_INDEXES,
    SYSTEM_SETTINGS_TABLE,
    SYSTEM_SETTINGS_SEED,
    SMM_BRANDS_TABLE,
    SMM_BRAND_CHANNELS_TABLE,
    SMM_INBOX_TABLE,
    SMM_JOBS_TABLE,
    SMM_AUTOMATIONS_TABLE,
    SMM_COMPETITOR_SNAPSHOTS_TABLE,
    SMM_INDEXES,
    SMM_OPS_MIGRATION,
    SMM_COMMENTS_MIGRATION,
    SMM_CHANNEL_FLOW_MIGRATION,
    GUIDE_BLOCKS_TABLE,
    VK_POSTS_PUBLISH_AT_MIGRATION,
    TARGET_DESTINATIONS_MIGRATION,
]
