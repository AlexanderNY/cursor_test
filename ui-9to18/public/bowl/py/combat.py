from __future__ import annotations

import math
import random

from config import cfg
from entities import Enemy, Pickup, Player, WorldObject, angle_diff, clamp, distance


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


def apply_red_eats_green(red: Pickup, green: Pickup) -> None:
    red.radius += float(cfg("red_eats_green_growth"))
    if red.radius > float(cfg("red_pickup_max_radius")):
        red.radius = float(cfg("red_pickup_max_radius"))


def apply_ram_damage(enemy: Enemy, damage: float) -> bool:
    enemy.health -= damage
    enemy.state = "cooldown"
    enemy.cooldown_left = float(cfg("ram_stun"))
    return enemy.health <= 0.0


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


def _is_in_front(
    origin_x: float,
    origin_y: float,
    target_x: float,
    target_y: float,
    facing: float,
    half_arc: float,
) -> bool:
    dx = target_x - origin_x
    dy = target_y - origin_y
    if math.hypot(dx, dy) <= 1e-6:
        return False
    angle = math.atan2(dy, dx)
    return abs(angle_diff(angle, facing)) <= half_arc


def find_grab_target_in_front(
    player_x: float,
    player_y: float,
    facing: float,
    grab_range: float,
    pickups: list[Pickup],
    obstacles: list[WorldObject],
) -> tuple[str, int] | None:
    half_arc = math.pi / 3.0
    best_kind: str | None = None
    best_key = -1
    best_dist = grab_range + 999.0

    for index, pickup in enumerate(pickups):
        if pickup.attached_to is not None:
            continue
        dist = distance(player_x, player_y, pickup.x, pickup.y)
        if dist > grab_range + pickup.radius:
            continue
        if not _is_in_front(player_x, player_y, pickup.x, pickup.y, facing, half_arc):
            continue
        if dist < best_dist:
            best_dist = dist
            best_kind = "pickup"
            best_key = index

    for obstacle in obstacles:
        dist = distance(player_x, player_y, obstacle.x, obstacle.y)
        if dist > grab_range + obstacle.radius:
            continue
        if not _is_in_front(player_x, player_y, obstacle.x, obstacle.y, facing, half_arc):
            continue
        if dist < best_dist:
            best_dist = dist
            best_kind = "obstacle"
            best_key = obstacle.id

    if best_kind is None:
        return None
    return best_kind, best_key


def spike_spread_angles(base_angle: float, spike_count: int) -> list[float]:
    if spike_count <= 1:
        return [base_angle]
    if spike_count == 2:
        spread = 0.22
        return [base_angle - spread, base_angle + spread]
    spread = 0.38
    step = spread / 1.5
    return [
        base_angle - spread,
        base_angle - step,
        base_angle + step,
        base_angle + spread,
    ]


def segment_circle_intersects(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    cx: float,
    cy: float,
    radius: float,
) -> bool:
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-6:
        return distance(x1, y1, cx, cy) <= radius
    t = clamp(((cx - x1) * dx + (cy - y1) * dy) / length_sq, 0.0, 1.0)
    closest_x = x1 + dx * t
    closest_y = y1 + dy * t
    return distance(closest_x, closest_y, cx, cy) <= radius


def spike_segments(
    origin_x: float,
    origin_y: float,
    body_radius: float,
    direction: float,
    spike_length: float,
    spike_count: int,
) -> list[tuple[float, float, float, float]]:
    segments: list[tuple[float, float, float, float]] = []
    start_offset = body_radius * 0.55
    for angle in spike_spread_angles(direction, spike_count):
        start_x = origin_x + math.cos(angle) * start_offset
        start_y = origin_y + math.sin(angle) * start_offset
        end_x = origin_x + math.cos(angle) * (start_offset + spike_length)
        end_y = origin_y + math.sin(angle) * (start_offset + spike_length)
        segments.append((start_x, start_y, end_x, end_y))
    return segments


def enemy_hits_spike_segments(
    enemy: Enemy,
    segments: list[tuple[float, float, float, float]],
) -> bool:
    hit_radius = enemy.radius * 0.92
    for x1, y1, x2, y2 in segments:
        if segment_circle_intersects(x1, y1, x2, y2, enemy.x, enemy.y, hit_radius):
            return True
    return False
