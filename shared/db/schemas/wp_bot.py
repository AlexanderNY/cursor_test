"""WordPress bot service DDL."""

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
"""

WP_COLLECT_PROFILE_TABLE = """
CREATE TABLE IF NOT EXISTS wp_collect_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    collect_enabled BOOLEAN DEFAULT FALSE,
    collect_all_available BOOLEAN DEFAULT TRUE,
    collect_limit INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

WP_COLLECT_SITES_TABLE = """
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
"""

ALL_TABLES: list[str] = [
    WP_PUBLISH_PROFILE_TABLE,
    WP_COLLECT_PROFILE_TABLE,
    WP_COLLECT_SITES_TABLE,
]
