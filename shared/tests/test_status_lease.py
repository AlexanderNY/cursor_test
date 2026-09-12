from shared.status_lease import reclaim_source_processing_sql, reclaim_stale_sql
from shared.db.queue_notify import SOURCE_NOTIFY_TABLES, queue_notify_statements
from shared.queue_wakeup import (
    ALLOWED_CHANNELS,
    CHANNEL_COLLECT,
    CHANNEL_PUBLISH,
    WakeGate,
)


def test_reclaim_stale_sql_uses_bind_params_and_ident():
    sql = reclaim_stale_sql(
        "post_targets",
        from_status="publishing",
        to_status="ready",
        older_than_minutes=5,
    )
    assert "UPDATE post_targets" in sql
    assert "%s" in sql
    assert "publishing" not in sql  # bound, not inlined


def test_reclaim_source_processing_sql_requires_platform_bind():
    sql = reclaim_source_processing_sql("posts")
    assert "UPDATE posts" in sql
    assert "NOT EXISTS" in sql
    assert sql.count("%s") == 2


def test_queue_notify_covers_process_and_publish():
    blob = "\n".join(queue_notify_statements())
    for table in SOURCE_NOTIFY_TABLES:
        assert table in blob
    assert "copyparse_process" in blob
    assert "copyparse_publish" in blob
    assert "WHEN (NEW.status = 'collected')" in blob
    assert "WHEN (NEW.status = 'ready')" in blob
    assert "post_targets" in blob
    assert "CREATE TRIGGER trg_copyparse_notify_collect" not in blob
    assert "CREATE TRIGGER trg_copyparse_notify_distribute" not in blob


def test_wake_gate_channels_allowlisted():
    assert CHANNEL_COLLECT in ALLOWED_CHANNELS
    assert CHANNEL_PUBLISH in ALLOWED_CHANNELS
    gate = WakeGate()
    gate.wake()
    assert gate.event.is_set()
