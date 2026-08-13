"""SQL-миграции для Processor сервиса."""

# Миграция: добавить колонку platform_texts в таблицу posts
POSTS_ADD_PLATFORM_TEXTS = """
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN platform_texts JSONB DEFAULT '{}';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Список всех миграций для выполнения при старте
SERVICE_CYCLE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS service_cycle_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    cycle_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ok',
    detail TEXT,
    items_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

ALL_MIGRATIONS = [
    POSTS_ADD_PLATFORM_TEXTS,
    SERVICE_CYCLE_LOG_TABLE,
]
