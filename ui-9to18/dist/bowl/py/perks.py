from __future__ import annotations

import json

_PERKS: dict = {}


def load_perks_from_json(raw: str) -> None:
    global _PERKS
    _PERKS = json.loads(raw)


def get_perk_def(perk_id: str) -> dict:
    return _PERKS.get(perk_id, {})


def get_max_level(perk_id: str) -> int:
    return int(get_perk_def(perk_id).get("max_level", 0))


def get_level_stats(perk_id: str, level: int) -> dict:
    if level <= 0:
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


def perk_speed_mult(perk_levels: dict[str, int]) -> float:
    stats = get_level_stats("leg", get_player_level(perk_levels, "leg"))
    return float(stats.get("speed_mult", 1.0))


def perk_visibility(perk_levels: dict[str, int], base: float) -> tuple[float, float]:
    level = get_player_level(perk_levels, "eye")
    stats = get_level_stats("eye", level)
    if not stats:
        return base, 1.0
    return base * float(stats.get("visibility_mult", 1.0)), float(stats.get("lightness_mult", 1.0))


def perk_hook_stats(perk_levels: dict[str, int]) -> tuple[float, float, float]:
    level = get_player_level(perk_levels, "tentacle")
    stats = get_level_stats("tentacle", level)
    if not stats:
        return 0.0, 0.0, 999.0
    return (
        float(stats.get("hook_range", 0)),
        float(stats.get("hook_pull", 0)),
        float(stats.get("hook_cooldown", 999)),
    )


def perk_spike_stats(perk_levels: dict[str, int]) -> tuple[float, float, float, float]:
    level = get_player_level(perk_levels, "spike")
    stats = get_level_stats("spike", level)
    if not stats:
        return 0.0, 0.0, 0.0, 999.0
    return (
        float(stats.get("damage", 0)),
        float(stats.get("range", 0)),
        float(stats.get("arc", 0)),
        float(stats.get("cooldown", 999)),
    )


def active_perk_ids(perk_levels: dict[str, int]) -> list[str]:
    return [pid for pid, lvl in perk_levels.items() if lvl > 0]
