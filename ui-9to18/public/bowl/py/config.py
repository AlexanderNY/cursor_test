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
    "obstacle_count": 6,
    "waypoints_per_enemy": 4,
    "min_spawn_distance": 90.0,
    "eats_per_level": 10,
    "base_visibility_radius": 110.0,
    "eye_visibility_mult": 1.5,
    "eye_lightness_mult": 2.0,
    "leg_speed_mult": 1.1,
    "green_pickup_speed": 22.0,
    "green_flee_radius": 150.0,
    "green_flee_speed": 320.0,
    "green_enemy_flee_radius": 190.0,
    "pickup_wander_interval": 1.1,
    "nutrient_count": 20,
    "nutrient_radius_x_min": 32.0,
    "nutrient_radius_x_max": 58.0,
    "nutrient_radius_y_ratio": 0.62,
    "nutrient_seek_radius": 340.0,
    "nutrient_seek_speed": 240.0,
    "red_hunt_radius": 420.0,
    "red_green_vision_radius": 110.0,
    "red_hunt_speed": 520.0,
    "red_eats_green_growth": 1.6,
    "red_pickup_max_radius": 36.0,
    "ram_min_speed": 850.0,
    "ram_base_damage": 14.0,
    "ram_sprint_mult": 1.75,
    "ram_cooldown": 0.5,
    "ram_stun": 0.65,
    "stamina_max": 100.0,
    "stamina_drain_per_sec": 35.0,
    "stamina_regen_per_sec": 22.0,
    "sprint_speed_mult": 1.65,
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
    "whirlpool_pull_speed": 750.0,
    "whirlpool_flee_speed": 2600.0,
    "whirlpool_player_speed_mult": 1.4,
    "whirlpool_radius": 120.0,
    "whirlpool_spin_speed": 2.2,
    "boss_radius": 48.0,
    "boss_speed": 200.0,
    "boss_hit_damage": 25.0,
    "boss_spawn_distance": 280.0,
    "bowl_rim_margin": 48.0,
    "edge_spawn_rim_inset": 24.0,
    "boss_kinds": ("titan", "stalker", "swarm", "leech", "vortex"),
    "boss_kind_weights": (1, 1, 1, 1, 1),
    "boss_titan_radius": 56.0,
    "boss_titan_health_mult": 2.2,
    "boss_titan_speed_mult": 0.62,
    "boss_titan_damage_mult": 1.55,
    "boss_stalker_radius": 44.0,
    "boss_stalker_health_mult": 1.5,
    "boss_stalker_speed_mult": 1.05,
    "boss_stalker_damage_mult": 1.0,
    "boss_stalker_orbit_radius": 190.0,
    "boss_stalker_dash_radius": 115.0,
    "boss_stalker_dash_duration": 1.4,
    "boss_stalker_dash_speed_mult": 1.75,
    "boss_swarm_radius": 46.0,
    "boss_swarm_health_mult": 1.65,
    "boss_swarm_speed_mult": 0.92,
    "boss_swarm_damage_mult": 0.95,
    "boss_swarm_spawn_interval": 9.0,
    "boss_swarm_max_minions": 3,
    "boss_swarm_minion_radius": 14.0,
    "boss_swarm_keep_distance": 95.0,
    "boss_leech_radius": 40.0,
    "boss_leech_health_mult": 1.15,
    "boss_leech_speed_mult": 1.42,
    "boss_leech_damage_mult": 0.85,
    "boss_leech_extra_drain": 8.0,
    "boss_leech_growth": 1.2,
    "boss_vortex_radius": 50.0,
    "boss_vortex_health_mult": 1.85,
    "boss_vortex_speed_mult": 1.0,
    "boss_vortex_damage_mult": 1.1,
    "boss_vortex_cycle_sec": 4.5,
    "boss_vortex_lunge_share": 0.35,
    "boss_vortex_lunge_speed_mult": 1.55,
    "boss_vortex_orbit_radius": 175.0,
    "boss_vortex_pull_radius": 210.0,
    "boss_vortex_pull_strength": 420.0,
    "ai_flee_radius": 200.0,
    "ai_flee_size_margin": 2.0,
    "ai_hunt_radius": 240.0,
    "enemy_kinds": ("grazer", "hunter", "lurker"),
    "enemy_kind_weights": (4, 3, 3),
    "grazer_patrol_speed_mult": 0.95,
    "grazer_green_speed_mult": 1.25,
    "hunter_aggro_radius": 300.0,
    "hunter_chase_speed_mult": 1.35,
    "hunter_patrol_speed_mult": 0.85,
    "lurker_ambush_radius": 130.0,
    "lurker_chase_radius": 320.0,
    "lurker_burst_duration": 2.8,
    "lurker_burst_speed_mult": 1.95,
    "lurker_patrol_speed_mult": 0.45,
}

CFG: dict = dict(_DEFAULT_CONFIG)


def load_config_from_json(raw: str) -> None:
    global CFG
    data = json.loads(raw)
    merged = dict(_DEFAULT_CONFIG)
    merged.update(data)
    if isinstance(merged.get("obstacle_kinds"), list):
        merged["obstacle_kinds"] = tuple(merged["obstacle_kinds"])
    if isinstance(merged.get("enemy_kinds"), list):
        merged["enemy_kinds"] = tuple(merged["enemy_kinds"])
    if isinstance(merged.get("enemy_kind_weights"), list):
        merged["enemy_kind_weights"] = tuple(merged["enemy_kind_weights"])
    if isinstance(merged.get("boss_kinds"), list):
        merged["boss_kinds"] = tuple(merged["boss_kinds"])
    if isinstance(merged.get("boss_kind_weights"), list):
        merged["boss_kind_weights"] = tuple(merged["boss_kind_weights"])
    CFG = merged


def cfg(key: str):
    return CFG[key]
