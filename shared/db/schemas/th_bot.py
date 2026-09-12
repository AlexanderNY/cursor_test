"""Threads bot service DDL."""

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
"""

THREADS_SELENIUM_SESSIONS_TABLE = """
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
"""

ALL_TABLES: list[str] = [
    THREADS_PROFILES_TABLE,
    THREADS_SELENIUM_SESSIONS_TABLE,
]
