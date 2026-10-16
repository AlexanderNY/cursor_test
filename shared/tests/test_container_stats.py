"""Tests for shared.container_stats (cgroup memory / CPU)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import shared.container_stats as cs


def _fake_read(files: Dict[Path, Optional[str]]):
    def _read_text(path: Path) -> Optional[str]:
        return files.get(path)

    return _read_text


def test_no_cgroup_returns_nulls(monkeypatch):
    cs.reset_cpu_sample_for_tests()
    monkeypatch.setattr(cs, "_read_text", _fake_read({}))
    stats = cs.get_container_stats()
    assert stats == {
        "cpu_percent": None,
        "memory_bytes": None,
        "memory_limit_bytes": None,
    }


def test_cgroup_v2_memory_and_limit(monkeypatch):
    cs.reset_cpu_sample_for_tests()
    monkeypatch.setattr(
        cs,
        "_read_text",
        _fake_read(
            {
                cs._CGROUP_V2_MEMORY_CURRENT: "188743680",
                cs._CGROUP_V2_MEMORY_MAX: "805306368",
                cs._CGROUP_V2_CPU_STAT: "usage_usec 1000000\nuser_usec 500000\n",
            }
        ),
    )
    stats = cs.get_container_stats()
    assert stats["memory_bytes"] == 188743680
    assert stats["memory_limit_bytes"] == 805306368
    assert stats["cpu_percent"] is None  # first sample


def test_cgroup_v2_memory_max_unlimited(monkeypatch):
    cs.reset_cpu_sample_for_tests()
    monkeypatch.setattr(
        cs,
        "_read_text",
        _fake_read(
            {
                cs._CGROUP_V2_MEMORY_CURRENT: "1024",
                cs._CGROUP_V2_MEMORY_MAX: "max",
            }
        ),
    )
    stats = cs.get_container_stats()
    assert stats["memory_bytes"] == 1024
    assert stats["memory_limit_bytes"] is None


def test_cpu_percent_delta(monkeypatch):
    cs.reset_cpu_sample_for_tests()
    files: Dict[Path, Optional[str]] = {
        cs._CGROUP_V2_MEMORY_CURRENT: "1000",
        cs._CGROUP_V2_MEMORY_MAX: "2000",
        cs._CGROUP_V2_CPU_STAT: "usage_usec 0\n",
    }
    monkeypatch.setattr(cs, "_read_text", _fake_read(files))

    monos = iter([100.0, 101.0])
    monkeypatch.setattr(cs.time, "monotonic", lambda: next(monos))

    first = cs.get_container_stats()
    assert first["cpu_percent"] is None

    files[cs._CGROUP_V2_CPU_STAT] = "usage_usec 500000\n"
    second = cs.get_container_stats()
    # 0.5 sec CPU over 1 sec wall = 50%
    assert second["cpu_percent"] == 50.0


def test_cgroup_v1_fallback(monkeypatch):
    cs.reset_cpu_sample_for_tests()
    monkeypatch.setattr(
        cs,
        "_read_text",
        _fake_read(
            {
                cs._CGROUP_V1_MEMORY_USAGE: "4096",
                cs._CGROUP_V1_MEMORY_LIMIT: "8192",
                cs._CGROUP_V1_CPU_USAGE: "2000000",  # 2 ms in ns
            }
        ),
    )
    monos = iter([10.0, 11.0])
    monkeypatch.setattr(cs.time, "monotonic", lambda: next(monos))

    first = cs.get_container_stats()
    assert first["memory_bytes"] == 4096
    assert first["memory_limit_bytes"] == 8192
    assert first["cpu_percent"] is None

    # +1_000_000_000 ns (= 1_000_000 usec) over 1 sec = 100%
    monkeypatch.setattr(
        cs,
        "_read_text",
        _fake_read(
            {
                cs._CGROUP_V1_MEMORY_USAGE: "4096",
                cs._CGROUP_V1_MEMORY_LIMIT: "8192",
                cs._CGROUP_V1_CPU_USAGE: "1002000000",
            }
        ),
    )
    second = cs.get_container_stats()
    assert second["cpu_percent"] == 100.0


def test_cgroup_v1_unlimited_limit(monkeypatch):
    cs.reset_cpu_sample_for_tests()
    huge = str((1 << 63) - 1)
    monkeypatch.setattr(
        cs,
        "_read_text",
        _fake_read(
            {
                cs._CGROUP_V1_MEMORY_USAGE: "100",
                cs._CGROUP_V1_MEMORY_LIMIT: huge,
            }
        ),
    )
    stats = cs.get_container_stats()
    assert stats["memory_bytes"] == 100
    assert stats["memory_limit_bytes"] is None
