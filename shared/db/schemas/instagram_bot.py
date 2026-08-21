"""Instagram bot service DDL."""

from shared.db.generate_ddl import build_post_indexes, build_post_table_ddl

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
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

INSTAGRAM_POSTS_TABLE = build_post_table_ddl(
    "instagram_posts",
    extra_columns={
        "instagram_source_id": "VARCHAR(100)",
        "videos": "JSONB DEFAULT '[]'",
    },
    column_overrides={"to_instagram": "BOOLEAN DEFAULT TRUE"},
)

INSTAGRAM_POSTS_INDEXES = (
    build_post_indexes("instagram_posts", with_user_domain=True)
    + "\nCREATE UNIQUE INDEX IF NOT EXISTS idx_instagram_posts_source "
    "ON instagram_posts(user_id, instagram_source_id) "
    "WHERE instagram_source_id IS NOT NULL;"
)

ALL_TABLES: list[str] = [
    INSTAGRAM_PROFILES_TABLE,
    INSTAGRAM_POSTS_TABLE,
    INSTAGRAM_POSTS_INDEXES,
]
