"""Схема portfolio-api: публичная страница, материалы и обложки."""

SITE_PORTFOLIOS_TABLE = """
CREATE TABLE IF NOT EXISTS site_portfolios (
    user_id INT PRIMARY KEY REFERENCES site_users(id) ON DELETE CASCADE,
    handle VARCHAR(32) NOT NULL,
    headline VARCHAR(160) NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    pinned_resume_id UUID,
    contact_phone VARCHAR(64) NOT NULL DEFAULT '',
    contact_email VARCHAR(255) NOT NULL DEFAULT '',
    contact_url VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_site_portfolios_handle ON site_portfolios (handle);
"""

SITE_PORTFOLIO_CASES_TABLE = """
CREATE TABLE IF NOT EXISTS site_portfolio_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL REFERENCES site_users(id) ON DELETE CASCADE,
    sort_order INT NOT NULL DEFAULT 0,
    title VARCHAR(160) NOT NULL,
    role_label VARCHAR(120) NOT NULL DEFAULT '',
    problem TEXT NOT NULL DEFAULT '',
    work_text TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT '',
    stack JSONB NOT NULL DEFAULT '[]'::jsonb,
    repo_url VARCHAR(500) NOT NULL DEFAULT '',
    demo_url VARCHAR(500) NOT NULL DEFAULT '',
    learn_slugs JSONB NOT NULL DEFAULT '[]'::jsonb,
    cert_track_id VARCHAR(32) NOT NULL DEFAULT '',
    blurb VARCHAR(400) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_site_portfolio_cases_user
    ON site_portfolio_cases (user_id, sort_order ASC, created_at ASC);
"""

SITE_PORTFOLIO_COVERS_TABLE = """
CREATE TABLE IF NOT EXISTS site_portfolio_covers (
    case_id UUID PRIMARY KEY REFERENCES site_portfolio_cases(id) ON DELETE CASCADE,
    mime VARCHAR(32) NOT NULL,
    content BYTEA NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# Existing databases keep the original CREATE TABLE; these add the new columns.
PORTFOLIO_PATCHES: list[str] = [
    "ALTER TABLE site_portfolios ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(64) NOT NULL DEFAULT ''",
    "ALTER TABLE site_portfolios ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255) NOT NULL DEFAULT ''",
    "ALTER TABLE site_portfolios ADD COLUMN IF NOT EXISTS contact_url VARCHAR(500) NOT NULL DEFAULT ''",
    "ALTER TABLE site_portfolio_cases ADD COLUMN IF NOT EXISTS blurb VARCHAR(400) NOT NULL DEFAULT ''",
]

PORTFOLIO_TABLES: list[str] = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    SITE_PORTFOLIOS_TABLE,
    SITE_PORTFOLIO_CASES_TABLE,
    *PORTFOLIO_PATCHES,
    SITE_PORTFOLIO_COVERS_TABLE,
]
