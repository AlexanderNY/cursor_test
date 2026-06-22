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
ALL_MIGRATIONS = [
    POSTS_ADD_PLATFORM_TEXTS,
]
