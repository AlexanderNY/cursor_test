"""Unit tests for admin post-trace stage inference."""

from services.admin_service import AdminService


def test_infer_path_stages_full_publish() -> None:
    hub = {"status": "ready", "source_platform": "tg", "created_at": "2026-01-01T00:00:00Z"}
    targets = [
        {"status": "published"},
        {"status": "published"},
    ]
    stages = {item["stage"]: item for item in AdminService._infer_path_stages(hub, targets)}
    assert stages["collected"]["done"] is True
    assert stages["processed"]["done"] is True
    assert stages["queued"]["done"] is True
    assert stages["publishing"]["done"] is True
    assert stages["published"]["done"] is True


def test_infer_path_stages_stuck_in_collected() -> None:
    hub = {"status": "collected", "source_platform": "url", "created_at": "2026-01-01T00:00:00Z"}
    stages = {item["stage"]: item for item in AdminService._infer_path_stages(hub, [])}
    assert stages["collected"]["done"] is True
    assert stages["processed"]["done"] is False
    assert stages["queued"]["done"] is False
    assert stages["published"]["done"] is False


def test_infer_path_stages_partial_failure() -> None:
    hub = {"status": "ready", "source_platform": "tg", "created_at": "2026-01-01T00:00:00Z"}
    targets = [{"status": "published"}, {"status": "failed"}]
    stages = {item["stage"]: item for item in AdminService._infer_path_stages(hub, targets)}
    assert stages["publishing"]["done"] is True
    assert stages["published"]["done"] is False
