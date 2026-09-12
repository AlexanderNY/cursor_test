-- Idempotent: roadmap voting tables for existing DBs.
-- Greenfield gets the same DDL via shared.db.schemas.core ALL_TABLES.

CREATE TABLE IF NOT EXISTS roadmap_items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_roadmap_items_active_created
    ON roadmap_items (is_active, created_at DESC);

CREATE TABLE IF NOT EXISTS roadmap_votes (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES roadmap_items(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (item_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_roadmap_votes_item_id ON roadmap_votes(item_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_votes_user_id ON roadmap_votes(user_id);
