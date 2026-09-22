from pathlib import Path

_SERVICE = Path(__file__).resolve().parents[1] / "services" / "schedules_service.py"


def test_schedules_or_brand_channel_flags_for_tg():
    source = _SERVICE.read_text(encoding="utf-8")
    assert "def merge_brand_channel_schedule_flags" in source
    assert 'for network in ("tg", "vk")' in source
    assert "COALESCE(c.role, 'source') = 'own'" in source


def merge_brand_channel_schedule_flags(result, *, platform, rows):
    by_user = {}
    for item in result:
        if item.get("platform") == platform:
            by_user[int(item["user_id"])] = item
    for row in rows:
        uid = int(row[0])
        ch_pub = bool(row[1])
        ch_col = bool(row[2])
        existing = by_user.get(uid)
        if existing:
            existing["publish_enabled"] = bool(existing.get("publish_enabled")) or ch_pub
            existing["collect_enabled"] = bool(existing.get("collect_enabled")) or ch_col
            continue
        result.append(
            {
                "user_id": uid,
                "platform": platform,
                "publish_enabled": ch_pub,
                "collect_enabled": ch_col,
                "schedule_type": "immediate",
                "time_intervals": [],
            }
        )


def test_merge_brand_channel_flags_ors_publish_onto_tg_profile():
    result = [
        {
            "user_id": 1,
            "platform": "tg",
            "publish_enabled": False,
            "collect_enabled": False,
            "schedule_type": "immediate",
            "time_intervals": [],
        }
    ]
    merge_brand_channel_schedule_flags(result, platform="tg", rows=[(1, True, False)])
    assert result[0]["publish_enabled"] is True
    assert len(result) == 1
