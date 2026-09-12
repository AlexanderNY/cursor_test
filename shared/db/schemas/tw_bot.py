"""Twitter/X bot service DDL."""

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
"""

ALL_TABLES: list[str] = [
    TW_PROFILES_TABLE,
]
