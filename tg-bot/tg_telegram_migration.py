"""DDL-миграции Telegram roadmap, которые tg-bot применяет при старте."""

TG_TELEGRAM_ROADMAP_MIGRATION: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS tg_events (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        chat_id BIGINT,
        message_id BIGINT,
        event_type VARCHAR(50) NOT NULL,
        rule_id VARCHAR(64),
        matched_conditions JSONB DEFAULT '[]',
        text_hash VARCHAR(64),
        text_preview TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_events_user_created ON tg_events(user_id, created_at);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_events_type_created ON tg_events(event_type, created_at);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_events_hash_chat ON tg_events(text_hash, chat_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_events_rule_created ON tg_events(rule_id, created_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS tg_dedup_cache (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        text_hash VARCHAR(64) NOT NULL,
        chat_id BIGINT NOT NULL,
        rule_id VARCHAR(64),
        channel_to_post VARCHAR(50),
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_dedup_hash_chat ON tg_dedup_cache(text_hash, chat_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_dedup_expires ON tg_dedup_cache(expires_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS tg_summary_cache (
        id SERIAL PRIMARY KEY,
        text_hash VARCHAR(64) NOT NULL UNIQUE,
        summary TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tg_summary_cache_expires ON tg_summary_cache(expires_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS tg_digests (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        chat_id BIGINT NOT NULL,
        digest_text TEXT NOT NULL,
        message_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_posts ADD COLUMN metadata JSONB DEFAULT '{}';
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN summarize_enabled BOOLEAN DEFAULT FALSE;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN summarize_min_length INTEGER DEFAULT 500;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN digest_interval_min INTEGER DEFAULT 30;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN digest_channel VARCHAR(50);
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN classification_enabled BOOLEAN DEFAULT FALSE;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN classification_categories JSONB DEFAULT '["новости", "реклама", "технологии", "финансы", "другое"]';
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
]
