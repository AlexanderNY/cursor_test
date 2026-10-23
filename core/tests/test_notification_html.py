"""Notification HTML allowlist."""

from services.notification_html import sanitize_notification_html


def test_keeps_internal_link_and_formatting() -> None:
    raw = '<p>Код на <a href="/telegram?auth=1" onclick="alert(1)">странице</a></p>'
    assert sanitize_notification_html(raw) == (
        '<p>Код на <a href="/telegram?auth=1">странице</a></p>'
    )


def test_strips_script_and_javascript_href() -> None:
    raw = '<script>alert(1)</script><a href="javascript:alert(1)">x</a>'
    cleaned = sanitize_notification_html(raw)
    assert "<script" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()
    assert "alert(1)" in cleaned
    assert ">x</a>" in cleaned


def test_drops_unknown_tags_but_keeps_text() -> None:
    cleaned = sanitize_notification_html('<img src=x onerror="alert(1)">привет<div>мир</div>')
    assert "<img" not in cleaned.lower()
    assert "<div" not in cleaned.lower()
    assert "привет" in cleaned
    assert "мир" in cleaned
