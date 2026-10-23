"""Unit tests for Instagram brand-channel handle normalization and dest mapping."""

from services.brand_channel_flow import (
    normalize_instagram_handle,
    publish_targets_to_destination_fields,
)


def test_normalize_handle_plain_and_at():
    assert normalize_instagram_handle("natgeo") == "natgeo"
    assert normalize_instagram_handle("@natgeo") == "natgeo"


def test_normalize_handle_from_url():
    assert normalize_instagram_handle("https://www.instagram.com/natgeo/") == "natgeo"
    assert normalize_instagram_handle("instagram.com/@nasa/reel/abc") == "nasa"


def test_normalize_handle_numeric_pk():
    assert normalize_instagram_handle("25025320") == "25025320"


def test_normalize_handle_rejects_garbage():
    assert normalize_instagram_handle("") is None
    assert normalize_instagram_handle("bad name!!!") is None


def test_publish_targets_sets_to_instagram():
    dest = publish_targets_to_destination_fields(
        [
            {"network": "instagram", "external_id": "@brand", "publish_enabled": True},
            {"network": "tg", "external_id": "-1001", "publish_enabled": True},
        ]
    )
    assert dest["to_instagram"] is True
    assert dest["to_tg"] is True
    assert "instagram" in dest["process_services"]
