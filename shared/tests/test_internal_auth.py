"""Tests for X-Internal-Token helpers."""

from shared.internal_auth import verify_internal_token


def test_verify_ok():
    ok, reason = verify_internal_token("abc", "abc")
    assert ok is True
    assert reason == ""


def test_verify_not_configured():
    ok, reason = verify_internal_token("abc", "")
    assert ok is False
    assert reason == "not_configured"


def test_verify_invalid():
    ok, reason = verify_internal_token("wrong", "expected")
    assert ok is False
    assert reason == "invalid"


def test_verify_missing_provided():
    ok, reason = verify_internal_token(None, "expected")
    assert ok is False
    assert reason == "invalid"
