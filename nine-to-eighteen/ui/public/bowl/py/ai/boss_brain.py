from __future__ import annotations

from dataclasses import dataclass

from bosses import boss_speed_mult
from config import cfg
from entities import Enemy, Player, distance, normalize


@dataclass
class BossIntent:
    ax: float = 0.0
    ay: float = 0.0
    speed: float = 0.0
    state: str = "chase"


def _boss_speed(boss_kind: str, mult: float = 1.0) -> float:
    return float(cfg("boss_speed")) * boss_speed_mult(boss_kind) * mult


def _intent_towards(
    enemy: Enemy,
    target_x: float,
    target_y: float,
    speed: float,
    state: str,
) -> BossIntent:
    dx, dy = normalize(target_x - enemy.x, target_y - enemy.y)
    return BossIntent(ax=dx, ay=dy, speed=speed, state=state)


def _compute_titan_intent(enemy: Enemy, player: Player) -> BossIntent:
    return _intent_towards(enemy, player.x, player.y, _boss_speed("titan"), "chase")


def _compute_stalker_intent(enemy: Enemy, player: Player) -> BossIntent:
    orbit_radius = float(cfg("boss_stalker_orbit_radius"))
    dash_radius = float(cfg("boss_stalker_dash_radius"))
    dist = distance(enemy.x, enemy.y, player.x, player.y)

    if enemy.burst_left > 0:
        return _intent_towards(
            enemy,
            player.x,
            player.y,
            _boss_speed("stalker", float(cfg("boss_stalker_dash_speed_mult"))),
            "chase",
        )

    if dist < dash_radius:
        enemy.burst_left = float(cfg("boss_stalker_dash_duration"))
        return _intent_towards(
            enemy,
            player.x,
            player.y,
            _boss_speed("stalker", float(cfg("boss_stalker_dash_speed_mult"))),
            "chase",
        )

    to_px, to_py = normalize(player.x - enemy.x, player.y - enemy.y)
    tangent_x, tangent_y = -to_py, to_px
    radial_x, radial_y = 0.0, 0.0
    if dist > orbit_radius + 40.0:
        radial_x, radial_y = to_px * 0.55, to_py * 0.55
    elif dist < orbit_radius - 35.0:
        radial_x, radial_y = -to_px * 0.45, -to_py * 0.45

    ax, ay = normalize(tangent_x + radial_x, tangent_y + radial_y)
    return BossIntent(
        ax=ax,
        ay=ay,
        speed=_boss_speed("stalker", 0.9),
        state="patrol" if dist > dash_radius else "chase",
    )


def _compute_swarm_intent(enemy: Enemy, player: Player) -> BossIntent:
    speed = _boss_speed("swarm")
    dist = distance(enemy.x, enemy.y, player.x, player.y)
    keep_distance = float(cfg("boss_swarm_keep_distance"))
    if dist < keep_distance:
        dx, dy = normalize(enemy.x - player.x, enemy.y - player.y)
        return BossIntent(ax=dx, ay=dy, speed=speed * 0.85, state="flee")
    return _intent_towards(enemy, player.x, player.y, speed, "chase")


def _compute_leech_intent(enemy: Enemy, player: Player) -> BossIntent:
    return _intent_towards(enemy, player.x, player.y, _boss_speed("leech"), "chase")


def _compute_vortex_intent(enemy: Enemy, player: Player) -> BossIntent:
    cycle = float(cfg("boss_vortex_cycle_sec"))
    phase = enemy.boss_timer % cycle if cycle > 0 else 0.0
    lunge_share = float(cfg("boss_vortex_lunge_share"))

    if phase >= cycle * (1.0 - lunge_share):
        return _intent_towards(
            enemy,
            player.x,
            player.y,
            _boss_speed("vortex", float(cfg("boss_vortex_lunge_speed_mult"))),
            "chase",
        )

    orbit_radius = float(cfg("boss_vortex_orbit_radius"))
    dist = distance(enemy.x, enemy.y, player.x, player.y)
    to_px, to_py = normalize(player.x - enemy.x, player.y - enemy.y)
    spin_dir = 1.0 if int(enemy.boss_timer / max(cycle, 0.001)) % 2 == 0 else -1.0
    tangent_x, tangent_y = -to_py * spin_dir, to_px * spin_dir
    radial_x, radial_y = 0.0, 0.0
    if dist > orbit_radius + 25.0:
        radial_x, radial_y = to_px * 0.5, to_py * 0.5
    elif dist < orbit_radius - 25.0:
        radial_x, radial_y = -to_px * 0.35, -to_py * 0.35
    ax, ay = normalize(tangent_x + radial_x, tangent_y + radial_y)
    return BossIntent(
        ax=ax,
        ay=ay,
        speed=_boss_speed("vortex", 0.95),
        state="patrol",
    )


def compute_boss_intent(enemy: Enemy, player: Player) -> BossIntent:
    boss_kind = enemy.boss_kind or "titan"
    if boss_kind == "stalker":
        return _compute_stalker_intent(enemy, player)
    if boss_kind == "swarm":
        return _compute_swarm_intent(enemy, player)
    if boss_kind == "leech":
        return _compute_leech_intent(enemy, player)
    if boss_kind == "vortex":
        return _compute_vortex_intent(enemy, player)
    return _compute_titan_intent(enemy, player)


def apply_vortex_pull(boss: Enemy, player: Player, dt: float) -> None:
    if boss.boss_kind != "vortex":
        return
    pull_radius = float(cfg("boss_vortex_pull_radius"))
    dist = distance(boss.x, boss.y, player.x, player.y)
    if dist >= pull_radius or dist <= 1e-6:
        return
    proximity = 1.0 - dist / pull_radius
    pull = float(cfg("boss_vortex_pull_strength")) * proximity * dt
    try:
        from perks import perk_pull_resist

        pull *= 1.0 - perk_pull_resist(player.perk_levels)
    except Exception:
        pass
    dx, dy = normalize(boss.x - player.x, boss.y - player.y)
    player.vx += dx * pull
    player.vy += dy * pull
