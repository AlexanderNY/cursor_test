"""Unit tests for post path timeline reconstruction."""

from shared.db.post_lifecycle import build_post_trace_timeline


def test_timeline_uses_lifecycle_events_when_present() -> None:
    hub = {
        "id": 1,
        "status": "ready",
        "source_platform": "tg",
        "created_at": "2026-01-01T10:00:00+00:00",
        "updated_at": "2026-01-01T10:05:00+00:00",
    }
    targets = [{"id": 10, "platform": "tg", "status": "published", "updated_at": "2026-01-01T10:06:00+00:00"}]
    events = [
        {
            "platform": "tg",
            "from_status": None,
            "to_status": "collected",
            "actor": "posts.create_inbound",
            "created_at": "2026-01-01T10:00:00+00:00",
            "payload": {},
        },
        {
            "platform": "hub",
            "from_status": "processing",
            "to_status": "ready",
            "actor": "processor.save_processed",
            "created_at": "2026-01-01T10:05:00+00:00",
            "payload": {},
        },
        {
            "platform": "tg",
            "from_status": "publishing",
            "to_status": "published",
            "actor": "bot.apply_publish_result",
            "created_at": "2026-01-01T10:06:00+00:00",
            "payload": {"target_id": 10},
        },
    ]

    timeline = build_post_trace_timeline(hub=hub, targets=targets, lifecycle_events=events)

    assert len(timeline) == 3
    assert all(item["source"] == "post_lifecycle_events" for item in timeline)
    assert [item["to_status"] for item in timeline] == ["collected", "ready", "published"]


def test_timeline_infers_path_when_journal_empty() -> None:
    hub = {
        "id": 2,
        "status": "ready",
        "source_platform": "vk",
        "created_at": "2026-02-01T12:00:00+00:00",
        "updated_at": "2026-02-01T12:10:00+00:00",
    }
    targets = [
        {
            "id": 20,
            "platform": "tg",
            "status": "failed",
            "updated_at": "2026-02-01T12:12:00+00:00",
            "result": {"error": "timeout"},
        }
    ]

    timeline = build_post_trace_timeline(hub=hub, targets=targets, lifecycle_events=[])

    assert len(timeline) >= 3
    assert all(item["source"] == "inferred" for item in timeline)
    statuses = [item["to_status"] for item in timeline]
    assert "collected" in statuses
    assert "ready" in statuses
    assert "failed" in statuses
