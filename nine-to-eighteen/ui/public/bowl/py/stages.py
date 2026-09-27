from __future__ import annotations

from config import CFG, cfg

_DEFAULT_ENEMY_CATALOG: dict[str, dict] = {
    "grazer": {
        "behavior": "grazer",
        "title": "Травоядный",
        "color": "#22c55e",
        "patrol_mult": 0.95,
        "chase_mult": 1.0,
        "green_mult": 1.25,
        "radius_mult": 1.0,
        "damage_mult": 1.0,
        "strafe": 0.0,
        "aura": 0.0,
        "drain": 0.0,
    },
    "hunter": {
        "behavior": "hunter",
        "title": "Охотник",
        "color": "#ef4444",
        "patrol_mult": 0.85,
        "chase_mult": 1.35,
        "green_mult": 1.0,
        "radius_mult": 1.0,
        "damage_mult": 1.0,
        "strafe": 0.0,
        "aura": 0.0,
        "drain": 0.0,
    },
    "lurker": {
        "behavior": "lurker",
        "title": "Засадник",
        "color": "#f59e0b",
        "patrol_mult": 0.9,
        "chase_mult": 1.95,
        "green_mult": 1.0,
        "radius_mult": 1.0,
        "damage_mult": 1.0,
        "strafe": 0.0,
        "aura": 0.0,
        "drain": 0.0,
    },
    "sludge": {
        "behavior": "grazer",
        "title": "Ил",
        "color": "#65a30d",
        "patrol_mult": 0.75,
        "chase_mult": 1.0,
        "green_mult": 1.1,
        "radius_mult": 1.35,
        "damage_mult": 1.1,
        "strafe": 0.0,
        "aura": 0.0,
        "drain": 0.0,
    },
    "rat": {
        "behavior": "hunter",
        "title": "Крыса",
        "color": "#a16207",
        "patrol_mult": 1.1,
        "chase_mult": 1.5,
        "green_mult": 1.0,
        "radius_mult": 0.95,
        "damage_mult": 1.0,
        "strafe": 0.55,
        "aura": 0.0,
        "drain": 0.0,
    },
    "roach": {
        "behavior": "lurker",
        "title": "Таракан",
        "color": "#854d0e",
        "patrol_mult": 1.15,
        "chase_mult": 2.1,
        "green_mult": 1.0,
        "radius_mult": 0.9,
        "damage_mult": 0.9,
        "strafe": 0.2,
        "aura": 0.0,
        "drain": 0.0,
    },
    "fry": {
        "behavior": "grazer",
        "title": "Малёк",
        "color": "#4ade80",
        "patrol_mult": 1.35,
        "chase_mult": 1.0,
        "green_mult": 1.4,
        "radius_mult": 0.8,
        "damage_mult": 0.8,
        "strafe": 0.25,
        "aura": 0.0,
        "drain": 0.0,
    },
    "leech_fish": {
        "behavior": "hunter",
        "title": "Пиявка",
        "color": "#be123c",
        "patrol_mult": 1.0,
        "chase_mult": 1.45,
        "green_mult": 1.0,
        "radius_mult": 1.0,
        "damage_mult": 0.95,
        "strafe": 0.15,
        "aura": 0.0,
        "drain": 6.0,
    },
    "stoneback": {
        "behavior": "lurker",
        "title": "Камень-спина",
        "color": "#78716c",
        "patrol_mult": 0.7,
        "chase_mult": 1.85,
        "green_mult": 1.0,
        "radius_mult": 1.2,
        "damage_mult": 1.2,
        "strafe": 0.0,
        "aura": 0.0,
        "drain": 0.0,
    },
    "bacterium": {
        "behavior": "grazer",
        "title": "Бактерия",
        "color": "#a3e635",
        "patrol_mult": 1.2,
        "chase_mult": 1.0,
        "green_mult": 1.3,
        "radius_mult": 0.7,
        "damage_mult": 0.7,
        "strafe": 0.35,
        "aura": 0.0,
        "drain": 0.0,
    },
    "chlorine": {
        "behavior": "hunter",
        "title": "Хлор",
        "color": "#67e8f9",
        "patrol_mult": 0.95,
        "chase_mult": 1.25,
        "green_mult": 1.0,
        "radius_mult": 1.05,
        "damage_mult": 1.15,
        "strafe": 0.2,
        "aura": 55.0,
        "drain": 0.0,
    },
    "filter": {
        "behavior": "lurker",
        "title": "Фильтр",
        "color": "#94a3b8",
        "patrol_mult": 0.85,
        "chase_mult": 1.7,
        "green_mult": 1.0,
        "radius_mult": 1.15,
        "damage_mult": 1.05,
        "strafe": 0.0,
        "aura": 0.0,
        "drain": 0.0,
    },
    "school": {
        "behavior": "grazer",
        "title": "Косяк",
        "color": "#38bdf8",
        "patrol_mult": 1.45,
        "chase_mult": 1.0,
        "green_mult": 1.35,
        "radius_mult": 0.85,
        "damage_mult": 0.85,
        "strafe": 0.45,
        "aura": 0.0,
        "drain": 0.0,
    },
    "jelly": {
        "behavior": "lurker",
        "title": "Медуза",
        "color": "#c084fc",
        "patrol_mult": 0.8,
        "chase_mult": 1.6,
        "green_mult": 1.0,
        "radius_mult": 1.1,
        "damage_mult": 1.0,
        "strafe": 0.1,
        "aura": 70.0,
        "drain": 0.0,
    },
    "crab": {
        "behavior": "hunter",
        "title": "Краб",
        "color": "#fb7185",
        "patrol_mult": 1.05,
        "chase_mult": 1.4,
        "green_mult": 1.0,
        "radius_mult": 1.1,
        "damage_mult": 1.2,
        "strafe": 0.85,
        "aura": 0.0,
        "drain": 0.0,
    },
}

_DEFAULT_STAGES: list[dict] = [
    {
        "id": "toilet",
        "title": "Унитаз",
        "hazard": "flush",
        "hazard_title": "Смыв",
        "boss": "titan",
        "boss_title": "Титан-пробка",
        "enemy_kinds": ["grazer", "hunter", "lurker"],
        "enemy_weights": [4, 3, 3],
        "obstacle_kinds": ["paper", "toothbrush"],
        "floor": "#e8eef5",
        "water_inner": "#1e4d7a",
        "water_mid": "rgba(37, 99, 168, 0.75)",
        "water_outer": "rgba(15, 45, 82, 0.95)",
        "rim": "#cbd5e1",
        "rim_stroke": "#94a3b8",
    },
    {
        "id": "sewer",
        "title": "Канализация",
        "hazard": "gas",
        "hazard_title": "Метан",
        "boss": "swarm",
        "boss_title": "Рой труб",
        "enemy_kinds": ["sludge", "rat", "roach"],
        "enemy_weights": [3, 4, 3],
        "obstacle_kinds": ["pipe", "pipe"],
        "floor": "#1c1917",
        "water_inner": "#365314",
        "water_mid": "rgba(77, 124, 15, 0.7)",
        "water_outer": "rgba(26, 46, 5, 0.95)",
        "rim": "#44403c",
        "rim_stroke": "#78716c",
    },
    {
        "id": "creek",
        "title": "Ручей сточных вод",
        "hazard": "current",
        "hazard_title": "Течение",
        "boss": "leech",
        "boss_title": "Пиявка-мать",
        "enemy_kinds": ["fry", "leech_fish", "stoneback"],
        "enemy_weights": [4, 3, 3],
        "obstacle_kinds": ["log", "log"],
        "floor": "#ecfccb",
        "water_inner": "#166534",
        "water_mid": "rgba(21, 128, 61, 0.7)",
        "water_outer": "rgba(20, 83, 45, 0.95)",
        "rim": "#bbf7d0",
        "rim_stroke": "#4ade80",
    },
    {
        "id": "plant",
        "title": "Очистные",
        "hazard": "chlorine",
        "hazard_title": "Хлор",
        "boss": "vortex",
        "boss_title": "Вихрь хлора",
        "enemy_kinds": ["bacterium", "chlorine", "filter"],
        "enemy_weights": [4, 3, 3],
        "obstacle_kinds": ["grate", "grate"],
        "floor": "#e0f2fe",
        "water_inner": "#0e7490",
        "water_mid": "rgba(6, 182, 212, 0.65)",
        "water_outer": "rgba(8, 51, 68, 0.95)",
        "rim": "#bae6fd",
        "rim_stroke": "#38bdf8",
    },
    {
        "id": "sea",
        "title": "Море",
        "hazard": "waves",
        "hazard_title": "Волны",
        "boss": "stalker",
        "boss_title": "Акула-сталкер",
        "enemy_kinds": ["school", "jelly", "crab"],
        "enemy_weights": [4, 3, 3],
        "obstacle_kinds": ["rock", "rock"],
        "floor": "#0c4a6e",
        "water_inner": "#0369a1",
        "water_mid": "rgba(14, 165, 233, 0.55)",
        "water_outer": "rgba(12, 74, 110, 0.95)",
        "rim": "#075985",
        "rim_stroke": "#38bdf8",
    },
]


def enemy_catalog() -> dict[str, dict]:
    raw = CFG.get("enemy_catalog")
    if isinstance(raw, dict) and raw:
        merged = dict(_DEFAULT_ENEMY_CATALOG)
        for key, value in raw.items():
            if isinstance(value, dict):
                base = dict(merged.get(str(key), {}))
                base.update(value)
                merged[str(key)] = base
        return merged
    return dict(_DEFAULT_ENEMY_CATALOG)


def stages_list() -> list[dict]:
    raw = CFG.get("stages")
    if isinstance(raw, list) and raw:
        return list(raw)
    return list(_DEFAULT_STAGES)


def stage_count() -> int:
    return max(1, len(stages_list()))


def clamp_stage(stage: int) -> int:
    return max(1, min(int(stage), stage_count()))


def get_stage(stage: int) -> dict:
    stages = stages_list()
    index = clamp_stage(stage) - 1
    return dict(stages[index])


def get_enemy_def(kind: str) -> dict:
    catalog = enemy_catalog()
    if kind in catalog:
        return dict(catalog[kind])
    return dict(catalog.get("grazer", _DEFAULT_ENEMY_CATALOG["grazer"]))


def enemy_behavior(kind: str) -> str:
    behavior = str(get_enemy_def(kind).get("behavior", "grazer"))
    if behavior in ("grazer", "hunter", "lurker"):
        return behavior
    return "grazer"


def score_value(key: str) -> int:
    scores = CFG.get("score")
    if isinstance(scores, dict) and key in scores:
        return int(scores[key])
    defaults = {
        "green": 10,
        "red": 25,
        "yellow": 80,
        "enemy": 40,
        "hazard": 150,
        "boss_kill": 400,
        "stage_exit": 250,
        "victory": 1000,
    }
    return int(defaults.get(key, 0))


def hazard_duration() -> float:
    return float(cfg("whirlpool_duration_sec"))
