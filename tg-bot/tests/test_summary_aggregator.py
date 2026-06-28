"""Tests for summary_aggregator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.summary_aggregator import SummaryAggregator


def test_domain_in_chats_numeric_match():
    aggregator = SummaryAggregator()
    assert aggregator._domain_in_chats("-100123", ["-100123"]) is True
    assert aggregator._domain_in_chats("-100123", ["-100999"]) is False


def test_domain_in_chats_username_match():
    aggregator = SummaryAggregator()
    assert aggregator._domain_in_chats("@news", ["@news"]) is True
    assert aggregator._domain_in_chats("@news", ["-100123"]) is False


def test_is_post_digested():
    assert SummaryAggregator._is_post_digested(None) is False
    assert SummaryAggregator._is_post_digested({"digested_at": "2026-01-01"}) is True
    assert SummaryAggregator._is_post_digested('{"digested_at": "2026-01-01"}') is True


@pytest.mark.asyncio
async def test_get_digest_sleep_interval_sec_uses_minimum():
    aggregator = SummaryAggregator()
    profiles = [
        {"digest_interval_min": 60},
        {"digest_interval_min": 15},
    ]
    with patch.object(aggregator, "_load_digest_profiles", AsyncMock(return_value=profiles)):
        assert await aggregator.get_digest_sleep_interval_sec() == 15 * 60


@pytest.mark.asyncio
async def test_get_digest_sleep_interval_sec_default_when_no_profiles():
    aggregator = SummaryAggregator()
    with patch.object(aggregator, "_load_digest_profiles", AsyncMock(return_value=[])):
        assert await aggregator.get_digest_sleep_interval_sec() == 1800


@pytest.mark.asyncio
async def test_run_digest_cycle_combined_mode():
    aggregator = SummaryAggregator()
    profile = {
        "user_id": 1,
        "digest_interval_min": 30,
        "digest_channel": "-100999",
        "digest_mode": "combined",
        "chats_to_read": ["-100123"],
    }
    chat_groups = {
        "-100123": [{"id": 10, "text": "alpha"}, {"id": 11, "text": "beta"}],
    }
    client = AsyncMock()
    client_manager = MagicMock()
    client_manager.get_client.return_value = client

    with (
        patch.object(aggregator, "_load_digest_profiles", AsyncMock(return_value=[profile])),
        patch.object(aggregator, "_fetch_recent_posts", AsyncMock(return_value=chat_groups)),
        patch.object(aggregator, "_build_combined_digest", AsyncMock(return_value="summary text")),
        patch.object(aggregator, "_save_digest", AsyncMock()),
        patch.object(aggregator, "_mark_posts_digested", AsyncMock()) as mark_mock,
        patch("services.summary_aggregator.ai_client", MagicMock()),
        patch("services.summary_aggregator.parse_channel", return_value=-100999),
    ):
        sent = await aggregator.run_digest_cycle(client_manager)

    assert sent == 1
    client.send_message.assert_awaited_once()
    mark_mock.assert_awaited_once_with([10, 11])


@pytest.mark.asyncio
async def test_run_digest_cycle_per_channel_mode():
    aggregator = SummaryAggregator()
    profile = {
        "user_id": 1,
        "digest_interval_min": 30,
        "digest_channel": "-100999",
        "digest_mode": "per_channel",
        "chats_to_read": [],
    }
    chat_groups = {"-100123": [{"id": 10, "text": "hello"}]}
    client = AsyncMock()
    client_manager = MagicMock()
    client_manager.get_client.return_value = client

    with (
        patch.object(aggregator, "_load_digest_profiles", AsyncMock(return_value=[profile])),
        patch.object(aggregator, "_fetch_recent_posts", AsyncMock(return_value=chat_groups)),
        patch.object(aggregator, "_build_digest", AsyncMock(return_value="digest")),
        patch.object(aggregator, "_save_digest", AsyncMock()),
        patch.object(aggregator, "_mark_posts_digested", AsyncMock()) as mark_mock,
        patch("services.summary_aggregator.ai_client", MagicMock()),
        patch("services.summary_aggregator.parse_channel", return_value=-100999),
    ):
        sent = await aggregator.run_digest_cycle(client_manager)

    assert sent == 1
    mark_mock.assert_awaited_once_with([10])
