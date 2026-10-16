"""Unit tests for Yandex cookie session helpers (no Selenium / Chrome)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.yandex_session import (  # noqa: E402
    classify_session_state,
    cookies_nonempty,
    filter_cookie_dict,
    is_publish_success_url,
    parse_session_cookies,
)


def test_filter_cookie_dict_keeps_add_cookie_fields() -> None:
    raw = {
        "name": "Session_id",
        "value": "abc",
        "domain": ".yandex.ru",
        "path": "/",
        "expiry": 1700000000.9,
        "secure": 1,
        "httpOnly": True,
        "sameSite": "None",
        "extra_ignored": "x",
    }
    filtered = filter_cookie_dict(raw)
    assert filtered is not None
    assert filtered["name"] == "Session_id"
    assert filtered["value"] == "abc"
    assert filtered["domain"] == ".yandex.ru"
    assert filtered["path"] == "/"
    assert filtered["expiry"] == 1700000000
    assert filtered["secure"] is True
    assert filtered["httpOnly"] is True
    assert filtered["sameSite"] == "None"
    assert "extra_ignored" not in filtered


def test_filter_cookie_dict_requires_name_and_value() -> None:
    assert filter_cookie_dict({}) is None
    assert filter_cookie_dict({"name": "a"}) is None
    assert filter_cookie_dict({"value": "b"}) is None


@pytest.mark.parametrize(
    ("cookies", "expected"),
    [
        (None, False),
        ([], False),
        ({"not": "list"}, False),
        ([{"name": "a", "value": "1"}], True),
    ],
)
def test_cookies_nonempty(cookies, expected: bool) -> None:
    assert cookies_nonempty(cookies) is expected


def test_parse_empty_json_string() -> None:
    assert cookies_nonempty(parse_session_cookies("[]")) is False


@pytest.mark.parametrize(
    ("has_cookies", "looks_logged_in", "expected"),
    [
        (False, None, "missing"),
        (False, True, "missing"),
        (True, True, "ok"),
        (True, False, "expired"),
        (True, None, "unknown"),
    ],
)
def test_classify_session_state(has_cookies: bool, looks_logged_in, expected: str) -> None:
    assert (
        classify_session_state(has_cookies=has_cookies, looks_logged_in=looks_logged_in)
        == expected
    )


def test_parse_session_cookies_filters_junk() -> None:
    raw = [
        {"name": "ok", "value": "1", "domain": "dzen.ru"},
        {"name": "", "value": "x"},
        "not-a-dict",
        {"value": "only"},
    ]
    parsed = parse_session_cookies(raw)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "ok"
    assert parsed[0]["domain"] == "dzen.ru"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://dzen.ru/a/AbCdEf", True),
        ("https://dzen.ru/media/id/123/article/xyz", True),
        ("https://dzen.ru/article/new?type=article", False),
        ("https://passport.yandex.ru/auth", False),
        ("", False),
    ],
)
def test_is_publish_success_url(url: str, expected: bool) -> None:
    assert is_publish_success_url(url) is expected
