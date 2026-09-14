-- Learn (9to18) posts + progress (idempotent).
CREATE TABLE IF NOT EXISTS learn_posts (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(128) UNIQUE NOT NULL,
    episode VARCHAR(32) NOT NULL DEFAULT '',
    title VARCHAR(512) NOT NULL,
    short_title VARCHAR(128) NOT NULL DEFAULT '',
    rubric_id VARCHAR(64) NOT NULL DEFAULT 'architecture',
    sort_order INTEGER NOT NULL DEFAULT 0,
    theory TEXT NOT NULL DEFAULT '',
    lab TEXT NOT NULL DEFAULT '',
    cheatsheet TEXT NOT NULL DEFAULT '',
    diagram TEXT NOT NULL DEFAULT '',
    links JSONB NOT NULL DEFAULT '[]'::jsonb,
    structured JSONB NOT NULL DEFAULT '{}'::jsonb,
    theory_format VARCHAR(16) NOT NULL DEFAULT 'markdown'
        CHECK (theory_format IN ('markdown', 'html')),
    lab_format VARCHAR(16) NOT NULL DEFAULT 'markdown'
        CHECK (lab_format IN ('markdown', 'html')),
    cheatsheet_format VARCHAR(16) NOT NULL DEFAULT 'markdown'
        CHECK (cheatsheet_format IN ('markdown', 'html')),
    profiles JSONB NOT NULL DEFAULT '[]'::jsonb,
    level VARCHAR(16) NOT NULL DEFAULT '',
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    excerpt TEXT NOT NULL DEFAULT '',
    duration_min INTEGER NOT NULL DEFAULT 0,
    prerequisites JSONB NOT NULL DEFAULT '[]'::jsonb,
    author VARCHAR(128) NOT NULL DEFAULT '',
    author_url VARCHAR(512) NOT NULL DEFAULT '',
    cover_url VARCHAR(1024) NOT NULL DEFAULT '',
    seo_title VARCHAR(200) NOT NULL DEFAULT '',
    seo_description VARCHAR(400) NOT NULL DEFAULT '',
    seo_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    canonical_url VARCHAR(512) NOT NULL DEFAULT '',
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_learn_posts_order
    ON learn_posts (sort_order ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_learn_posts_published
    ON learn_posts (published_at);

-- Additive migration for existing DBs (CREATE IF NOT EXISTS does not alter).
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS structured JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS profiles JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS level VARCHAR(16) NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS excerpt TEXT NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS duration_min INTEGER NOT NULL DEFAULT 0;
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS prerequisites JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS author VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS author_url VARCHAR(512) NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS cover_url VARCHAR(1024) NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS seo_title VARCHAR(200) NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS seo_description VARCHAR(400) NOT NULL DEFAULT '';
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS seo_keywords JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE learn_posts
    ADD COLUMN IF NOT EXISTS canonical_url VARCHAR(512) NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS learn_progress (
    user_id INTEGER NOT NULL,
    slug VARCHAR(128) NOT NULL REFERENCES learn_posts(slug) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_learn_progress_user
    ON learn_progress (user_id);
