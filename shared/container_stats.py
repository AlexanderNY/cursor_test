"""Снимок CPU и памяти текущего контейнера через cgroup (v2 / v1).

Память — usage и limit контейнера (Python + дочерние процессы вроде Chromium).
CPU — процент от одного ядра с прошлого вызова в этом процессе (как docker stats).
Первый замер без предыдущей точки отдаёт cpu_percent=None.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# cgroup v2 (Docker / systemd)
_CGROUP_V2_MEMORY_CURRENT = Path("/sys/fs/cgroup/memory.current")
_CGROUP_V2_MEMORY_MAX = Path("/sys/fs/cgroup/memory.max")
_CGROUP_V2_CPU_STAT = Path("/sys/fs/cgroup/cpu.stat")

# cgroup v1
_CGROUP_V1_MEMORY_USAGE = Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")
_CGROUP_V1_MEMORY_LIMIT = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
_CGROUP_V1_CPU_USAGE = Path("/sys/fs/cgroup/cpuacct/cpuacct.usage")

# Лимит v1 без ограничения часто выглядит как огромное число (~2^63).
_V1_UNLIMITED_THRESHOLD = 1 << 62

_prev_cpu_usage_usec: Optional[int] = None
_prev_cpu_mono: Optional[float] = None


def reset_cpu_sample_for_tests() -> None:
    """Сбрасывает состояние дельты CPU (только для тестов)."""
    global _prev_cpu_usage_usec, _prev_cpu_mono
    _prev_cpu_usage_usec = None
    _prev_cpu_mono = None


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _parse_int(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    value = raw.strip()
    if not value or value == "max":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _read_memory() -> Tuple[Optional[int], Optional[int]]:
    """Возвращает (usage_bytes, limit_bytes). limit=None если лимита нет."""
    current_raw = _read_text(_CGROUP_V2_MEMORY_CURRENT)
    if current_raw is not None:
        usage = _parse_int(current_raw)
        limit = _parse_int(_read_text(_CGROUP_V2_MEMORY_MAX))
        return usage, limit

    usage = _parse_int(_read_text(_CGROUP_V1_MEMORY_USAGE))
    limit = _parse_int(_read_text(_CGROUP_V1_MEMORY_LIMIT))
    if limit is not None and limit >= _V1_UNLIMITED_THRESHOLD:
        limit = None
    return usage, limit


def _read_cpu_usage_usec() -> Optional[int]:
    """Накопленное CPU usage в микросекундах."""
    stat_raw = _read_text(_CGROUP_V2_CPU_STAT)
    if stat_raw is not None:
        for line in stat_raw.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] == "usage_usec":
                return _parse_int(parts[1])
        return None

    # v1: наносекунды
    nanos = _parse_int(_read_text(_CGROUP_V1_CPU_USAGE))
    if nanos is None:
        return None
    return nanos // 1000


def _cpu_percent(usage_usec: Optional[int], now_mono: float) -> Optional[float]:
    """Процент CPU относительно одного ядра с прошлого замера."""
    global _prev_cpu_usage_usec, _prev_cpu_mono

    if usage_usec is None:
        return None

    prev_usage = _prev_cpu_usage_usec
    prev_mono = _prev_cpu_mono
    _prev_cpu_usage_usec = usage_usec
    _prev_cpu_mono = now_mono

    if prev_usage is None or prev_mono is None:
        return None

    elapsed_sec = now_mono - prev_mono
    if elapsed_sec <= 0:
        return None

    delta_usec = usage_usec - prev_usage
    if delta_usec < 0:
        return None

    # 1e6 usec CPU за 1 сек wall = 100% одного ядра
    percent = (delta_usec / 1_000_000.0) / elapsed_sec * 100.0
    return round(percent, 1)


def get_container_stats() -> Dict[str, Any]:
    """Снимок нагрузки контейнера для вложения в /health.

    Returns:
        cpu_percent: float | None
        memory_bytes: int | None
        memory_limit_bytes: int | None
    """
    memory_bytes, memory_limit_bytes = _read_memory()
    usage_usec = _read_cpu_usage_usec()
    cpu_percent = _cpu_percent(usage_usec, time.monotonic())
    return {
        "cpu_percent": cpu_percent,
        "memory_bytes": memory_bytes,
        "memory_limit_bytes": memory_limit_bytes,
    }
