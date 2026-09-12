from pathlib import Path


def test_post_service_no_platform_table_inserts():
    source = Path(__file__).resolve().parents[1].joinpath("services", "post_service.py").read_text(
        encoding="utf-8"
    )
    for table in (
        "tg_posts",
        "vk_posts",
        "wp_posts",
        "tw_posts",
        "dzen_posts",
        "instagram_posts",
        "threads_posts",
        "cpost_posts",
        "url_posts",
    ):
        assert f"INSERT INTO {table}" not in source
        assert f"FROM {table}" not in source
        assert f"JOIN {table}" not in source
    assert "create_unified_post" in source
