"""SQL-миграции для Collector сервиса.

Collector работает с таблицами posts, tg_posts, wp_posts и др.,
которые создаются в core. Здесь только миграции, специфичные для collector.
"""

# Миграция: добавить source_platform и source_id в таблицу posts
POSTS_SOURCE_MIGRATION = """
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN source_platform VARCHAR(10);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE posts ADD COLUMN source_id INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
"""

# Уникальный индекс для предотвращения дублей при сборе
POSTS_SOURCE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source
    ON posts(source_platform, source_id)
    WHERE source_platform IS NOT NULL;
"""

# Композитные индексы для ускорения запросов collector
POSTS_COMPOSITE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at);
"""

TG_POSTS_COMPOSITE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_tg_posts_status_created ON tg_posts(status, created_at);
"""

WP_POSTS_COMPOSITE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_wp_posts_status_created ON wp_posts(status, created_at);
"""

ALL_TABLES = [
    POSTS_SOURCE_MIGRATION,
    POSTS_SOURCE_INDEX,
    POSTS_COMPOSITE_INDEX,
    TG_POSTS_COMPOSITE_INDEX,
    WP_POSTS_COMPOSITE_INDEX,
]
