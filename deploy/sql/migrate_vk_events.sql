-- Journal for VK collect/publish (mirrors tg_events). Safe to re-run.
CREATE TABLE IF NOT EXISTS vk_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    owner_id BIGINT,
    post_id BIGINT,
    event_type VARCHAR(50) NOT NULL,
    rule_id VARCHAR(64),
    matched_conditions JSONB DEFAULT '[]',
    text_hash VARCHAR(64),
    text_preview TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_vk_events_user_created ON vk_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_vk_events_type_created ON vk_events(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_vk_events_hash_owner ON vk_events(text_hash, owner_id);
CREATE INDEX IF NOT EXISTS idx_vk_events_owner_created ON vk_events(owner_id, created_at);
CREATE INDEX IF NOT EXISTS idx_vk_events_user_type_created
    ON vk_events(user_id, event_type, created_at);
