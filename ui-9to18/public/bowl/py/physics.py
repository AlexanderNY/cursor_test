from __future__ import annotations

import math

from config import cfg
from entities import Enemy, Pickup, Player, WorldObject, clamp_circle_in_ellipse, clamp_circle_in_rect, distance, normalize


def entity_mass(radius: float, weight: float | None = None) -> float:
    if weight is not None and weight > 0:
        return weight
    return max(radius * radius, 1.0)


def apply_friction(vx: float, vy: float, friction: float, dt: float) -> tuple[float, float]:
    factor = max(0.0, 1.0 - friction * dt)
    return vx * factor, vy * factor


def clamp_speed(vx: float, vy: float, max_speed: float) -> tuple[float, float]:
    speed = math.hypot(vx, vy)
    if speed <= max_speed or speed <= 1e-6:
        return vx, vy
    scale = max_speed / speed
    return vx * scale, vy * scale


def apply_acceleration(
    vx: float,
    vy: float,
    ax: float,
    ay: float,
    accel: float,
    mass: float,
    dt: float,
) -> tuple[float, float]:
    nx, ny = normalize(ax, ay)
    if nx == 0.0 and ny == 0.0:
        return vx, vy
    impulse = accel / max(mass, 1.0)
    return vx + nx * impulse * dt, vy + ny * impulse * dt


def integrate_body(
    x: float,
    y: float,
    vx: float,
    vy: float,
    radius: float,
    dt: float,
    friction: float,
    max_speed: float,
    world_width: float,
    world_height: float,
    bowl_cx: float,
    bowl_cy: float,
    bowl_rx: float,
    bowl_ry: float,
    use_ellipse: bool,
) -> tuple[float, float, float, float]:
    vx, vy = apply_friction(vx, vy, friction, dt)
    vx, vy = clamp_speed(vx, vy, max_speed)
    x += vx * dt
    y += vy * dt
    if use_ellipse:
        x, y, vx, vy = constrain_circle_in_ellipse(
            x, y, vx, vy, radius, bowl_cx, bowl_cy, bowl_rx, bowl_ry
        )
    else:
        x, y = clamp_circle_in_rect(x, y, radius, world_width, world_height)
    return x, y, vx, vy


def get_bowl_outer_radii(bowl_rx: float, bowl_ry: float) -> tuple[float, float]:
    margin = float(cfg("bowl_rim_margin"))
    return bowl_rx + margin, bowl_ry + margin


def constrain_circle_in_ellipse(
    x: float,
    y: float,
    vx: float,
    vy: float,
    radius: float,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
) -> tuple[float, float, float, float]:
    dx = x - center_x
    dy = y - center_y
    if radius_x <= radius or radius_y <= radius:
        return center_x, center_y, 0.0, 0.0
    eff_rx = radius_x - radius
    eff_ry = radius_y - radius
    norm = (dx * dx) / (eff_rx * eff_rx) + (dy * dy) / (eff_ry * eff_ry)
    if norm <= 1.0:
        return x, y, vx, vy
    scale = 1.0 / math.sqrt(norm)
    x = center_x + dx * scale
    y = center_y + dy * scale
    nx, ny = normalize(dx / (radius_x * radius_x), dy / (radius_y * radius_y))
    outward = vx * nx + vy * ny
    if outward > 0.0:
        vx -= outward * nx
        vy -= outward * ny
    return x, y, vx, vy


def push_obstacle(
    pusher_mass: float,
    pusher_vx: float,
    pusher_vy: float,
    px: float,
    py: float,
    pr: float,
    obj: WorldObject,
    push_strength: float,
) -> None:
    if not obj.pushable:
        return
    dx = obj.x - px
    dy = obj.y - py
    dist = math.hypot(dx, dy)
    min_dist = pr + obj.radius
    if dist >= min_dist or dist <= 1e-6:
        return
    nx, ny = dx / dist, dy / dist
    overlap = min_dist - dist
    obj_mass = max(obj.mass, 1.0)
    total_mass = pusher_mass + obj_mass
    push_ratio = pusher_mass / total_mass
    relative = max(math.hypot(pusher_vx, pusher_vy), push_strength * 0.25)
    impulse = (relative + overlap * 2.0) * push_ratio * push_strength / obj_mass
    obj.vx += nx * impulse
    obj.vy += ny * impulse
    obj.x += nx * overlap * push_ratio
    obj.y += ny * overlap * push_ratio


def resolve_mover_obstacle(
    entity_x: float,
    entity_y: float,
    entity_r: float,
    entity_vx: float,
    entity_vy: float,
    entity_mass: float,
    obj: WorldObject,
) -> tuple[float, float, float, float]:
    dx = entity_x - obj.x
    dy = entity_y - obj.y
    dist = math.hypot(dx, dy)
    min_dist = entity_r + obj.radius
    if dist >= min_dist:
        return entity_x, entity_y, entity_vx, entity_vy
    if dist <= 1e-6:
        return obj.x + min_dist, obj.y, entity_vx, entity_vy
    nx, ny = dx / dist, dy / dist
    overlap = min_dist - dist
    entity_x += nx * overlap
    entity_y += ny * overlap
    push_obstacle(entity_mass, entity_vx, entity_vy, entity_x, entity_y, entity_r, obj, float(cfg("push_strength")))
    if obj.pushable:
        reaction = overlap * entity_mass / (entity_mass + max(obj.mass, 1.0))
        entity_vx -= nx * reaction * 0.15
        entity_vy -= ny * reaction * 0.15
    return entity_x, entity_y, entity_vx, entity_vy


def resolve_circle_bounce(
    ax: float,
    ay: float,
    avx: float,
    avy: float,
    amass: float,
    ar: float,
    bx: float,
    by: float,
    bvx: float,
    bvy: float,
    bmass: float,
    br: float,
) -> tuple[float, float, float, float, float, float, float, float]:
    dx = ax - bx
    dy = ay - by
    dist = math.hypot(dx, dy)
    min_dist = ar + br
    if dist >= min_dist or dist <= 1e-6:
        return ax, ay, avx, avy, bx, by, bvx, bvy
    nx, ny = dx / dist, dy / dist
    overlap = min_dist - dist
    total = amass + bmass
    ax += nx * overlap * (bmass / total)
    ay += ny * overlap * (bmass / total)
    bx -= nx * overlap * (amass / total)
    by -= ny * overlap * (amass / total)
    rel_v = (avx - bvx) * nx + (avy - bvy) * ny
    if rel_v < 0:
        impulse = rel_v * 0.5
        avx -= impulse * nx * (bmass / total)
        avy -= impulse * ny * (bmass / total)
        bvx += impulse * nx * (amass / total)
        bvy += impulse * ny * (amass / total)
    return ax, ay, avx, avy, bx, by, bvx, bvy
