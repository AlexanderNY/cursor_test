from __future__ import annotations

import math
import random

from config import cfg
from entities import Enemy, Nutrient, Pickup, Player, distance, normalize


def nearest_nutrient(
    x: float,
    y: float,
    nutrients: list[Nutrient],
    seek_radius: float,
) -> Nutrient | None:
    best: Nutrient | None = None
    best_dist = seek_radius
    for nutrient in nutrients:
        dist = distance(x, y, nutrient.x, nutrient.y)
        if dist < best_dist:
            best_dist = dist
            best = nutrient
    return best


def nearest_green_pickup(
    x: float,
    y: float,
    pickups: list[Pickup],
    hunt_radius: float,
) -> Pickup | None:
    best: Pickup | None = None
    best_dist = hunt_radius
    for pickup in pickups:
        if pickup.kind != "green" or pickup.attached_to is not None:
            continue
        dist = distance(x, y, pickup.x, pickup.y)
        if dist < best_dist:
            best_dist = dist
            best = pickup
    return best


def _accumulate_flee(
    ax: float,
    ay: float,
    from_x: float,
    from_y: float,
    px: float,
    py: float,
    flee_radius: float,
    weight: float = 1.0,
) -> tuple[float, float]:
    dist = distance(px, py, from_x, from_y)
    if dist >= flee_radius or dist <= 1e-6:
        return ax, ay
    dx, dy = normalize(px - from_x, py - from_y)
    proximity = (1.0 - dist / flee_radius) * weight
    return ax + dx * proximity, ay + dy * proximity


def update_green_pickup(
    pickup: Pickup,
    player: Player,
    enemies: list[Enemy],
    nutrients: list[Nutrient],
    dt: float,
    rng: random.Random,
) -> None:
    if pickup.attached_to is not None:
        return

    flee_ax, flee_ay = 0.0, 0.0
    player_radius = float(cfg("green_flee_radius"))
    enemy_radius = float(cfg("green_enemy_flee_radius"))
    flee_speed = float(cfg("green_flee_speed"))

    flee_ax, flee_ay = _accumulate_flee(
        flee_ax,
        flee_ay,
        player.x,
        player.y,
        pickup.x,
        pickup.y,
        player_radius,
        1.0,
    )
    for enemy in enemies:
        flee_ax, flee_ay = _accumulate_flee(
            flee_ax,
            flee_ay,
            enemy.x,
            enemy.y,
            pickup.x,
            pickup.y,
            enemy_radius,
            1.15 if enemy.is_boss else 1.0,
        )

    if abs(flee_ax) > 1e-6 or abs(flee_ay) > 1e-6:
        dx, dy = normalize(flee_ax, flee_ay)
        pickup.vx += dx * flee_speed * dt
        pickup.vy += dy * flee_speed * dt
    else:
        nutrient = nearest_nutrient(
            pickup.x,
            pickup.y,
            nutrients,
            float(cfg("nutrient_seek_radius")),
        )
        if nutrient is not None:
            dx, dy = normalize(nutrient.x - pickup.x, nutrient.y - pickup.y)
            seek = float(cfg("nutrient_seek_speed")) * dt
            pickup.vx += dx * seek
            pickup.vy += dy * seek
        else:
            pickup.wander_timer -= dt
            if pickup.wander_timer <= 0:
                pickup.wander_timer = float(cfg("pickup_wander_interval"))
                angle = rng.uniform(0.0, math.tau)
                speed = float(cfg("green_pickup_speed"))
                pickup.vx += math.cos(angle) * speed * 0.45
                pickup.vy += math.sin(angle) * speed * 0.45


def update_red_pickup(
    pickup: Pickup,
    pickups: list[Pickup],
    dt: float,
    rng: random.Random,
) -> None:
    if pickup.attached_to is not None:
        return
    vision_radius = max(
        float(cfg("red_green_vision_radius")),
        float(cfg("red_hunt_radius")),
        900.0,
    )
    target = nearest_green_pickup(
        pickup.x,
        pickup.y,
        pickups,
        vision_radius,
    )
    hunt_speed = float(cfg("red_hunt_speed"))
    pickup.wander_timer -= dt
    if target is None:
        if pickup.wander_timer <= 0:
            pickup.wander_timer = float(cfg("pickup_wander_interval")) * rng.uniform(0.25, 0.7)
            angle = rng.uniform(0.0, math.tau)
            kick = hunt_speed * rng.uniform(0.35, 0.7)
            pickup.vx += math.cos(angle) * kick * 0.35
            pickup.vy += math.sin(angle) * kick * 0.35
        return
    dx, dy = normalize(target.x - pickup.x, target.y - pickup.y)
    sway = math.sin(pickup.x * 0.05 + pickup.y * 0.04) * 0.95
    sway += math.sin(pickup.wander_timer * 8.0) * 0.35
    px, py = -dy, dx
    dx, dy = normalize(dx + px * sway, dy + py * sway)
    pickup.vx += dx * hunt_speed * dt
    pickup.vy += dy * hunt_speed * dt
    if pickup.wander_timer <= 0:
        pickup.wander_timer = rng.uniform(0.12, 0.38)
        side = 1.0 if rng.random() < 0.5 else -1.0
        pickup.vx += px * side * hunt_speed * 0.22
        pickup.vy += py * side * hunt_speed * 0.22
    pickup.spike_angle = math.atan2(target.y - pickup.y, target.x - pickup.x)


def update_yellow_pickup(
    pickup: Pickup,
    player: Player,
    dt: float,
    rng: random.Random,
) -> None:
    if pickup.attached_to is not None:
        return
    flee_radius = float(cfg("yellow_flee_radius"))
    dist = distance(pickup.x, pickup.y, player.x, player.y)
    if dist < flee_radius and dist > 1e-6:
        dx, dy = normalize(pickup.x - player.x, pickup.y - player.y)
        sway = math.sin(pickup.x * 0.04 + pickup.wander_timer * 6.0) * 0.7
        px, py = -dy, dx
        dx, dy = normalize(dx + px * sway, dy + py * sway)
        flee = float(cfg("yellow_flee_speed")) * dt
        pickup.vx += dx * flee
        pickup.vy += dy * flee
        pickup.spike_angle = math.atan2(dy, dx)
        return
    pickup.wander_timer -= dt
    if pickup.wander_timer <= 0:
        pickup.wander_timer = float(cfg("pickup_wander_interval")) * rng.uniform(0.35, 0.9)
        angle = rng.uniform(0.0, math.tau)
        kick = float(cfg("yellow_flee_speed")) * 0.35
        pickup.vx += math.cos(angle) * kick * 0.3
        pickup.vy += math.sin(angle) * kick * 0.3


def approach_speed(
    mover_vx: float,
    mover_vy: float,
    mover_x: float,
    mover_y: float,
    target_x: float,
    target_y: float,
) -> float:
    dx, dy = normalize(target_x - mover_x, target_y - mover_y)
    return max(0.0, mover_vx * dx + mover_vy * dy)


def compute_ram_damage(player: Player) -> float:
    speed = math.hypot(player.vx, player.vy)
    min_speed = float(cfg("ram_min_speed"))
    if speed < min_speed:
        return 0.0
    ratio = min(speed / min_speed, 2.4)
    damage = float(cfg("ram_base_damage")) * ratio
    if player.is_sprinting:
        damage *= float(cfg("ram_sprint_mult"))
    return damage


def try_ram_enemy(player: Player, enemy: Enemy) -> float:
    if player.ram_cooldown > 0:
        return 0.0
    if distance(player.x, player.y, enemy.x, enemy.y) >= player.radius + enemy.radius:
        return 0.0
    approach = approach_speed(player.vx, player.vy, player.x, player.y, enemy.x, enemy.y)
    if approach < float(cfg("ram_min_speed")) * 0.55:
        return 0.0
    damage = compute_ram_damage(player)
    if damage <= 0:
        return 0.0
    return damage
