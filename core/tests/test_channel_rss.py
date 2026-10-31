"""RSS feeds attached to an own channel."""

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / "services" / "channel_rss.py"
_spec = importlib.util.spec_from_file_location("channel_rss_under_test", _PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_mod)

MAX_RSS_FEEDS = _mod.MAX_RSS_FEEDS
feed_is_due = _mod.feed_is_due
mark_feed_ran = _mod.mark_feed_ran
merge_rss_feeds = _mod.merge_rss_feeds
public_rss_feeds = _mod.public_rss_feeds
rss_item_id = _mod.rss_item_id
rss_item_text = _mod.rss_item_text


def test_merge_normalizes_url_and_keeps_seen_ids():
    existing = [
        {
            "url": "https://example.com/rss",
            "enabled": True,
            "interval_min": 60,
            "suffix": "",
            "seen_ids": ["post-1"],
            "last_run_at": "2026-01-01T00:00:00+00:00",
        }
    ]
    merged = merge_rss_feeds(
        existing,
        [{"url": "https://Example.COM/rss", "enabled": True, "interval_min": 30, "suffix": "#news"}],
    )
    assert len(merged) == 1
    assert merged[0]["url"] == "https://example.com/rss"
    assert merged[0]["seen_ids"] == ["post-1"]
    assert merged[0]["last_run_at"] == "2026-01-01T00:00:00+00:00"
    assert merged[0]["suffix"] == "#news"
    assert merged[0]["interval_min"] == 30
    assert "seen_ids" not in public_rss_feeds(merged)[0]


def test_merge_rejects_private_and_duplicate_urls():
    with pytest.raises(ValueError, match="Некорректный URL"):
        merge_rss_feeds([], [{"url": "http://127.0.0.1/rss"}])
    merged = merge_rss_feeds(
        [],
        [
            {"url": "https://example.com/a"},
            {"url": "https://example.com/a"},
        ],
    )
    assert len(merged) == 1


def test_merge_caps_feed_count():
    incoming = [{"url": f"https://example.com/{idx}.xml"} for idx in range(MAX_RSS_FEEDS + 1)]
    with pytest.raises(ValueError, match="Не больше"):
        merge_rss_feeds([], incoming)


def test_feed_is_due_respects_interval():
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    fresh = {
        "url": "https://example.com/rss",
        "enabled": True,
        "interval_min": 60,
        "last_run_at": (now - timedelta(minutes=10)).isoformat(),
    }
    stale = {
        **fresh,
        "last_run_at": (now - timedelta(minutes=60)).isoformat(),
    }
    assert feed_is_due(fresh, now) is False
    assert feed_is_due(stale, now) is True
    assert feed_is_due({**fresh, "enabled": False, "last_run_at": None}, now) is False
    assert feed_is_due({**fresh, "last_run_at": None}, now) is True


def test_rss_item_text_strips_html_and_appends_link():
    text = rss_item_text(
        {
            "id": "guid-1",
            "title": "Hello",
            "summary": "<p>World <script>bad()</script></p>",
            "link": "https://example.com/post",
        },
        suffix="#brand",
    )
    assert "script" not in text
    assert "bad()" not in text
    assert "Hello" in text
    assert "World" in text
    assert "https://example.com/post" in text
    assert text.endswith("#brand")
    assert rss_item_id({"id": "guid-1", "link": "https://example.com/post"}) == "guid-1"


def test_mark_feed_ran_appends_seen_id():
    feed: dict = {"seen_ids": ["a"]}
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    mark_feed_ran(feed, now, "b")
    assert feed["seen_ids"] == ["a", "b"]
    assert feed["last_run_at"].startswith("2026-06-01")
