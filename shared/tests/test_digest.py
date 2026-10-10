from datetime import datetime, timedelta

from shared.digest import (
    build_digest_source_index,
    channel_in_digest_sources,
    clamp_interval_min,
    combine_digest_texts,
    cover_image_from_pack,
    is_digest_due,
    parse_channel_ids,
    parse_digest_ai_payload,
    pick_cover_pack,
    should_create_digest,
    should_notify_cover_miss,
)


def test_parse_channel_ids_dedupes():
    assert parse_channel_ids([1, "2", 1, "x", None]) == [1, 2]


def test_clamp_interval_min():
    assert clamp_interval_min(1) == 5
    assert clamp_interval_min(60) == 60
    assert clamp_interval_min(9999) == 1440
    assert clamp_interval_min("bad") == 60


def test_is_digest_due():
    now = datetime(2026, 1, 1, 12, 0, 0)
    assert is_digest_due(None, 60, now=now) is True
    assert is_digest_due(now - timedelta(minutes=59), 60, now=now) is False
    assert is_digest_due(now - timedelta(minutes=60), 60, now=now) is True


def test_build_digest_source_index():
    jobs = [
        {"id": 1, "enabled": True, "source_channel_ids": [10, 11]},
        {"id": 2, "enabled": False, "source_channel_ids": [12]},
        {"id": 3, "enabled": True, "source_channel_ids": [11, 13]},
    ]
    index = build_digest_source_index(jobs)
    assert set(index) == {10, 11, 13}
    assert index[10]["id"] == 1
    assert index[11]["id"] == 1
    assert channel_in_digest_sources(13, index) is True
    assert channel_in_digest_sources(12, index) is False


def test_combine_digest_texts_limits():
    posts = [{"domain": "a", "post_text": "one"}, {"domain": "b", "post_text": "two"}]
    text = combine_digest_texts(posts, max_posts=1)
    assert "[a]" in text
    assert "two" not in text


def test_should_create_digest_requires_text():
    assert should_create_digest([]) is False
    assert should_create_digest([{"post_text": "  "}]) is False
    assert should_create_digest([{"post_text": "hello"}]) is True


def test_pick_cover_pack_exact_and_partial():
    packs = [
        {"id": 1, "tags": ["спорт"], "object_keys": ["/a.jpg"]},
        {"id": 2, "tags": ["экономика", "нефть"], "object_keys": ["/b.jpg"]},
        {"id": 3, "tags": ["экономика"], "object_keys": []},
    ]
    hit = pick_cover_pack(packs, ["нефть", "рынок"])
    assert hit is not None and hit["id"] == 2
    assert cover_image_from_pack(hit) == "/b.jpg"
    assert pick_cover_pack(packs, ["мода"]) is None
    assert pick_cover_pack([], ["экономика"]) is None


def test_should_notify_cover_miss_dedup():
    now = datetime(2026, 1, 2, 12, 0, 0)
    assert should_notify_cover_miss(theme="нефть", last_theme=None, last_at=None, now=now)
    assert should_notify_cover_miss(
        theme="нефть",
        last_theme="нефть",
        last_at=now - timedelta(hours=25),
        now=now,
    )
    assert not should_notify_cover_miss(
        theme="нефть",
        last_theme="нефть",
        last_at=now - timedelta(hours=1),
        now=now,
    )
    assert should_notify_cover_miss(
        theme="спорт",
        last_theme="нефть",
        last_at=now - timedelta(hours=1),
        now=now,
    )


def test_parse_digest_ai_payload_json_and_plain():
    parsed = parse_digest_ai_payload(
        '{"summary":"Текст сводки","theme":"Нефть","tags":["нефть","рынок"]}'
    )
    assert parsed["summary"] == "Текст сводки"
    assert parsed["theme"] == "Нефть"
    assert "нефть" in parsed["tags"]
    plain = parse_digest_ai_payload("просто текст")
    assert plain["summary"] == "просто текст"
    assert plain["tags"] == []
