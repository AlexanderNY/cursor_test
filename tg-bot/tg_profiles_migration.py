"""DDL-миграции tg_profiles, которые tg-bot применяет при старте (основные таблицы — в core)."""

TG_PROFILES_ALERT_MIGRATION: list[str] = [
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN alert_enabled BOOLEAN DEFAULT FALSE;
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
    """
    DO $$
    BEGIN
      ALTER TABLE tg_profiles ADD COLUMN alert_rules JSONB DEFAULT '[]';
    EXCEPTION WHEN duplicate_column THEN NULL;
    END $$;
    """,
]
