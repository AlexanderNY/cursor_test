"""Target post contract: hub content in ``posts``, per-network queue in ``post_targets``.

Slice 0 freezes names, statuses, extras JSON, and NOTIFY channels.
Collectors and publishers use this hub + ``post_targets`` only.

Content row (``posts.status``):
    collected → processing → ready | review | deleted
    ``created`` is an inbound alias of ``collected`` (legacy inserts).

Target row (``post_targets.status``):
    pending → ready → publishing → published | failed | skipped | deleted

``posts.extras`` JSONB (inbound / platform-native, not publish outcome)::

    metadata, instagram_source_id, vk_source_id, attachments (collect-time)

``post_targets.result`` JSONB (publish outcome)::

    telegram_message_id, telegram_chat_id, published_vk_post_id,
    published_owner_id, remote_id, error
"""

from __future__ import annotations

from shared.db.generate_ddl import build_add_column_if_missing

POST_PLATFORMS: tuple[str, ...] = (
    "tg",
    "vk",
    "wp",
    "tw",
    "threads",
    "instagram",
    "dzen",
    "url",
    "cpost",
)

PUBLISH_PLATFORMS: tuple[str, ...] = (
    "tg",
    "vk",
    "wp",
    "tw",
    "threads",
    "instagram",
    "dzen",
)

POST_CONTENT_STATUS_VALUES: tuple[str, ...] = (
    "collected",
    "created",
    "processing",
    "ready",
    "review",
    "deleted",
)

POST_TARGET_STATUS_VALUES: tuple[str, ...] = (
    "pending",
    "ready",
    "publishing",
    "published",
    "failed",
    "skipped",
    "deleted",
)

POST_EXTRAS_KEYS: frozenset[str] = frozenset(
    {
        "metadata",
        "instagram_source_id",
        "vk_source_id",
        "attachments",
    }
)

POST_TARGET_RESULT_KEYS: frozenset[str] = frozenset(
    {
        "telegram_message_id",
        "telegram_chat_id",
        "published_vk_post_id",
        "published_owner_id",
        "remote_id",
        "error",
    }
)

NOTIFY_CHANNEL_PUBLISH = "copyparse_publish"

POST_TARGETS_TABLE_NAME = "post_targets"


def _sql_in_check(column: str, values: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"CHECK ({column} IN ({quoted}))"


POST_CONTENT_STATUS_CHECK = _sql_in_check("status", POST_CONTENT_STATUS_VALUES)
POST_TARGET_STATUS_CHECK = _sql_in_check("status", POST_TARGET_STATUS_VALUES)
POST_TARGET_PLATFORM_CHECK = _sql_in_check("platform", PUBLISH_PLATFORMS)


def posts_unified_columns_sql() -> str:
    """ALTER existing ``posts`` so greenfield CREATE and old DBs converge."""
    return "\n".join(
        [
            build_add_column_if_missing("posts", "source_native_id", "TEXT"),
            build_add_column_if_missing("posts", "extras", "JSONB DEFAULT '{}'"),
        ]
    )


def posts_source_native_dedupe_sql() -> str:
    """Null duplicate ``source_native_id`` so the unique index can be created."""
    return """
WITH ranked AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY user_id, COALESCE(source_platform, ''), source_native_id
           ORDER BY id DESC
         ) AS rn
  FROM posts
  WHERE source_native_id IS NOT NULL
)
UPDATE posts SET source_native_id = NULL
WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
""".strip()


def posts_contract_cleanup_sql() -> str:
    """Live DB: drop destination flags, tighten CHECKs, promote publish queue."""
    publish_in = ", ".join(f"'{platform}'" for platform in PUBLISH_PLATFORMS)
    content_in = ", ".join(f"'{status}'" for status in POST_CONTENT_STATUS_VALUES)
    drop_columns = ",\n    ".join(
        f"DROP COLUMN IF EXISTS {name}"
        for name in (
            "to_tg",
            "to_tw",
            "to_wp",
            "to_vk",
            "to_dzen",
            "to_instagram",
            "to_threads",
        )
    )
    return f"""
UPDATE posts SET status = 'ready'
 WHERE status IN ('distributed', 'published', 'publishing');
UPDATE posts SET status = 'review'
 WHERE status IS NULL OR status NOT IN ({content_in});

DELETE FROM post_targets WHERE platform IN ('url', 'cpost');

UPDATE post_targets AS t
SET status = 'ready', updated_at = CURRENT_TIMESTAMP
FROM posts AS p
WHERE t.post_id = p.id
  AND t.status = 'pending'
  AND p.status = 'ready'
  AND t.platform IN ({publish_in});

ALTER TABLE posts
    {drop_columns};

DO $$
DECLARE rec RECORD;
BEGIN
  FOR rec IN
    SELECT c.conname
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
    WHERE c.conrelid = 'posts'::regclass
      AND c.contype = 'c'
      AND a.attname = 'status'
  LOOP
    EXECUTE 'ALTER TABLE posts DROP CONSTRAINT IF EXISTS ' || quote_ident(rec.conname);
  END LOOP;
END $$;
ALTER TABLE posts DROP CONSTRAINT IF EXISTS posts_status_check;
DO $$ BEGIN
  ALTER TABLE posts ADD CONSTRAINT posts_status_check
    CHECK (status IN ({content_in}));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
DECLARE rec RECORD;
BEGIN
  FOR rec IN
    SELECT c.conname
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
    WHERE c.conrelid = 'post_targets'::regclass
      AND c.contype = 'c'
      AND a.attname = 'platform'
  LOOP
    EXECUTE 'ALTER TABLE post_targets DROP CONSTRAINT IF EXISTS ' || quote_ident(rec.conname);
  END LOOP;
END $$;
ALTER TABLE post_targets DROP CONSTRAINT IF EXISTS post_targets_platform_check;
DO $$ BEGIN
  ALTER TABLE post_targets ADD CONSTRAINT post_targets_platform_check
    CHECK (platform IN ({publish_in}));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DROP TABLE IF EXISTS migration_post_id_map;
DROP FUNCTION IF EXISTS copyparse_notify_collect() CASCADE;
DROP FUNCTION IF EXISTS copyparse_notify_distribute() CASCADE;
""".strip()


def post_targets_table_ddl() -> str:
    return f"""
CREATE TABLE IF NOT EXISTS {POST_TARGETS_TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    platform VARCHAR(20) NOT NULL {POST_TARGET_PLATFORM_CHECK},
    status VARCHAR(50) NOT NULL DEFAULT 'pending' {POST_TARGET_STATUS_CHECK},
    publish_at TIMESTAMPTZ,
    target_channels JSONB DEFAULT '[]',
    target_groups JSONB DEFAULT '[]',
    result JSONB DEFAULT '{{}}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_post_targets_post_platform UNIQUE (post_id, platform)
);
""".strip()


def post_targets_indexes_sql() -> str:
    table = POST_TARGETS_TABLE_NAME
    return "\n".join(
        [
            f"CREATE INDEX IF NOT EXISTS idx_{table}_user_status "
            f"ON {table}(user_id, status, created_at);",
            f"CREATE INDEX IF NOT EXISTS idx_{table}_claim "
            f"ON {table}(platform, status, publish_at) "
            f"WHERE status IN ('ready', 'publishing');",
            f"CREATE INDEX IF NOT EXISTS idx_{table}_post_id ON {table}(post_id);",
        ]
    )
