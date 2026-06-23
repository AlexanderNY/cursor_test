"""Tests for routing_engine helpers."""

from types import SimpleNamespace

from services.routing_engine import ensure_rule_ids
from services.message_handler import MessageHandler


def test_ensure_rule_ids_adds_missing():
    profile = {"alert_rules": [{"enabled": True}]}
    ensure_rule_ids(profile)
    assert profile["alert_rules"][0].get("id")


def test_chat_id_in_list():
    handler = MessageHandler()
    assert handler.chat_id_in_list(-100123, ["-100123"]) is True
    assert handler.chat_id_in_list(-100123, ["-999"]) is False


def test_time_windows_empty_allows():
    handler = MessageHandler()
    assert handler.is_within_time_windows([]) is True
