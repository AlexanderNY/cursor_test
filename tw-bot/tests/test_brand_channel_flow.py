"""Unit tests for Twitter brand-channel handle normalization and dest mapping."""

from services.brand_channel_flow import (
    normalize_tw_handle,
    publish_targets_to_destination_fields,
)


def test_normalize_handle_plain_and_at():
    assert normalize_tw_handle("elonmusk") == "elonmusk"
    assert normalize_tw_handle("@elonmusk") == "elonmusk"


def test_normalize_handle_from_url():
    assert normalize_tw_handle("https://x.com/OpenAI") == "OpenAI"
    assert normalize_tw_handle("https://twitter.com/OpenAI/status/1") == "OpenAI"
    assert normalize_tw_handle("x.com/@nasa") == "nasa"


def test_normalize_handle_numeric_rest_id():
    assert normalize_tw_handle("44196397") == "44196397"


def test_normalize_handle_rejects_garbage():
    assert normalize_tw_handle("") is None
    assert normalize_tw_handle("not a handle!!!") is None
    assert normalize_tw_handle("too_long_handle_name_xyz") is None


def test_publish_targets_sets_to_tw():
    dest = publish_targets_to_destination_fields(
        [
            {
                "network": "tw",
                "external_id": "@brand",
                "publish_enabled": True,
            },
            {
                "network": "tg",
                "external_id": "-1001",
                "publish_enabled": True,
            },
        ]
    )
    assert dest["to_tw"] is True
    assert dest["to_tg"] is True
    assert "-1001" in dest["target_channels"]
    assert "twitter" in dest["process_services"]
    assert "telegram" in dest["process_services"]
