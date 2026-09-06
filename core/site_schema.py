"""DDL for 9to18.ru dedicated database (db_9to18)."""

SITE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS site_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    site_role VARCHAR(32) NOT NULL DEFAULT 'user'
        CHECK (site_role IN ('user', 'site_admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_users_email ON site_users (email);
"""

SITE_APPS_TABLE = """
CREATE TABLE IF NOT EXISTS site_apps (
    slug VARCHAR(64) PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    subtitle VARCHAR(255) NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    accent VARCHAR(32) NOT NULL DEFAULT '#2dd4bf',
    emoji VARCHAR(16) NOT NULL DEFAULT '',
    external_href VARCHAR(512) NOT NULL DEFAULT '',
    app_path VARCHAR(255) NOT NULL DEFAULT '',
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SITE_APP_ADMINS_TABLE = """
CREATE TABLE IF NOT EXISTS site_app_admins (
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    app_slug VARCHAR(64) NOT NULL REFERENCES site_apps(slug) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, app_slug)
);
CREATE INDEX IF NOT EXISTS idx_site_app_admins_slug ON site_app_admins (app_slug);
"""

SITE_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS site_posts (
    id SERIAL PRIMARY KEY,
    app_slug VARCHAR(64) NOT NULL REFERENCES site_apps(slug) ON DELETE CASCADE,
    slug VARCHAR(128) NOT NULL,
    title VARCHAR(512) NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (app_slug, slug)
);
CREATE INDEX IF NOT EXISTS idx_site_posts_app ON site_posts (app_slug, published_at DESC);
"""

SITE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS site_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SITE_CONTACTS_TABLE = """
CREATE TABLE IF NOT EXISTS site_contacts (
    id SERIAL PRIMARY KEY,
    app_slug VARCHAR(64) NOT NULL DEFAULT '',
    name VARCHAR(120) NOT NULL DEFAULT '',
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'read', 'done')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_contacts_created ON site_contacts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_site_contacts_app ON site_contacts (app_slug);
"""

SITE_LEARN_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS site_learn_progress (
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    slug VARCHAR(128) NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_site_learn_progress_user ON site_learn_progress (user_id, completed_at DESC);
"""

SITE_PASSWORD_RESET_TABLE = """
CREATE TABLE IF NOT EXISTS site_password_resets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_password_resets_user ON site_password_resets (user_id);
"""

SITE_QUIZ_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS site_quiz_attempts (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    source_type VARCHAR(32) NOT NULL DEFAULT 'post'
        CHECK (source_type IN ('post', 'learn', 'quiz_page')),
    source_key VARCHAR(255) NOT NULL,
    score INT NOT NULL DEFAULT 0,
    total INT NOT NULL DEFAULT 0,
    answers JSONB NOT NULL DEFAULT '[]'::jsonb,
    finished_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_quiz_attempts_user
    ON site_quiz_attempts (user_id, finished_at DESC);
CREATE INDEX IF NOT EXISTS idx_site_quiz_attempts_source
    ON site_quiz_attempts (user_id, source_key);
"""

SITE_ANKI_CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS site_anki_cards (
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    card_id VARCHAR(255) NOT NULL,
    front TEXT NOT NULL DEFAULT '',
    back TEXT NOT NULL DEFAULT '',
    source_key VARCHAR(255) NOT NULL DEFAULT '',
    ease SMALLINT NOT NULL DEFAULT 0,
    interval_days INT NOT NULL DEFAULT 0,
    repetitions INT NOT NULL DEFAULT 0,
    due_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, card_id)
);
CREATE INDEX IF NOT EXISTS idx_site_anki_cards_due
    ON site_anki_cards (user_id, due_at);
"""

# Idempotent patches for already-created DBs (run AFTER CREATE TABLE IF NOT EXISTS)
SITE_SCHEMA_PATCHES: list[str] = [
    """
    ALTER TABLE site_contacts
    ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'new'
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_site_contacts_status ON site_contacts (status)
    """,
]

SITE_ALL_TABLES: list[str] = [
    SITE_USERS_TABLE,
    SITE_APPS_TABLE,
    SITE_APP_ADMINS_TABLE,
    SITE_POSTS_TABLE,
    SITE_SETTINGS_TABLE,
    SITE_CONTACTS_TABLE,
    SITE_LEARN_PROGRESS_TABLE,
    SITE_PASSWORD_RESET_TABLE,
    SITE_QUIZ_ATTEMPTS_TABLE,
    SITE_ANKI_CARDS_TABLE,
]
