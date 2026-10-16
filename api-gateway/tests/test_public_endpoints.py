"""Unit tests for gateway public-endpoint allowlist."""

import sys
from pathlib import Path

# api-gateway package root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from middleware.jwt_validator import check_public_endpoint  # noqa: E402


def test_login_is_public():
    assert check_public_endpoint("/auth/login") is True


def test_tw_oauth_callback_is_public():
    assert check_public_endpoint("/tw/oauth/callback") is True


def test_th_bot_selenium_requires_jwt():
    assert check_public_endpoint("/th-bot/selenium/attempt") is False


def test_url_bot_run_requires_jwt():
    assert check_public_endpoint("/url-bot/run") is False


def test_tg_bot_auth_requires_jwt():
    assert check_public_endpoint("/tg-bot/auth/code") is False


def test_dzen_rss_prefix_is_public():
    assert check_public_endpoint("/dzen/rss/1") is True
