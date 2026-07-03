from __future__ import annotations

import math
from dataclasses import dataclass

from config import cfg
from entities import Enemy, Pickup, Player, distance, normalize


@dataclass
class MobIntent:
    ax: float = 0.0
    ay: float = 0.0
    speed: float = 0.0
    state: str = "patrol"


def _entity_threats(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    margin: float,
    flee_radius: float,
) -> list[tuple[float, float, float]]:
    threats: list[tuple[float, float, float]] = []
    if player.radius > enemy.radius + margin:
        dist = distance(enemy.x, enemy.y, player.x, player.y)
        if dist < flee_radius:
            threats.append((player.x, player.y, dist))
    for other in enemies:
        if other is enemy:
            continue
        if other.radius > enemy.radius + margin:
            dist = distance(enemy.x, enemy.y, other.x, other.y)
            if dist < flee_radius:
                threats.append((other.x, other.y, dist))
    return threats


def _nearest_green(
    enemy: Enemy,
    pickups: list[Pickup],
    hunt_radius: float,
) -> Pickup | None:
    best: Pickup | None = None
    best_dist = hunt_radius
    for pickup in pickups:
        if pickup.kind != "green":
            continue
        dist = distance(enemy.x, enemy.y, pickup.x, pickup.y)
        if dist < best_dist:
            best_dist = dist
            best = pickup
    return best


def _nearest_prey(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    hunt_radius: float,
) -> tuple[float, float] | None:
    best: tuple[float, float] | None = None
    best_dist = hunt_radius
    if player.radius < enemy.radius:
        dist = distance(enemy.x, enemy.y, player.x, player.y)
        if dist < best_dist:
            best_dist = dist
            best = (player.x, player.y)
    for other in enemies:
        if other is enemy:
            continue
        if other.radius < enemy.radius:
            dist = distance(enemy.x, enemy.y, other.x, other.y)
            if dist < best_dist:
                best_dist = dist
                best = (other.x, other.y)
    return best


def compute_mob_intent(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    pickups: list[Pickup],
) -> MobIntent:
    if enemy.is_boss:
        dx, dy = normalize(player.x - enemy.x, player.y - enemy.y)
        return MobIntent(
            ax=dx,
            ay=dy,
            speed=float(cfg("boss_speed")),
            state="chase",
        )

    if enemy.state == "cooldown" and enemy.cooldown_left > 0:
        return MobIntent(state="cooldown")

    flee_radius = float(cfg("ai_flee_radius"))
    hunt_radius = float(cfg("ai_hunt_radius"))
    margin = float(cfg("ai_flee_size_margin"))

    threats = _entity_threats(enemy, player, enemies, margin, flee_radius)
    if threats:
        threats.sort(key=lambda item: item[2])
        tx, ty, _ = threats[0]
        dx, dy = normalize(enemy.x - tx, enemy.y - ty)
        return MobIntent(
            ax=dx,
            ay=dy,
            speed=float(cfg("enemy_speed_chase")),
            state="flee",
        )

    green = _nearest_green(enemy, pickups, hunt_radius)
    if green is not None:
        dx, dy = normalize(green.x - enemy.x, green.y - enemy.y)
        return MobIntent(
            ax=dx,
            ay=dy,
            speed=float(cfg("enemy_speed_patrol")),
            state="patrol",
        )

    prey = _nearest_prey(enemy, player, enemies, hunt_radius)
    if prey is not None:
        dx, dy = normalize(prey[0] - enemy.x, prey[1] - enemy.y)
        return MobIntent(
            ax=dx,
            ay=dy,
            speed=float(cfg("enemy_speed_chase")),
            state="chase",
        )

    if enemy.waypoints:
        target_x, target_y = enemy.waypoints[enemy.waypoint_index]
        if distance(enemy.x, enemy.y, target_x, target_y) < 8.0:
            enemy.waypoint_index = (enemy.waypoint_index + 1) % len(enemy.waypoints)
            target_x, target_y = enemy.waypoints[enemy.waypoint_index]
        dx, dy = normalize(target_x - enemy.x, target_y - enemy.y)
        return MobIntent(
            ax=dx,
            ay=dy,
            speed=float(cfg("enemy_speed_patrol")),
            state="patrol",
        )

    return MobIntent(state="patrol")
