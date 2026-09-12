from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_collector_has_no_etl_copy_jobs():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "collect_service" not in main
    assert "distribute_service" not in main
    assert "run_collect_cycle" not in main
    assert "run_distribute_cycle" not in main
    assert "dzen_rss_reader_service" in main
    assert "post_targets" in main
    assert not (ROOT / "services" / "collect_service.py").exists()
    assert not (ROOT / "services" / "distribute_service.py").exists()
