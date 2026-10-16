"""Tests for signed OAuth state helper."""

from shared.oauth_state import sign_oauth_state, verify_oauth_state


def test_sign_and_verify_roundtrip():
    secret = "test-secret-key"
    state = sign_oauth_state(42, secret)
    assert verify_oauth_state(state, secret) == 42


def test_verify_rejects_tampered_state():
    secret = "test-secret-key"
    state = sign_oauth_state(7, secret)
    parts = state.split(".")
    parts[0] = "8"
    tampered = ".".join(parts)
    assert verify_oauth_state(tampered, secret) is None


def test_verify_rejects_wrong_secret():
    state = sign_oauth_state(1, "secret-a")
    assert verify_oauth_state(state, "secret-b") is None


def test_verify_rejects_plain_user_id():
    assert verify_oauth_state("123", "secret") is None
