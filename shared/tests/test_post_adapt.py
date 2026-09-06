"""Tests for shared.post_adapt."""

import pytest

from shared.post_adapt import (
    NETWORK_TEXT_LIMITS,
    adapters_to_platform_texts,
    adapt_for_networks,
    fit_text,
    hard_truncate,
    normalize_network,
    prepare_platform_texts,
    to_plain,
)


def test_normalize_network_aliases():
    assert normalize_network("Telegram") == "tg"
    assert normalize_network("vkontakte") == "vk"
    assert normalize_network("x") == "tw"
    assert normalize_network("tw") == "tw"


def test_to_plain_strips_html():
    assert to_plain("<b>Hello</b> &nbsp;world") == "Hello  world"
    assert to_plain("") == ""


def test_hard_truncate():
    assert hard_truncate("abcdef", 3) == "abc"
    assert hard_truncate("ab", 10) == "ab"


@pytest.mark.asyncio
async def test_fit_text_truncates_without_summarize():
    long_text = "x" * 400
    fitted = await fit_text(long_text, "tw", prefer_summarize=False)
    assert len(fitted) == NETWORK_TEXT_LIMITS["tw"]
    assert fitted == "x" * 280


@pytest.mark.asyncio
async def test_adapt_keeps_html_for_tg_plain_for_others():
    html = "<b>" + ("a" * 300) + "</b>"
    adapters = await adapt_for_networks(
        html,
        media=["https://img.example/1.jpg"],
        networks=["tg", "tw", "vk"],
        prefer_summarize=False,
    )
    assert "tg" in adapters
    assert adapters["tg"]["parse_mode"] == "HTML"
    assert "<b>" in adapters["tg"]["text"]
    assert len(adapters["tg"]["text"]) <= NETWORK_TEXT_LIMITS["tg"]

    assert "tw" in adapters
    assert "<" not in adapters["tw"]["text"]
    assert len(adapters["tw"]["text"]) == NETWORK_TEXT_LIMITS["tw"]

    assert "vk" in adapters
    assert adapters["vk"]["attachments_mode"] == "single"
    assert len(adapters["vk"]["text"]) <= NETWORK_TEXT_LIMITS["vk"]


@pytest.mark.asyncio
async def test_adapt_from_targets_list():
    adapters = await adapt_for_networks(
        "hello",
        media=[],
        targets=[{"network": "telegram"}, {"network": "threads"}],
        prefer_summarize=False,
    )
    assert set(adapters.keys()) == {"tg", "threads"}
    assert adapters["tg"]["text"] == "hello"
    assert adapters["threads"]["text"] == "hello"


@pytest.mark.asyncio
async def test_static_html_appended_when_fits():
    adapters = await adapt_for_networks(
        "hi",
        networks=["tg"],
        static_html="<i>footer</i>",
        prefer_summarize=False,
    )
    assert adapters["tg"]["text"] == "hi\n<i>footer</i>"


@pytest.mark.asyncio
async def test_static_html_skipped_when_over_limit():
    body = "y" * (NETWORK_TEXT_LIMITS["tw"] - 2)
    adapters = await adapt_for_networks(
        body,
        networks=["tw"],
        static_html="TOOLONG",
        prefer_summarize=False,
    )
    assert adapters["tw"]["text"] == body


@pytest.mark.asyncio
async def test_prepare_platform_texts_long_keys():
    flag_to_network = {
        "to_tg": "telegram",
        "to_tw": "twitter",
        "to_vk": "vkontakte",
    }
    texts = await prepare_platform_texts(
        "<p>" + ("z" * 500) + "</p>",
        {"to_tg": True, "to_tw": True, "to_vk": False},
        flag_to_network=flag_to_network,
        prefer_summarize=False,
    )
    assert "telegram" in texts
    assert "twitter" in texts
    assert "vkontakte" not in texts
    assert len(texts["twitter"]) == 280
    assert "<" not in texts["twitter"]


@pytest.mark.asyncio
async def test_fit_text_summarize_result_never_exceeds_limit(monkeypatch):
    async def fake_summarize(text: str, max_length: int) -> str:
        return text[:max_length] + "..."

    monkeypatch.setattr("shared.ai_client.summarize", fake_summarize)
    fitted = await fit_text("x" * 400, "tw", prefer_summarize=True)
    assert len(fitted) == NETWORK_TEXT_LIMITS["tw"]


def test_adapters_to_platform_texts():
    mapped = adapters_to_platform_texts(
        {"tg": {"text": "a"}, "vk": {"text": "b"}, "unknown": {"text": "c"}}
    )
    assert mapped == {"telegram": "a", "vkontakte": "b", "unknown": "c"}
