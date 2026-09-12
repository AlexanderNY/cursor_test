from shared.db.post_columns import POST_BASE_COLUMNS, POST_STATUS_VALUES
from shared.db.post_model import (
    NOTIFY_CHANNEL_PUBLISH,
    POST_CONTENT_STATUS_VALUES,
    POST_EXTRAS_KEYS,
    POST_PLATFORMS,
    POST_TARGET_RESULT_KEYS,
    POST_TARGET_STATUS_VALUES,
    POST_TARGETS_TABLE_NAME,
    PUBLISH_PLATFORMS,
    post_targets_indexes_sql,
    post_targets_table_ddl,
    posts_contract_cleanup_sql,
    posts_unified_columns_sql,
)
from shared.db.queue_notify import queue_notify_statements
from shared.db.schemas.core import ALL_TABLES as CORE_TABLES
from shared.db.schemas.core import POSTS_TABLE
from shared.queue_wakeup import ALLOWED_CHANNELS, CHANNEL_PUBLISH
from shared.status_lease import reclaim_stale_sql


def test_content_statuses_have_no_distributed():
    assert "distributed" not in POST_CONTENT_STATUS_VALUES
    assert POST_STATUS_VALUES == POST_CONTENT_STATUS_VALUES
    assert POST_CONTENT_STATUS_VALUES == (
        "collected",
        "created",
        "processing",
        "ready",
        "review",
        "deleted",
    )
    assert "to_tg" not in POST_BASE_COLUMNS
    assert "to_tg" not in POSTS_TABLE


def test_target_statuses_are_publish_queue():
    assert POST_TARGET_STATUS_VALUES == (
        "pending",
        "ready",
        "publishing",
        "published",
        "failed",
        "skipped",
        "deleted",
    )


def test_publish_platforms_subset_of_post_platforms():
    assert set(PUBLISH_PLATFORMS) <= set(POST_PLATFORMS)
    assert "cpost" not in PUBLISH_PLATFORMS
    assert "url" not in PUBLISH_PLATFORMS


def test_posts_greenfield_ddl_has_unified_columns():
    assert "source_native_id" in POSTS_TABLE
    assert "extras" in POSTS_TABLE
    assert "platform_texts" in POSTS_TABLE


def test_posts_unified_migration_is_idempotent_alter():
    sql = posts_unified_columns_sql()
    assert "source_native_id" in sql
    assert "extras" in sql
    assert "duplicate_column" in sql


def test_posts_contract_cleanup_drops_flags_and_hub_only_platforms():
    sql = posts_contract_cleanup_sql()
    assert "DROP COLUMN IF EXISTS to_tg" in sql
    assert "DELETE FROM post_targets WHERE platform IN ('url', 'cpost')" in sql
    assert "DROP TABLE IF EXISTS migration_post_id_map" in sql
    assert "DROP FUNCTION IF EXISTS copyparse_notify_collect()" in sql


def test_post_targets_ddl_fk_unique_and_checks():
    ddl = post_targets_table_ddl()
    assert f"CREATE TABLE IF NOT EXISTS {POST_TARGETS_TABLE_NAME}" in ddl
    assert "REFERENCES posts(id) ON DELETE CASCADE" in ddl
    assert "UNIQUE (post_id, platform)" in ddl
    for platform in PUBLISH_PLATFORMS:
        assert f"'{platform}'" in ddl
    assert "'url'" not in ddl
    assert "'cpost'" not in ddl
    for status in POST_TARGET_STATUS_VALUES:
        assert f"'{status}'" in ddl
    indexes = post_targets_indexes_sql()
    assert "WHERE status IN ('ready', 'publishing')" in indexes


def test_extras_and_result_keys_are_disjoint():
    assert POST_EXTRAS_KEYS.isdisjoint(POST_TARGET_RESULT_KEYS)
    assert "instagram_source_id" in POST_EXTRAS_KEYS
    assert "telegram_message_id" in POST_TARGET_RESULT_KEYS


def test_core_schema_includes_post_targets_before_notify():
    blob = "\n".join(CORE_TABLES)
    assert POST_TARGETS_TABLE_NAME in blob
    assert "copyparse_notify_publish" in blob
    targets_at = blob.index("CREATE TABLE IF NOT EXISTS post_targets")
    notify_at = blob.index("copyparse_notify_publish")
    assert targets_at < notify_at


def test_queue_notify_publish_channel_on_targets():
    blob = "\n".join(queue_notify_statements())
    assert NOTIFY_CHANNEL_PUBLISH in blob
    assert CHANNEL_PUBLISH == NOTIFY_CHANNEL_PUBLISH
    assert CHANNEL_PUBLISH in ALLOWED_CHANNELS
    assert f"ON {POST_TARGETS_TABLE_NAME}" in blob
    assert "PERFORM pg_notify('copyparse_collect'" not in blob
    assert "PERFORM pg_notify('copyparse_distribute'" not in blob
    assert "CREATE OR REPLACE FUNCTION copyparse_notify_collect" not in blob
    assert "CREATE OR REPLACE FUNCTION copyparse_notify_distribute" not in blob
    assert "CREATE TRIGGER trg_copyparse_notify_collect" not in blob
    assert "CREATE TRIGGER trg_copyparse_notify_distribute" not in blob


def test_reclaim_stale_sql_accepts_post_targets():
    sql = reclaim_stale_sql(
        POST_TARGETS_TABLE_NAME,
        from_status="publishing",
        to_status="ready",
        older_than_minutes=5,
    )
    assert f"UPDATE {POST_TARGETS_TABLE_NAME}" in sql
    assert "%s" in sql
    assert "publishing" not in sql
