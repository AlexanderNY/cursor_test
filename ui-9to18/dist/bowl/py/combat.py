from __future__ import annotations

import math
import random

from config import cfg
from entities import Enemy, Pickup, Player, angle_diff, distance


def can_eat_entity(eater_radius: float, target_radius: float) -> bool:
    return eater_radius > target_radius


def grow_from_green(entity_radius: float) -> float:
    return entity_radius + float(cfg("green_growth"))


def apply_green_pickup(entity, pickup: Pickup) -> None:
    entity.radius = grow_from_green(entity.radius)
    if isinstance(entity, Player):
        entity.green = min(100.0, entity.green + float(cfg("green_gain")))


def apply_red_pickup(player: Player, pickup: Pickup) -> None:
    player.red = min(100.0, player.red + float(cfg("red_gain")))
    player.radius += float(cfg("red_growth"))


def init_enemy_health(radius: float) -> float:
    return radius


def apply_spike_damage(enemy: Enemy, damage: float) -> bool:
    enemy.health -= damage
    enemy.state = "cooldown"
    enemy.cooldown_left = float(cfg("spike_stun"))
    return enemy.health <= 0.0


def split_enemy_to_greens(enemy: Enemy, rng: random.Random) -> list[Pickup]:
    count = rng.randint(
        int(cfg("split_min_greens")),
        int(cfg("split_max_greens")),
    )
    pickups: list[Pickup] = []
    chunk_radius = max(float(cfg("pickup_radius_min")), enemy.radius / max(count, 1) * 0.6)
    for _ in range(count):
        angle = rng.uniform(0.0, math.tau)
        offset = enemy.radius * 0.35
        pickups.append(
            Pickup(
                x=enemy.x + math.cos(angle) * offset,
                y=enemy.y + math.sin(angle) * offset,
                kind="green",
                radius=chunk_radius,
            )
        )
    return pickups


def try_consume_entity(
    eater,
    target: Enemy,
    is_player: bool,
) -> bool:
    if not can_eat_entity(eater.radius, target.radius):
        return False
    eater.radius = grow_from_green(eater.radius)
    if isinstance(eater, Player):
        eater.enemies_eaten += 1
    return True


def find_spike_target(
    attacker_x: float,
    attacker_y: float,
    facing: float,
    spike_range: float,
    spike_arc: float,
    enemies: list[Enemy],
) -> Enemy | None:
    best: Enemy | None = None
    best_dist = spike_range + 999.0
    for enemy in enemies:
        dist = distance(attacker_x, attacker_y, enemy.x, enemy.y)
        if dist > spike_range + enemy.radius:
            continue
        angle = math.atan2(enemy.y - attacker_y, enemy.x - attacker_x)
        if abs(angle_diff(angle, facing)) <= spike_arc / 2.0 and dist < best_dist:
            best_dist = dist
            best = enemy
    return best
