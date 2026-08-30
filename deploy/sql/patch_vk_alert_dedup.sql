-- Cursor so alert-only / filtered polls do not re-process the same wall posts
CREATE TABLE IF NOT EXISTS vk_wall_cursors (
    user_id INTEGER NOT NULL,
    domain VARCHAR(255) NOT NULL,
    last_source_id BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, domain)
);

CREATE TABLE IF NOT EXISTS vk_alert_dedup (
    user_id INTEGER NOT NULL,
    rule_id VARCHAR(256) NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, rule_id, text_hash)
);

CREATE INDEX IF NOT EXISTS idx_vk_alert_dedup_created
    ON vk_alert_dedup (created_at);
