from __future__ import annotations

from dataclasses import dataclass

from config import cfg
from entities import Enemy, Pickup, Player, distance, normalize
from stages import enemy_behavior, get_enemy_def


@dataclass
class MobIntent:
    ax: float = 0.0
    ay: float = 0.0
    speed: float = 0.0
    state: str = "patrol"


def _patrol_speed() -> float:
    return float(cfg("enemy_speed_patrol"))


def _chase_speed() -> float:
    return float(cfg("enemy_speed_chase"))


def _with_strafe(ax: float, ay: float, strafe: float) -> tuple[float, float]:
    if strafe <= 0.0:
        return ax, ay
    # Perpendicular component keeps hunters from walking a straight line.
    px, py = -ay, ax
    return ax + px * strafe, ay + py * strafe


def _intent_towards(
    enemy: Enemy,
    target_x: float,
    target_y: float,
    speed: float,
    state: str,
    strafe: float = 0.0,
) -> MobIntent:
    dx, dy = normalize(target_x - enemy.x, target_y - enemy.y)
    dx, dy = _with_strafe(dx, dy, strafe)
    dx, dy = normalize(dx, dy)
    return MobIntent(ax=dx, ay=dy, speed=speed, state=state)


def _flee_from_threats(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    flee_radius: float,
    margin: float,
) -> MobIntent | None:
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
    if not threats:
        return None
    threats.sort(key=lambda item: item[2])
    tx, ty, _ = threats[0]
    dx, dy = normalize(enemy.x - tx, enemy.y - ty)
    return MobIntent(ax=dx, ay=dy, speed=_chase_speed(), state="flee")


def _nearest_green(enemy: Enemy, pickups: list[Pickup], hunt_radius: float) -> Pickup | None:
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


def _nearest_smaller_prey(
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


def _patrol_waypoints(enemy: Enemy, speed: float, strafe: float = 0.0) -> MobIntent:
    if not enemy.waypoints:
        return MobIntent(state="patrol", speed=speed)
    target_x, target_y = enemy.waypoints[enemy.waypoint_index]
    if distance(enemy.x, enemy.y, target_x, target_y) < 28.0:
        enemy.waypoint_index = (enemy.waypoint_index + 1) % len(enemy.waypoints)
        target_x, target_y = enemy.waypoints[enemy.waypoint_index]
    return _intent_towards(enemy, target_x, target_y, speed, "patrol", strafe=strafe * 0.4)


def _compute_grazer_intent(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    pickups: list[Pickup],
    flee_radius: float,
    margin: float,
    hunt_radius: float,
    enemy_def: dict,
) -> MobIntent:
    flee = _flee_from_threats(enemy, player, enemies, flee_radius, margin)
    if flee is not None:
        return flee

    strafe = float(enemy_def.get("strafe", 0.0))
    green = _nearest_green(enemy, pickups, hunt_radius)
    if green is not None:
        speed = _patrol_speed() * float(enemy_def.get("green_mult", 1.25))
        return _intent_towards(enemy, green.x, green.y, speed, "patrol", strafe=strafe * 0.3)

    return _patrol_waypoints(
        enemy,
        _patrol_speed() * float(enemy_def.get("patrol_mult", 0.95)),
        strafe=strafe,
    )


def _compute_hunter_intent(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    flee_radius: float,
    margin: float,
    enemy_def: dict,
) -> MobIntent:
    flee = _flee_from_threats(enemy, player, enemies, flee_radius, margin)
    if flee is not None:
        return flee

    aggro = float(cfg("hunter_aggro_radius"))
    chase_mult = float(enemy_def.get("chase_mult", 1.35))
    strafe = float(enemy_def.get("strafe", 0.0))
    if player.radius < enemy.radius:
        dist = distance(enemy.x, enemy.y, player.x, player.y)
        if dist < aggro:
            return _intent_towards(
                enemy,
                player.x,
                player.y,
                _chase_speed() * chase_mult,
                "chase",
                strafe=strafe,
            )

    prey = _nearest_smaller_prey(enemy, player, enemies, aggro)
    if prey is not None:
        return _intent_towards(
            enemy,
            prey[0],
            prey[1],
            _chase_speed() * chase_mult,
            "chase",
            strafe=strafe * 0.6,
        )

    return _patrol_waypoints(
        enemy,
        _patrol_speed() * float(enemy_def.get("patrol_mult", 0.85)),
        strafe=strafe,
    )


def _compute_lurker_intent(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    flee_radius: float,
    margin: float,
    enemy_def: dict,
) -> MobIntent:
    flee = _flee_from_threats(enemy, player, enemies, flee_radius, margin)
    if flee is not None:
        enemy.burst_left = 0.0
        return flee

    ambush_radius = float(cfg("lurker_ambush_radius"))
    chase_radius = float(cfg("lurker_chase_radius"))
    burst_speed = _chase_speed() * float(enemy_def.get("chase_mult", 1.95))
    patrol_speed = _patrol_speed() * float(enemy_def.get("patrol_mult", 0.9))
    strafe = float(enemy_def.get("strafe", 0.0))

    if player.radius < enemy.radius:
        dist = distance(enemy.x, enemy.y, player.x, player.y)
        if dist < ambush_radius:
            enemy.burst_left = float(cfg("lurker_burst_duration"))
        if enemy.burst_left > 0.0 and dist < chase_radius:
            return _intent_towards(enemy, player.x, player.y, burst_speed, "chase", strafe=strafe * 0.2)

    if enemy.burst_left > 0.0:
        return _patrol_waypoints(enemy, patrol_speed, strafe=strafe)

    return _patrol_waypoints(enemy, patrol_speed, strafe=strafe)


def compute_mob_intent(
    enemy: Enemy,
    player: Player,
    enemies: list[Enemy],
    pickups: list[Pickup],
) -> MobIntent:
    if enemy.is_boss:
        from ai.boss_brain import compute_boss_intent

        intent = compute_boss_intent(enemy, player)
        return MobIntent(ax=intent.ax, ay=intent.ay, speed=intent.speed, state=intent.state)

    if enemy.state == "cooldown" and enemy.cooldown_left > 0:
        return MobIntent(state="cooldown")

    flee_radius = float(cfg("ai_flee_radius"))
    margin = float(cfg("ai_flee_size_margin"))
    hunt_radius = float(cfg("ai_hunt_radius"))
    enemy_def = get_enemy_def(enemy.kind)
    behavior = enemy_behavior(enemy.kind)

    if behavior == "hunter":
        return _compute_hunter_intent(enemy, player, enemies, flee_radius, margin, enemy_def)
    if behavior == "lurker":
        return _compute_lurker_intent(enemy, player, enemies, flee_radius, margin, enemy_def)
    return _compute_grazer_intent(
        enemy,
        player,
        enemies,
        pickups,
        flee_radius,
        margin,
        hunt_radius,
        enemy_def,
    )
