from services.processing_service import (
    _match_url_config,
    resolve_process_destinations,
)


def test_match_url_config_prefers_item_id():
    urls = [
        {"id": "a", "url": "https://example.com/x", "target_social_networks": {"tg": False}},
        {"id": "b", "url": "https://example.com/x", "target_social_networks": {"tg": True}},
    ]
    matched = _match_url_config(urls, "https://example.com/x", url_item_id="b")
    assert matched is not None
    assert matched["id"] == "b"


def test_resolve_destinations_from_url_channels():
    platforms, channels, groups = resolve_process_destinations(
        {"source_platform": "url", "target_channels": [], "target_groups": []},
        {
            "process_services": [],
            "url_target_social_networks": {"tg": True, "vk": False},
            "url_target_channels": ["-1002009872429"],
            "url_target_groups": [],
        },
    )
    assert "tg" in platforms
    assert channels == ["-1002009872429"]
    assert groups == []


def test_resolve_destinations_from_existing_targets():
    platforms, channels, groups = resolve_process_destinations(
        {"source_platform": "url"},
        {"process_services": []},
        existing_targets=[
            {
                "platform": "tg",
                "target_channels": ["-1001"],
                "target_groups": [],
            }
        ],
    )
    assert platforms == ["tg"]
    assert channels == ["-1001"]
    assert groups == []
