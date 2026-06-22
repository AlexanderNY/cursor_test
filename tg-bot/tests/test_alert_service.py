"""Tests for alert_service."""

from services.alert_service import build_alert_message, get_active_rules, parse_channel


def test_build_alert_message_within_limit():
    text = build_alert_message("Alert!", -100123, "Hello world")
    assert text == "Alert!\n\nКанал: -100123\nСообщение:\nHello world"


def test_build_alert_message_truncates_long_body():
    long_body = "x" * 5000
    text = build_alert_message("A", 1, long_body)
    assert len(text) <= 4096
    assert text.endswith("...")


def test_parse_channel_numeric_and_username():
    assert parse_channel("-100123") == -100123
    assert parse_channel("@mychannel") == "@mychannel"


def test_get_active_rules_filters_incomplete():
    profile = {
        "alert_enabled": True,
        "alert_rules": [
            {
                "enabled": True,
                "chats_to_read": ["-1001"],
                "save_conditions": ["keyword"],
                "channel_to_post": "-1002",
                "alert_text": "Test alert",
            },
            {
                "enabled": True,
                "chats_to_read": ["-1001"],
                "save_conditions": [],
                "channel_to_post": "-1002",
                "alert_text": "Incomplete",
            },
        ],
    }
    active = get_active_rules(profile)
    assert len(active) == 1
    assert active[0]["alert_text"] == "Test alert"


def test_get_active_rules_disabled_when_flag_off():
    profile = {
        "alert_enabled": False,
        "alert_rules": [
            {
                "enabled": True,
                "chats_to_read": ["-1001"],
                "save_conditions": ["keyword"],
                "channel_to_post": "-1002",
                "alert_text": "Test alert",
            }
        ],
    }
    assert get_active_rules(profile) == []
