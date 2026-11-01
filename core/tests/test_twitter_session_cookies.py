"""Cookies сессии X, вставленные пользователем из браузера."""

import json

import pytest

from services.twitter_session_cookies import build_x_session_cookies, clean_cookie_value


def test_no_auth_token_means_no_cookie_update():
    assert build_x_session_cookies(None, None) is None
    assert build_x_session_cookies("  ", "abc") is None


def test_builds_auth_token_and_ct0_for_x_domain():
    token = "a" * 40
    csrf = "b" * 160
    cookies = json.loads(build_x_session_cookies(token, csrf))
    assert [item["name"] for item in cookies] == ["auth_token", "ct0"]
    assert all(item["domain"] == ".x.com" for item in cookies)
    assert cookies[0]["value"] == token
    assert cookies[1]["value"] == csrf


def test_ct0_is_optional():
    cookies = json.loads(build_x_session_cookies("c" * 40, ""))
    assert [item["name"] for item in cookies] == ["auth_token"]


def test_strips_devtools_copy_artifacts():
    assert clean_cookie_value(' "auth_token=abc123"; ', "auth_token") == "abc123"
    assert clean_cookie_value("ct0=xyz;", "ct0") == "xyz"


def test_rejects_garbage():
    with pytest.raises(ValueError):
        build_x_session_cookies("not a token!", None)
    with pytest.raises(ValueError):
        build_x_session_cookies("d" * 40, "bad value")
