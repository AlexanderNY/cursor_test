"""Publish HTML allowlist."""

from shared.publish_html import sanitize_publish_html


def test_keeps_formatting_and_safe_link() -> None:
    raw = '<p>Код на <a href="https://example.com/a" onclick="alert(1)">странице</a></p>'
    assert sanitize_publish_html(raw) == (
        '<p>Код на <a href="https://example.com/a">странице</a></p>'
    )


def test_strips_script_iframe_and_javascript_href() -> None:
    raw = '<script>alert(1)</script><iframe src="https://evil.example"></iframe><a href="javascript:alert(1)">x</a>'
    cleaned = sanitize_publish_html(raw)
    assert "<script" not in cleaned.lower()
    assert "<iframe" not in cleaned.lower()
    assert "javascript:" not in cleaned.lower()
    assert "alert(1)" in cleaned
    assert ">x</a>" in cleaned


def test_drops_event_handler_on_image() -> None:
    cleaned = sanitize_publish_html('<img src=x onerror="alert(1)">привет')
    assert "<img" not in cleaned.lower()
    assert "onerror" not in cleaned.lower()
    assert "привет" in cleaned
