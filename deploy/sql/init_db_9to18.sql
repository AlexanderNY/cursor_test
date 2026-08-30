-- Database: db_9to18 (9to18.ru site contour — separate from CopyParse db_bot)
-- Create once (as postgres superuser):
--   CREATE DATABASE db_9to18 OWNER postgres ENCODING 'UTF8';
-- Then: psql -d db_9to18 -f deploy/sql/init_db_9to18.sql

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

CREATE TABLE IF NOT EXISTS site_app_admins (
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    app_slug VARCHAR(64) NOT NULL REFERENCES site_apps(slug) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, app_slug)
);
CREATE INDEX IF NOT EXISTS idx_site_app_admins_slug ON site_app_admins (app_slug);

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

-- Promo / feature flags for 9to18 (not CopyParse system_settings)
CREATE TABLE IF NOT EXISTS site_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Anonymous / user contact form (not CopyParse feedback)
CREATE TABLE IF NOT EXISTS site_contacts (
    id SERIAL PRIMARY KEY,
    app_slug VARCHAR(64) NOT NULL DEFAULT '',
    name VARCHAR(120) NOT NULL DEFAULT '',
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_contacts_created ON site_contacts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_site_contacts_app ON site_contacts (app_slug);
CREATE INDEX IF NOT EXISTS idx_site_contacts_status ON site_contacts (status);

CREATE TABLE IF NOT EXISTS site_learn_progress (
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    slug VARCHAR(128) NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_site_learn_progress_user
    ON site_learn_progress (user_id, completed_at DESC);

CREATE TABLE IF NOT EXISTS site_password_resets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_password_resets_user ON site_password_resets (user_id);
