from pathlib import Path

_SERVICE = Path(__file__).resolve().parents[1] / "services" / "processing_service.py"


def test_processor_cycle_does_not_touch_platform_post_tables():
    source = _SERVICE.read_text(encoding="utf-8")
    for table in (
        "tg_posts",
        "vk_posts",
        "wp_posts",
        "url_posts",
        "tw_posts",
        "threads_posts",
        "instagram_posts",
        "dzen_posts",
        "cpost_posts",
    ):
        assert table not in source
    assert "PostsRepository" in source
    assert "post_targets" in source
    assert "ensure_targets" in source
    assert "SET to_tg" not in source


def test_orphan_review_sql_requires_no_post_targets():
    source = _SERVICE.read_text(encoding="utf-8")
    assert "FROM post_targets t" in source
    assert "t.status IN ('pending', 'ready', 'publishing')" in source
