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

CREATE TABLE IF NOT EXISTS learn_progress (
    user_id INTEGER NOT NULL,
    slug VARCHAR(128) NOT NULL REFERENCES learn_posts(slug) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_learn_progress_user
    ON learn_progress (user_id);
