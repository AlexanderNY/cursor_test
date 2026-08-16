"""Tests for brand-channel alert rule conversion."""

from services.brand_channel_flow import channel_alert_rules_as_profile_rules


def test_alert_rules_expand_to_selected_destinations():
    channel = {
        "id": 10,
        "external_id": "-1001",
        "alert_delivery": {
            "alert_text": "Hit",
            "include_ai_summary": True,
            "channel_to_post": "-1002",
        },
        "alert_rules": [
            {
                "id": "kw-1",
                "enabled": True,
                "save_conditions": ["urgent"],
                "conditions_mode": "any_of",
            }
        ],
    }
    dests = [
        {"external_id": "-1002", "title": "Ops", "network": "tg"},
        {"external_id": "-1003", "title": "News", "network": "tg"},
    ]
    rules = channel_alert_rules_as_profile_rules(channel, destinations=dests)
    assert len(rules) == 2
    assert {r["channel_to_post"] for r in rules} == {"-1002", "-1003"}
    assert all(r["alert_text"] == "Hit" for r in rules)
    assert all(r["save_conditions"] == ["urgent"] for r in rules)
    assert all(r["chats_to_read"] == ["-1001"] for r in rules)


def test_alert_rules_fallback_to_channel_to_post():
    channel = {
        "id": 10,
        "external_id": "-1001",
        "alert_delivery": {
            "alert_text": "Hit",
            "channel_to_post": "-1009",
            "channel_to_post_title": "Legacy",
        },
        "alert_rules": [{"id": "r1", "enabled": True, "save_conditions": ["kw"]}],
    }
    rules = channel_alert_rules_as_profile_rules(channel)
    assert len(rules) == 1
    assert rules[0]["channel_to_post"] == "-1009"
    assert rules[0]["channel_to_post_title"] == "Legacy"


def test_alert_rules_skip_without_text_or_keywords():
    channel = {
        "id": 10,
        "external_id": "-1001",
        "alert_delivery": {"alert_text": "", "channel_to_post": "-1002"},
        "alert_rules": [{"enabled": True, "save_conditions": ["kw"]}],
    }
    assert channel_alert_rules_as_profile_rules(channel) == []

    channel["alert_delivery"]["alert_text"] = "Hi"
    channel["alert_rules"] = [{"enabled": True, "save_conditions": []}]
    assert channel_alert_rules_as_profile_rules(channel) == []
