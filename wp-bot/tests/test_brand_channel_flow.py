"""Tests for WordPress brand-channel helpers."""

from services.brand_channel_flow import (
    normalize_site_url,
    post_target_sites,
    publish_targets_to_destination_fields,
    site_urls_match,
)


def test_normalize_site_url_strips_slash_and_lowercases_host():
    assert normalize_site_url("HTTPS://Example.COM/blog/") == "https://example.com/blog"
    assert normalize_site_url("example.com") == "https://example.com"
    assert normalize_site_url("") == ""


def test_site_urls_match():
    assert site_urls_match("https://Example.com/", "https://example.com")
    assert not site_urls_match("https://a.com", "https://b.com")
    assert not site_urls_match("", "")


def test_publish_targets_map_wp_and_tg():
    fields = publish_targets_to_destination_fields(
        [
            {
                "network": "wp",
                "external_id": "https://blog.example.com",
                "publish_enabled": True,
            },
            {
                "network": "tg",
                "external_id": "-1001",
                "publish_enabled": True,
            },
            {
                "network": "vk",
                "external_id": "club123",
                "publish_enabled": True,
            },
        ]
    )
    assert fields["to_wp"] is True
    assert fields["to_tg"] is True
    assert fields["to_vk"] is True
    assert "https://blog.example.com" in fields["target_channels"]
    assert "-1001" in fields["target_channels"]
    assert fields["target_groups"] == ["club123"]
    assert "wordpress" in fields["process_services"]
    assert "telegram" in fields["process_services"]


def test_publish_targets_skip_disabled():
    fields = publish_targets_to_destination_fields(
        [
            {
                "network": "wp",
                "external_id": "https://blog.example.com",
                "publish_enabled": False,
            }
        ]
    )
    assert fields["to_wp"] is False
    assert fields["target_channels"] == []


def test_post_target_sites_parses_json_list():
    assert post_target_sites({"target_channels": ["https://a.com", ""]}) == [
        "https://a.com"
    ]
    assert post_target_sites({"target_channels": '["https://b.com"]'}) == [
        "https://b.com"
    ]
    assert post_target_sites({}) == []
