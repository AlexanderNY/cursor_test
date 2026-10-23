"""Unit tests for Threads brand-channel handle normalization and dest mapping."""

from services.brand_channel_flow import (
    normalize_threads_handle,
    publish_targets_to_destination_fields,
)
from services.threads_feed_browser import (
    canonical_post_url,
    extract_post_id,
    parse_post_card_fields,
)


def test_normalize_handle_plain_and_at():
    assert normalize_threads_handle("mybrand") == "mybrand"
    assert normalize_threads_handle("@mybrand") == "mybrand"


def test_normalize_handle_from_url():
    assert normalize_threads_handle("https://www.threads.net/@OpenAI") == "OpenAI"
    assert normalize_threads_handle("threads.net/@nasa/post/abc") == "nasa"


def test_normalize_handle_numeric_id():
    assert normalize_threads_handle("17841400000000000") == "17841400000000000"


def test_normalize_handle_rejects_garbage():
    assert normalize_threads_handle("") is None
    assert normalize_threads_handle("bad handle!!!") is None


def test_publish_targets_sets_to_threads():
    dest = publish_targets_to_destination_fields(
        [
            {"network": "threads", "external_id": "@brand", "publish_enabled": True},
            {"network": "tg", "external_id": "-1001", "publish_enabled": True},
        ]
    )
    assert dest["to_threads"] is True
    assert dest["to_tg"] is True
    assert "threads" in dest["process_services"]


def test_extract_post_id():
    assert extract_post_id("https://www.threads.net/@u/post/CxYz123") == "CxYz123"
    assert extract_post_id("https://www.threads.net/t/AbC") == "AbC"
    assert extract_post_id("https://www.threads.net/@u") is None


def test_parse_post_card_fields():
    card = parse_post_card_fields(
        ["https://www.threads.net/@alice", "https://www.threads.net/@alice/post/ZZ9"],
        "Hello threads",
        "alice",
    )
    assert card is not None
    assert card["post_id"] == "ZZ9"
    assert card["url"] == canonical_post_url("ZZ9", "alice")
    assert card["text"] == "Hello threads"
