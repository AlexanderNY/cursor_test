from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_instagram_collector_writes_hub_posts():
    source = (ROOT / "instagram-bot" / "services" / "post_collector.py").read_text(
        encoding="utf-8"
    )
    assert "INSERT INTO instagram_posts" not in source
    assert "InboundPostCreate" in source
    assert 'source_platform="instagram"' in source


def test_tw_collector_writes_hub_posts():
    source = (ROOT / "tw-bot" / "services" / "feed_collector.py").read_text(encoding="utf-8")
    assert "INSERT INTO tw_posts" not in source
    assert "InboundPostCreate" in source
    assert 'source_platform="tw"' in source


def test_dzen_collectors_write_hub_posts():
    selenium = (ROOT / "dzen-bot" / "services" / "dzen_feed_collector.py").read_text(
        encoding="utf-8"
    )
    rss = (ROOT / "collector" / "services" / "dzen_rss_reader_service.py").read_text(
        encoding="utf-8"
    )
    assert "INSERT INTO dzen_posts" not in selenium
    assert "INSERT INTO dzen_posts" not in rss
    assert 'source_platform="dzen"' in selenium
    assert 'source_platform="dzen"' in rss
