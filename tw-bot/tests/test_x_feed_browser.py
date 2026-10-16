"""Юнит-тесты парсера ленты X (без живого x.com / Chrome)."""

from services.x_feed_browser import (
    canonical_status_url,
    dumps_cookies,
    extract_status_id,
    loads_cookies,
    parse_tweet_card_fields,
)


def test_extract_status_id_from_user_status_href():
    assert extract_status_id("https://x.com/elonmusk/status/1234567890") == "1234567890"
    assert extract_status_id("https://twitter.com/foo/status/99887766?s=20") == "99887766"


def test_extract_status_id_from_web_status():
    assert extract_status_id("https://x.com/i/web/status/555") == "555"
    assert extract_status_id("/i/web/status/555/") == "555"


def test_extract_status_id_rejects_non_status():
    assert extract_status_id("https://x.com/home") is None
    assert extract_status_id("") is None
    assert extract_status_id("https://x.com/user/status/") is None


def test_canonical_status_url():
    assert canonical_status_url("42") == "https://x.com/i/web/status/42"


def test_parse_tweet_card_fields_prefers_first_valid_href():
    card = parse_tweet_card_fields(
        [
            "https://x.com/alice",
            "https://x.com/alice/status/777888999",
            "https://x.com/alice/status/777888999/analytics",
        ],
        "Hello from the feed\n#line2",
    )
    assert card is not None
    assert card["status_id"] == "777888999"
    assert card["url"] == "https://x.com/i/web/status/777888999"
    assert card["text"] == "Hello from the feed\n#line2"


def test_parse_tweet_card_fields_none_without_status():
    assert parse_tweet_card_fields(["https://x.com/bob"], "no status link") is None


def test_user_and_web_status_same_canonical_id():
    a = extract_status_id("https://x.com/someone/status/111222333")
    b = extract_status_id("https://x.com/i/web/status/111222333")
    assert a == b == "111222333"
    assert canonical_status_url(a) == canonical_status_url(b)


def test_cookies_roundtrip():
    raw = [
        {
            "name": "auth_token",
            "value": "secret",
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "expiry": 1700000000.9,
        },
        {"name": "ct0", "value": "csrf", "domain": ".x.com", "path": "/"},
        {"bad": True},
    ]
    dumped = dumps_cookies(raw)
    loaded = loads_cookies(dumped)
    assert len(loaded) == 2
    assert loaded[0]["name"] == "auth_token"
    assert loaded[0]["value"] == "secret"
    assert loaded[1]["name"] == "ct0"


def test_loads_cookies_empty_or_invalid():
    assert loads_cookies(None) == []
    assert loads_cookies("") == []
    assert loads_cookies("not-json") == []
    assert loads_cookies("{}") == []
