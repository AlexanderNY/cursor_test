from __future__ import annotations

import random

from config import cfg
from entities import BossKind, Enemy, Player


BOSS_TITLES: dict[str, str] = {
    "titan": "Титан",
    "stalker": "Сталкер",
    "swarm": "Роевик",
    "leech": "Кровосос",
    "vortex": "Вихрь",
}


def pick_boss_kind(rng: random.Random) -> BossKind:
    kinds = cfg("boss_kinds")
    weights = cfg("boss_kind_weights")
    if not kinds:
        return "titan"
    if isinstance(weights, (list, tuple)) and len(weights) == len(kinds):
        return rng.choices(list(kinds), weights=list(weights), k=1)[0]
    return rng.choice(list(kinds))


def boss_title(boss_kind: BossKind) -> str:
    return BOSS_TITLES.get(boss_kind, "Босс")


def boss_damage_mult(boss_kind: BossKind) -> float:
    return float(cfg(f"boss_{boss_kind}_damage_mult"))


def boss_speed_mult(boss_kind: BossKind) -> float:
    return float(cfg(f"boss_{boss_kind}_speed_mult"))


def create_boss(x: float, y: float, boss_kind: BossKind) -> Enemy:
    radius = float(cfg(f"boss_{boss_kind}_radius"))
    health = radius * float(cfg(f"boss_{boss_kind}_health_mult"))
    return Enemy(
        x=x,
        y=y,
        radius=radius,
        health=health,
        max_health=health,
        state="chase",
        is_boss=True,
        boss_kind=boss_kind,
        boss_spawn_cooldown=float(cfg("boss_swarm_spawn_interval")),
    )


def apply_boss_hit(boss: Enemy, player: Player) -> float:
    damage = float(cfg("boss_hit_damage")) * boss_damage_mult(boss.boss_kind)
    player.red = max(0.0, player.red - damage)
    if boss.boss_kind == "leech":
        player.red = max(0.0, player.red - float(cfg("boss_leech_extra_drain")))
        growth = float(cfg("boss_leech_growth"))
        boss.radius += growth
        boss.health = min(boss.max_health, boss.health + growth * 0.5)
    return damage
