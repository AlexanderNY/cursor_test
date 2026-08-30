-- Wave 1 ops: contact status, learn progress, password resets (db_9to18)
-- psql -d db_9to18 -f deploy/sql/patch_site_wave1_ops.sql

ALTER TABLE site_contacts
    ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'new';

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
