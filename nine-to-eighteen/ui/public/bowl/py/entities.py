from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Literal

PickupKind = Literal["green", "red"]
EnemyState = Literal["patrol", "chase", "cooldown", "flee"]
EnemyKind = Literal["grazer", "hunter", "lurker"]
BossKind = Literal["titan", "stalker", "swarm", "leech", "vortex"]
PerkKind = Literal["leg", "eye", "tentacle", "spike", "shell", "dash", "anchor", "none"]
ObjectKind = Literal["paper", "toothbrush"]


@dataclass
class Player:
    x: float
    y: float
    red: float = 10.0
    green: float = 10.0
    radius: float = 18.0
    vx: float = 0.0
    vy: float = 0.0
    perk_levels: dict[str, int] = field(default_factory=dict)
    facing_angle: float = 0.0
    action_cooldown: float = 0.0
    eat_count: int = 0
    enemies_eaten: int = 0
    color: str = "#60a5fa"
    stamina: float = 100.0
    is_sprinting: bool = False
    ram_cooldown: float = 0.0
    grab_kind: str = "none"
    grab_pickup_index: int = -1
    grab_obstacle_id: int = -1
    grab_time_left: float = 0.0

    @property
    def weight(self) -> float:
        return self.red + self.green

    def perk_level(self, perk: str) -> int:
        return int(self.perk_levels.get(perk, 0))

    def has_perk(self, perk: str) -> bool:
        return self.perk_level(perk) > 0


@dataclass
class Nutrient:
    x: float
    y: float
    radius_x: float
    radius_y: float
    angle: float = 0.0


@dataclass
class Pickup:
    x: float
    y: float
    kind: PickupKind
    radius: float = 10.0
    vx: float = 0.0
    vy: float = 0.0
    wander_timer: float = 0.0
    spike_angle: float = 0.0
    attached_to: int | None = None


@dataclass
class Enemy:
    x: float
    y: float
    radius: float = 16.0
    health: float = 16.0
    vx: float = 0.0
    vy: float = 0.0
    state: EnemyState = "patrol"
    cooldown_left: float = 0.0
    waypoint_index: int = 0
    waypoints: list[tuple[float, float]] = field(default_factory=list)
    is_boss: bool = False
    kind: EnemyKind = "grazer"
    boss_kind: BossKind = "titan"
    max_health: float = 0.0
    boss_timer: float = 0.0
    boss_spawn_count: int = 0
    boss_spawn_cooldown: float = 0.0
    burst_left: float = 0.0
    move_speed: float = 0.0

    @property
    def display_max_health(self) -> float:
        return self.max_health if self.max_health > 0.0 else self.radius

    @property
    def weight(self) -> float:
        return self.radius * self.radius


@dataclass
class WorldObject:
    id: int
    x: float
    y: float
    kind: ObjectKind
    radius: float
    angle: float
    width: float
    height: float
    vx: float = 0.0
    vy: float = 0.0
    mass: float = 50.0
    pushable: bool = True


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def normalize(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy)
    if length <= 1e-6:
        return 0.0, 0.0
    return dx / length, dy / length


def move_towards(
    x: float,
    y: float,
    target_x: float,
    target_y: float,
    speed: float,
    dt: float,
) -> tuple[float, float]:
    dx = target_x - x
    dy = target_y - y
    nx, ny = normalize(dx, dy)
    return x + nx * speed * dt, y + ny * speed * dt


def clamp_circle_in_rect(
    x: float,
    y: float,
    radius: float,
    width: float,
    height: float,
) -> tuple[float, float]:
    return (
        clamp(x, radius, width - radius),
        clamp(y, radius, height - radius),
    )


def clamp_circle_in_ellipse(
    x: float,
    y: float,
    radius: float,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
) -> tuple[float, float]:
    dx = x - center_x
    dy = y - center_y
    if radius_x <= radius or radius_y <= radius:
        return center_x, center_y
    norm = (dx * dx) / ((radius_x - radius) ** 2) + (dy * dy) / ((radius_y - radius) ** 2)
    if norm <= 1.0:
        return x, y
    scale = 1.0 / math.sqrt(norm)
    return center_x + dx * scale, center_y + dy * scale


def resolve_circle_collision(
    x: float,
    y: float,
    radius: float,
    ox: float,
    oy: float,
    oradius: float,
) -> tuple[float, float]:
    dx = x - ox
    dy = y - oy
    dist = math.hypot(dx, dy)
    min_dist = radius + oradius
    if dist >= min_dist:
        return x, y
    if dist <= 1e-6:
        return ox + min_dist, oy
    nx = dx / dist
    ny = dy / dist
    return ox + nx * min_dist, oy + ny * min_dist


def random_point_in_ellipse(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    margin: float,
    rng: random.Random,
) -> tuple[float, float]:
    angle = rng.uniform(0.0, math.tau)
    dist = math.sqrt(rng.random())
    x = center_x + math.cos(angle) * max(radius_x - margin, margin) * dist
    y = center_y + math.sin(angle) * max(radius_y - margin, margin) * dist
    return x, y


def random_point_on_ellipse_edge(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    rng: random.Random,
) -> tuple[float, float]:
    angle = rng.uniform(0.0, math.tau)
    return (
        center_x + math.cos(angle) * radius_x,
        center_y + math.sin(angle) * radius_y,
    )


def random_point_on_rect_edge(
    width: float,
    height: float,
    margin: float,
    rng: random.Random,
) -> tuple[float, float]:
    edge = rng.randint(0, 3)
    if edge == 0:
        return rng.uniform(margin, width - margin), margin
    if edge == 1:
        return rng.uniform(margin, width - margin), height - margin
    if edge == 2:
        return margin, rng.uniform(margin, height - margin)
    return width - margin, rng.uniform(margin, height - margin)


def is_far_enough(
    x: float,
    y: float,
    others: list[tuple[float, float]],
    min_dist: float,
) -> bool:
    for ox, oy in others:
        if distance(x, y, ox, oy) < min_dist:
            return False
    return True


def angle_diff(a: float, b: float) -> float:
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi
