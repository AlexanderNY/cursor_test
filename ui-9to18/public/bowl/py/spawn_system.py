from __future__ import annotations

import math
import random

from combat import init_enemy_health
from config import cfg
from entities import (
    Enemy,
    EnemyKind,
    Pickup,
    distance,
    is_far_enough,
    random_point_in_ellipse,
    random_point_on_ellipse_edge,
)


def pick_enemy_kind(rng: random.Random) -> EnemyKind:
    kinds = cfg("enemy_kinds")
    weights = cfg("enemy_kind_weights")
    if not kinds:
        return "grazer"
    if isinstance(weights, (list, tuple)) and len(weights) == len(kinds):
        return rng.choices(list(kinds), weights=list(weights), k=1)[0]
    return rng.choice(list(kinds))


def create_enemy(
    x: float,
    y: float,
    bowl_cx: float,
    bowl_cy: float,
    bowl_rx: float,
    bowl_ry: float,
    rng: random.Random,
    kind: str | None = None,
) -> Enemy:
    radius = rng.uniform(float(cfg("enemy_radius_min")), float(cfg("enemy_radius_max")))
    waypoints = [
        random_point_in_ellipse(bowl_cx, bowl_cy, bowl_rx, bowl_ry, 30.0, rng)
        for _ in range(int(cfg("waypoints_per_enemy")))
    ]
    return Enemy(
        x=x,
        y=y,
        radius=radius,
        health=init_enemy_health(radius),
        waypoints=waypoints,
        kind=kind or pick_enemy_kind(rng),
    )


def _find_rim_spawn(
    bowl_cx: float,
    bowl_cy: float,
    outer_rx: float,
    outer_ry: float,
    spawn_radius: float,
    player_x: float,
    player_y: float,
    occupied: list[tuple[float, float]],
    rng: random.Random,
    max_attempts: int = 12,
) -> tuple[float, float] | None:
    inset = float(cfg("edge_spawn_rim_inset"))
    min_player = float(cfg("edge_spawn_min_player_distance"))
    min_other = float(cfg("min_spawn_distance"))
    eff_rx = max(outer_rx - spawn_radius - inset, spawn_radius + 8.0)
    eff_ry = max(outer_ry - spawn_radius - inset, spawn_radius + 8.0)

    for _ in range(max_attempts):
        x, y = random_point_on_ellipse_edge(bowl_cx, bowl_cy, eff_rx, eff_ry, rng)
        if distance(x, y, player_x, player_y) < min_player:
            continue
        if not is_far_enough(x, y, occupied, min_other):
            continue
        return x, y
    return None


def try_spawn_green_batch(
    pickups: list[Pickup],
    bowl_cx: float,
    bowl_cy: float,
    outer_rx: float,
    outer_ry: float,
    player_x: float,
    player_y: float,
    occupied: list[tuple[float, float]],
    rng: random.Random,
) -> int:
    max_count = int(cfg("max_green_pickups"))
    batch = int(cfg("edge_spawn_green_batch"))
    green_count = sum(1 for p in pickups if p.kind == "green")
    if green_count >= max_count:
        return 0
    spawned = 0
    occ = list(occupied) + [(p.x, p.y) for p in pickups]
    for _ in range(batch):
        if green_count + spawned >= max_count:
            break
        radius = rng.uniform(float(cfg("pickup_radius_min")), float(cfg("pickup_radius_max")))
        point = _find_rim_spawn(
            bowl_cx,
            bowl_cy,
            outer_rx,
            outer_ry,
            radius,
            player_x,
            player_y,
            occ,
            rng,
        )
        if point is None:
            continue
        x, y = point
        pickups.append(Pickup(x=x, y=y, kind="green", radius=radius))
        occ.append((x, y))
        spawned += 1
    return spawned


def try_spawn_red_batch(
    pickups: list[Pickup],
    bowl_cx: float,
    bowl_cy: float,
    outer_rx: float,
    outer_ry: float,
    player_x: float,
    player_y: float,
    occupied: list[tuple[float, float]],
    rng: random.Random,
) -> int:
    max_count = int(cfg("max_red_pickups"))
    batch = int(cfg("edge_spawn_red_batch"))
    red_count = sum(1 for p in pickups if p.kind == "red")
    if red_count >= max_count:
        return 0
    spawned = 0
    occ = list(occupied) + [(p.x, p.y) for p in pickups]
    for _ in range(batch):
        if red_count + spawned >= max_count:
            break
        radius = rng.uniform(float(cfg("pickup_radius_min")), float(cfg("pickup_radius_max")))
        point = _find_rim_spawn(
            bowl_cx,
            bowl_cy,
            outer_rx,
            outer_ry,
            radius,
            player_x,
            player_y,
            occ,
            rng,
        )
        if point is None:
            continue
        x, y = point
        spike_angle = rng.uniform(0.0, math.tau)
        pickups.append(Pickup(x=x, y=y, kind="red", radius=radius, spike_angle=spike_angle))
        occ.append((x, y))
        spawned += 1
    return spawned


def try_spawn_enemy_batch(
    enemies: list[Enemy],
    bowl_cx: float,
    bowl_cy: float,
    outer_rx: float,
    outer_ry: float,
    player_x: float,
    player_y: float,
    occupied: list[tuple[float, float]],
    bowl_rx: float,
    bowl_ry: float,
    rng: random.Random,
) -> int:
    max_count = int(cfg("max_enemies"))
    batch = int(cfg("edge_spawn_enemy_batch"))
    non_boss_count = sum(1 for e in enemies if not e.is_boss)
    if non_boss_count >= max_count:
        return 0
    spawned = 0
    occ = list(occupied) + [(e.x, e.y) for e in enemies]
    for _ in range(batch):
        if non_boss_count + spawned >= max_count:
            break
        radius = rng.uniform(float(cfg("enemy_radius_min")), float(cfg("enemy_radius_max")))
        point = _find_rim_spawn(
            bowl_cx,
            bowl_cy,
            outer_rx,
            outer_ry,
            radius,
            player_x,
            player_y,
            occ,
            rng,
        )
        if point is None:
            continue
        x, y = point
        enemies.append(create_enemy(x, y, bowl_cx, bowl_cy, bowl_rx, bowl_ry, rng))
        occ.append((x, y))
        spawned += 1
    return spawned
