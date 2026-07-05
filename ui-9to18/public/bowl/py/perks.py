from __future__ import annotations

import json

_PERKS: dict = {}
DEFAULT_PERK_IDS = ("leg", "eye", "tentacle", "spike")


def load_perks_from_json(raw: str) -> None:
    global _PERKS
    _PERKS = json.loads(raw)


def get_perk_def(perk_id: str) -> dict:
    return _PERKS.get(perk_id, {})


def get_max_level(perk_id: str) -> int:
    return int(get_perk_def(perk_id).get("max_level", 0))


def default_perk_levels() -> dict[str, int]:
    return {perk_id: 0 for perk_id in DEFAULT_PERK_IDS}


def get_level_stats(perk_id: str, level: int) -> dict:
    if level < 0:
        return {}
    levels = get_perk_def(perk_id).get("levels", {})
    return dict(levels.get(str(level), {}))


def get_player_level(perk_levels: dict[str, int], perk_id: str) -> int:
    return int(perk_levels.get(perk_id, 0))


def can_upgrade(perk_levels: dict[str, int], perk_id: str) -> bool:
    return get_player_level(perk_levels, perk_id) < get_max_level(perk_id)


def upgrade_perk(perk_levels: dict[str, int], perk_id: str) -> dict[str, int]:
    updated = dict(perk_levels)
    current = get_player_level(updated, perk_id)
    if current < get_max_level(perk_id):
        updated[perk_id] = current + 1
    return updated


def _speed_bonus_from_stats(stats: dict) -> float:
    speed_mult = float(stats.get("speed_mult", 1.0))
    if speed_mult <= 1.0:
        return 0.0
    return speed_mult - 1.0


def perk_speed_mult(perk_levels: dict[str, int]) -> float:
    bonus = 0.0
    for perk_id in ("leg", "eye"):
        stats = get_level_stats(perk_id, get_player_level(perk_levels, perk_id))
        bonus += _speed_bonus_from_stats(stats)
    return 1.0 + bonus


def perk_visibility(perk_levels: dict[str, int], base: float) -> tuple[float, float]:
    return base, 1.0


def perk_limb_count(perk_levels: dict[str, int], perk_id: str) -> int:
    level = get_player_level(perk_levels, perk_id)
    stats = get_level_stats(perk_id, level)
    if stats.get("limb_count") is not None:
        return int(stats["limb_count"])
    return level * 2 if level > 0 else 0


def perk_tentacle_stats(perk_levels: dict[str, int]) -> tuple[float, float, int]:
    level = get_player_level(perk_levels, "tentacle")
    stats = get_level_stats("tentacle", level)
    if not stats:
        return 0.0, 0.0, 0
    return (
        float(stats.get("grab_range", 0)),
        float(stats.get("grab_duration", 0)),
        int(stats.get("limb_count", level * 2 if level > 0 else 2)),
    )


def perk_spike_contact_stats(perk_levels: dict[str, int]) -> tuple[float, float, int]:
    level = get_player_level(perk_levels, "spike")
    stats = get_level_stats("spike", level)
    if not stats:
        return 0.0, 0.0, 0
    return (
        float(stats.get("damage", 0)),
        float(stats.get("spike_length", 0)),
        int(stats.get("spike_count", 0)),
    )


def active_perk_ids(perk_levels: dict[str, int]) -> list[str]:
    return list(DEFAULT_PERK_IDS)


def sanitize_perk_levels(raw: dict) -> dict[str, int]:
    result = default_perk_levels()
    for perk_id, level in raw.items():
        perk_key = str(perk_id)
        if perk_key not in result:
            continue
        max_level = get_max_level(perk_key)
        if max_level <= 0:
            continue
        result[perk_key] = max(0, min(int(level), max_level))
    return result
