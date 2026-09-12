from pathlib import Path

from shared.db.bot_queue import claimed_target_as_post, dest_flags_to_platforms


def test_dest_flags_to_platforms():
    assert dest_flags_to_platforms({"to_tg": True, "to_vk": False}) == ["tg"]
    assert dest_flags_to_platforms({}) == []


def test_claimed_target_as_post_sets_queue_ids():
    row = {
        "target_id": 9,
        "post_id": 4,
        "user_id": 1,
        "post_text": "hi",
        "platform": "tg",
    }
    post = claimed_target_as_post(row)
    assert post["id"] == 9
    assert post["_target_id"] == 9
    assert post["_post_id"] == 4
    assert post["_queue"] == "targets"


def test_tg_collector_inserts_hub_posts():
    source = Path(__file__).resolve().parents[1].joinpath(
        "services", "post_collector.py"
    ).read_text(encoding="utf-8")
    assert "INSERT INTO tg_posts" not in source
    assert "InboundPostCreate" in source
    assert 'source_platform="tg"' in source
