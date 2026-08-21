"""VK bot service DDL."""

from shared.db.generate_ddl import build_post_indexes, build_post_table_ddl

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
"""

VK_POSTS_TABLE = build_post_table_ddl(
    "vk_posts",
    extra_columns={
        "vk_source_id": "INTEGER",
        "attachments": "JSONB DEFAULT '[]'",
        "publish_at": "TIMESTAMPTZ",
    },
)

VK_POSTS_INDEXES = build_post_indexes(
    "vk_posts",
    with_publish_at=True,
    with_user_domain=True,
)

ALL_TABLES: list[str] = [
    VK_PROFILES_TABLE,
    VK_POSTS_TABLE,
    VK_POSTS_INDEXES,
]
