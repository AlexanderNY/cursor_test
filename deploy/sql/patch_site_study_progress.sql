-- Quiz attempts + Anki card state for 9to18 student cabinet (db_9to18).
-- Also applied at core startup via site_schema.SITE_ALL_TABLES.

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
