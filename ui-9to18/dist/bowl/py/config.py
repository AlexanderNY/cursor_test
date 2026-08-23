from __future__ import annotations

import json
import math

_DEFAULT_CONFIG: dict = {
    "save_version": 4,
    "world_scale": 6.0,
    "base_player_radius": 18.0,
    "player_speed": 2200.0,
    "pickup_radius_min": 6.0,
    "pickup_radius_max": 14.0,
    "enemy_radius_min": 12.0,
    "enemy_radius_max": 24.0,
    "green_gain": 5.0,
    "red_gain": 5.0,
    "enemy_speed_patrol": 800.0,
    "enemy_speed_chase": 1400.0,
    "aggro_radius": 220.0,
    "hit_damage": 15.0,
    "knockback_distance": 60.0,
    "enemy_hit_cooldown": 1.2,
    "green_pickup_count": 45,
    "red_pickup_count": 45,
    "enemy_count": 12,
    "obstacle_count": 40,
    "waypoints_per_enemy": 4,
    "min_spawn_distance": 90.0,
    "eats_per_level": 10,
    "base_visibility_radius": 110.0,
    "eye_visibility_mult": 1.5,
    "eye_lightness_mult": 2.0,
    "leg_speed_mult": 1.1,
    "green_pickup_speed": 22.0,
    "pickup_wander_interval": 1.4,
    "hook_range": 220.0,
    "hook_pull_distance": 140.0,
    "hook_cooldown": 1.1,
    "spike_range": 55.0,
    "spike_arc": math.pi / 3.0,
    "spike_cooldown": 0.9,
    "spike_stun": 2.0,
    "obstacle_kinds": ("paper", "toothbrush"),
    "match_timer_sec": 120.0,
    "whirlpool_duration_sec": 10.0,
    "whirlpool_pull_speed": 180.0,
    "whirlpool_flee_speed": 160.0,
    "whirlpool_radius": 120.0,
    "whirlpool_spin_speed": 2.5,
    "boss_radius": 48.0,
    "boss_speed": 200.0,
    "boss_hit_damage": 25.0,
    "boss_spawn_distance": 280.0,
}

CFG: dict = dict(_DEFAULT_CONFIG)


def load_config_from_json(raw: str) -> None:
    global CFG
    data = json.loads(raw)
    merged = dict(_DEFAULT_CONFIG)
    merged.update(data)
    if isinstance(merged.get("obstacle_kinds"), list):
        merged["obstacle_kinds"] = tuple(merged["obstacle_kinds"])
    CFG = merged


def cfg(key: str):
    return CFG[key]
