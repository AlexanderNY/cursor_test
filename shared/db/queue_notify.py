"""DDL: NOTIFY collector/processor/distribute/publish when queue statuses change."""

from __future__ import annotations

from shared.db.post_model import NOTIFY_CHANNEL_PUBLISH, POST_TARGETS_TABLE_NAME

SOURCE_NOTIFY_TABLES: tuple[str, ...] = ()

NOTIFY_FUNCTIONS_SQL: tuple[str, ...] = (
    """
CREATE OR REPLACE FUNCTION copyparse_notify_process() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('copyparse_process', TG_TABLE_NAME);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
""",
    f"""
CREATE OR REPLACE FUNCTION copyparse_notify_publish() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('{NOTIFY_CHANNEL_PUBLISH}', NEW.platform);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
""",
)


def build_trigger_statements() -> list[str]:
    return [
        "DROP TRIGGER IF EXISTS trg_copyparse_notify_process ON posts",
        """
CREATE TRIGGER trg_copyparse_notify_process
AFTER INSERT OR UPDATE OF status ON posts
FOR EACH ROW
WHEN (NEW.status = 'collected')
EXECUTE FUNCTION copyparse_notify_process()
""",
        "DROP TRIGGER IF EXISTS trg_copyparse_notify_collect ON posts",
        "DROP TRIGGER IF EXISTS trg_copyparse_notify_distribute ON posts",
        f"DROP TRIGGER IF EXISTS trg_copyparse_notify_publish ON {POST_TARGETS_TABLE_NAME}",
        f"""
CREATE TRIGGER trg_copyparse_notify_publish
AFTER INSERT OR UPDATE OF status ON {POST_TARGETS_TABLE_NAME}
FOR EACH ROW
WHEN (NEW.status = 'ready')
EXECUTE FUNCTION copyparse_notify_publish()
""",
    ]


def queue_notify_statements() -> list[str]:
    return list(NOTIFY_FUNCTIONS_SQL) + build_trigger_statements()


def build_queue_notify_sql() -> str:
    return ";\n".join(queue_notify_statements()) + ";\n"


QUEUE_NOTIFY_TRIGGERS = build_queue_notify_sql()
