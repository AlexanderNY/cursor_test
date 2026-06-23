"""Tests for alert_service."""

import pytest

from services.alert_service import build_alert_message, get_active_rules, parse_channel


@pytest.mark.asyncio
async def test_build_alert_message_within_limit():
    text = await build_alert_message("Alert!", -100123, "Hello world")
    assert text == "Alert!\n\nКанал: -100123\nСообщение:\nHello world"


@pytest.mark.asyncio
async def test_build_alert_message_truncates_long_body():
    long_body = "x" * 5000
    text = await build_alert_message("A", 1, long_body)
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
    assert active[0].get("id")


def test_get_active_rules_includes_extended_fields():
    profile = {
        "alert_enabled": True,
        "alert_rules": [
            {
                "id": "rule-1",
                "enabled": True,
                "priority": 5,
                "chats_to_read": ["-1001"],
                "save_conditions": ["kw"],
                "channel_to_post": "-1002",
                "alert_text": "Hi",
                "dedup_window_sec": 120,
                "include_ai_summary": True,
                "stop_on_match": True,
            }
        ],
    }
    active = get_active_rules(profile)
    assert active[0]["priority"] == 5
    assert active[0]["dedup_window_sec"] == 120
    assert active[0]["include_ai_summary"] is True
    assert active[0]["stop_on_match"] is True


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
