"""Какие тосты авторизации снимаются после подключения Telegram."""

from services.notification_service import auth_notification_types_to_clear


def test_connected_session_clears_only_network_error() -> None:
    assert auth_notification_types_to_clear(authorized=False) == ["tg_auth_error"]


def test_authorized_session_clears_code_and_password_prompts() -> None:
    assert auth_notification_types_to_clear(authorized=True) == [
        "tg_auth_error",
        "tg_auth_code",
        "tg_auth_2fa",
    ]
