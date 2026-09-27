from __future__ import annotations

import json
import math
import random

from ai.boss_brain import apply_vortex_pull
from ai.mob_brain import compute_mob_intent
from bosses import apply_boss_hit, boss_title, create_boss
from combat import (
    apply_green_pickup,
    apply_ram_damage,
    apply_red_eats_green,
    apply_red_pickup,
    apply_yellow_pickup,
    apply_spike_damage,
    can_eat_entity,
    enemy_hits_spike_segments,
    find_grab_target_in_front,
    split_enemy_to_greens,
    spike_segments,
    try_consume_entity,
)
from config import cfg, load_config_from_json
from entities import (
    Enemy,
    Nutrient,
    Pickup,
    Player,
    WorldObject,
    clamp_circle_in_ellipse,
    distance,
    is_far_enough,
    normalize,
    random_point_in_ellipse,
)
from ecosystem import try_ram_enemy, update_green_pickup, update_red_pickup, update_yellow_pickup
from perks import (
    active_perk_ids,
    can_upgrade,
    perk_dash_stats,
    perk_pull_resist,
    perk_shell_mults,
    perk_spike_contact_stats,
    perk_speed_mult,
    perk_tentacle_stats,
    perk_visibility,
    default_perk_levels,
    sanitize_perk_levels,
    upgrade_perk,
    load_perks_from_json,
)
from physics import (
    apply_acceleration,
    apply_friction,
    constrain_circle_in_ellipse,
    entity_mass,
    get_bowl_outer_radii,
    integrate_body,
    resolve_circle_bounce,
    resolve_mover_obstacle,
)
from save_codec import export_state, import_state
from spawn_system import (
    create_enemy,
    try_spawn_enemy_batch,
    try_spawn_green_batch,
    try_spawn_red_batch,
    try_spawn_yellow_batch,
)
from stages import (
    clamp_stage,
    get_enemy_def,
    get_stage,
    hazard_duration,
    score_value,
    stage_count,
)

GamePhase = str


class GameEngine:
    def __init__(self) -> None:
        self.player = Player(x=0.0, y=0.0)
        self.pickups: list[Pickup] = []
        self.nutrients: list[Nutrient] = []
        self.enemies: list[Enemy] = []
        self.obstacles: list[WorldObject] = []
        self.world_width = 1600.0
        self.world_height = 900.0
        self.game_over = False
        self.level = 1
        self.stage = 1
        self.score = 0
        self.victory = False
        self.pending_perk_select = False
        self.bowl_center_x = 800.0
        self.bowl_center_y = 450.0
        self.bowl_radius_x = 400.0
        self.bowl_radius_y = 400.0
        self.phase: GamePhase = "normal"
        self.match_timer = 0.0
        self.whirlpool_time_left = 0.0
        self.whirlpool_angle = 0.0
        self.boss_fight_timer = 0.0
        self.exit_open = False
        self._had_boss = False
        self._last_perk_milestone = 0
        self._green_spawn_timer = 0.0
        self._red_spawn_timer = 0.0
        self._yellow_spawn_timer = 0.0
        self._enemy_spawn_timer = 0.0
        self._obstacle_id = 1
        self._hazard_kind = "flush"
        self._hazard_zones: list[dict] = []
        self._hazard_rings: list[dict] = []
        self._prev_enemies_eaten = 0
        self._prev_boss_alive = False
        self._rng = random.Random()

    def load_config(self, json_raw: str) -> None:
        load_config_from_json(json_raw)

    def load_perks(self, json_raw: str) -> None:
        load_perks_from_json(json_raw)

    def new_game(
        self,
        viewport_width: float,
        viewport_height: float,
        perk: str = "none",
        color: str = "#60a5fa",
        perk_levels: dict | None = None,
        start_stage: int = 1,
    ) -> None:
        self._rng = random.Random()
        self.world_width = viewport_width * cfg("world_scale")
        self.world_height = viewport_height * cfg("world_scale")
        self.bowl_center_x = self.world_width / 2.0
        self.bowl_center_y = self.world_height / 2.0
        self.bowl_radius_x = min(self.world_width, self.world_height) * 0.42
        self.bowl_radius_y = min(self.world_width, self.world_height) * 0.42
        self.level = 1
        self.stage = clamp_stage(start_stage)
        self.score = 0
        self.victory = False
        self.game_over = False
        self.phase = "normal"
        self.match_timer = 0.0
        self.whirlpool_time_left = 0.0
        self.whirlpool_angle = 0.0
        self.boss_fight_timer = 0.0
        self.exit_open = False
        self._had_boss = False
        self._last_perk_milestone = 0
        self._green_spawn_timer = 0.0
        self._red_spawn_timer = 0.0
        self._yellow_spawn_timer = 0.0
        self._enemy_spawn_timer = 0.0
        self._hazard_kind = str(get_stage(self.stage).get("hazard", "flush"))
        self._hazard_zones = []
        self._hazard_rings = []
        self._prev_enemies_eaten = 0
        self._prev_boss_alive = False
        self.player = Player(
            x=self.bowl_center_x,
            y=self.bowl_center_y,
            radius=float(cfg("base_player_radius")),
            color=self._normalize_color(color),
        )
        self.pickups = []
        self.nutrients = []
        self.enemies = []
        self.obstacles = []
        self._obstacle_id = 1
        self._spawn_obstacles()
        self._spawn_nutrients()
        self._spawn_pickups("green", int(cfg("green_pickup_count")))
        self._spawn_pickups("red", int(cfg("red_pickup_count")))
        self._spawn_pickups("yellow", int(cfg("yellow_pickup_count")))
        self._spawn_enemies(int(cfg("enemy_count")))
        if perk_levels is not None:
            self.player.perk_levels = sanitize_perk_levels(perk_levels)
            self.pending_perk_select = False
        else:
            self.player.perk_levels = default_perk_levels()
            if perk and perk != "none":
                self.player.perk_levels[perk] = 1
            self.pending_perk_select = False

    def add_perk(self, perk: str) -> None:
        if can_upgrade(self.player.perk_levels, perk):
            self.player.perk_levels = upgrade_perk(self.player.perk_levels, perk)
        self.pending_perk_select = False

    def skip_perk_select(self) -> None:
        self.pending_perk_select = False

    def load_state(self, state_json: str) -> bool:
        try:
            data = json.loads(state_json)
            if int(data.get("version", 0)) < 1:
                return False
            self.restore_from_save(data)
            return True
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return False

    def restore_from_save(self, data: dict) -> None:
        (
            self.player,
            self.pickups,
            self.enemies,
            self.obstacles,
            self.world_width,
            self.world_height,
            self.game_over,
            self.level,
            self.bowl_center_x,
            self.bowl_center_y,
            self.bowl_radius_x,
            self.bowl_radius_y,
            self.pending_perk_select,
        ) = import_state(data)
        self.phase = data.get("phase", "normal")
        self.match_timer = float(data.get("match_timer", 0.0))
        self.whirlpool_time_left = float(data.get("whirlpool_time_left", 0.0))
        self.whirlpool_angle = float(data.get("whirlpool_angle", 0.0))
        self.boss_fight_timer = float(data.get("boss_fight_timer", 0.0))
        self.exit_open = bool(data.get("exit_open", False))
        self._had_boss = bool(data.get("had_boss", self.phase in ("boss", "exit")))
        self._last_perk_milestone = int(data.get("last_perk_milestone", 0))
        self._green_spawn_timer = float(data.get("green_spawn_timer", 0.0))
        self._red_spawn_timer = float(data.get("red_spawn_timer", 0.0))
        self._yellow_spawn_timer = float(data.get("yellow_spawn_timer", 0.0))
        self._enemy_spawn_timer = float(data.get("enemy_spawn_timer", 0.0))
        max_id = max((obj.id for obj in self.obstacles), default=0)
        self._obstacle_id = max_id + 1
        self.nutrients = [
            Nutrient(
                x=float(item["x"]),
                y=float(item["y"]),
                radius_x=float(item["radius_x"]),
                radius_y=float(item["radius_y"]),
                angle=float(item.get("angle", 0.0)),
            )
            for item in data.get("nutrients", [])
        ]
        if not self.nutrients:
            self._spawn_nutrients()
        self.stage = clamp_stage(int(data.get("stage", 1)))
        self.score = int(data.get("score", 0))
        self.victory = bool(data.get("victory", False))
        self._hazard_kind = str(data.get("hazard_kind", get_stage(self.stage).get("hazard", "flush")))
        self._hazard_zones = list(data.get("hazard_zones", []))
        self._hazard_rings = list(data.get("hazard_rings", []))
        self._prev_enemies_eaten = int(self.player.enemies_eaten)
        self._prev_boss_alive = any(e.is_boss for e in self.enemies)
        if self.phase == "whirlpool":
            self.phase = "hazard"

    def export_state_json(self) -> str:
        return json.dumps(self.export_save())

    def export_save(self) -> dict:
        state = export_state(
            version=int(cfg("save_version")),
            player=self.player,
            pickups=self.pickups,
            enemies=self.enemies,
            obstacles=self.obstacles,
            world_width=self.world_width,
            world_height=self.world_height,
            game_over=self.game_over,
            level=self.level,
            bowl_center_x=self.bowl_center_x,
            bowl_center_y=self.bowl_center_y,
            bowl_radius_x=self.bowl_radius_x,
            bowl_radius_y=self.bowl_radius_y,
            pending_perk_select=self.pending_perk_select,
        )
        state["phase"] = self.phase
        state["match_timer"] = self.match_timer
        state["whirlpool_time_left"] = self.whirlpool_time_left
        state["whirlpool_angle"] = self.whirlpool_angle
        state["boss_fight_timer"] = self.boss_fight_timer
        state["exit_open"] = self.exit_open
        state["had_boss"] = self._had_boss
        state["last_perk_milestone"] = self._last_perk_milestone
        state["green_spawn_timer"] = self._green_spawn_timer
        state["red_spawn_timer"] = self._red_spawn_timer
        state["yellow_spawn_timer"] = self._yellow_spawn_timer
        state["enemy_spawn_timer"] = self._enemy_spawn_timer
        state["stage"] = self.stage
        state["score"] = self.score
        state["victory"] = self.victory
        state["hazard_kind"] = self._hazard_kind
        state["hazard_zones"] = list(self._hazard_zones)
        state["hazard_rings"] = list(self._hazard_rings)
        state["nutrients"] = [
            {
                "x": n.x,
                "y": n.y,
                "radius_x": n.radius_x,
                "radius_y": n.radius_y,
                "angle": n.angle,
            }
            for n in self.nutrients
        ]
        return state

    def get_render_state(self, viewport_width: float, viewport_height: float) -> dict:
        base_vis = float(cfg("base_visibility_radius"))
        visibility, lightness = perk_visibility(self.player.perk_levels, base_vis)

        camera_x = self.player.x - viewport_width / 2.0
        camera_y = self.player.y - viewport_height / 2.0
        camera_x = max(0.0, min(self.world_width - viewport_width, camera_x))
        camera_y = max(0.0, min(self.world_height - viewport_height, camera_y))

        per_enemy = int(cfg("enemies_per_perk"))
        skill_progress = self._skill_progress()
        eaten_mod = skill_progress % per_enemy if per_enemy else 0
        outer_rx, outer_ry = self._bowl_outer_radii()

        stage_data = get_stage(self.stage)
        return {
            "level": self.level,
            "stage": self.stage,
            "stage_count": stage_count(),
            "stage_id": stage_data.get("id", "toilet"),
            "stage_title": stage_data.get("title", "Унитаз"),
            "score": self.score,
            "victory": self.victory,
            "eat_count": self.player.eat_count,
            "enemies_eaten": self.player.enemies_eaten,
            "skill_progress": skill_progress,
            "enemies_eaten_mod": eaten_mod,
            "enemies_per_perk": per_enemy,
            "pending_perk_select": self.pending_perk_select,
            "world": {"width": self.world_width, "height": self.world_height},
            "bowl": {
                "cx": self.bowl_center_x,
                "cy": self.bowl_center_y,
                "rx": self.bowl_radius_x,
                "ry": self.bowl_radius_y,
                "outer_rx": outer_rx,
                "outer_ry": outer_ry,
                "rim_margin": float(cfg("bowl_rim_margin")),
            },
            "arena": {
                "floor": stage_data.get("floor", "#e8eef5"),
                "water_inner": stage_data.get("water_inner", "#1e4d7a"),
                "water_mid": stage_data.get("water_mid", "rgba(37, 99, 168, 0.75)"),
                "water_outer": stage_data.get("water_outer", "rgba(15, 45, 82, 0.95)"),
                "rim": stage_data.get("rim", "#cbd5e1"),
                "rim_stroke": stage_data.get("rim_stroke", "#94a3b8"),
            },
            "camera": {"x": camera_x, "y": camera_y},
            "visibility_radius": visibility,
            "lightness_mult": lightness,
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "radius": self.player.radius,
                "red": self.player.red,
                "green": self.player.green,
                "weight": self.player.weight,
                "perk_levels": sanitize_perk_levels(self.player.perk_levels),
                "perks": active_perk_ids(self.player.perk_levels),
                "facing_angle": self.player.facing_angle,
                "color": self.player.color,
                "stamina": self.player.stamina,
                "stamina_max": float(cfg("stamina_max")),
                "is_sprinting": self.player.is_sprinting,
                "grab_kind": self.player.grab_kind,
                "grab_time_left": self.player.grab_time_left,
                "move_angle": self._player_move_angle(),
                "speed": math.hypot(self.player.vx, self.player.vy),
            },
            "obstacles": [
                {
                    "x": obj.x,
                    "y": obj.y,
                    "kind": obj.kind,
                    "radius": obj.radius,
                    "angle": obj.angle,
                    "width": obj.width,
                    "height": obj.height,
                }
                for obj in self.obstacles
            ],
            "nutrients": [
                {
                    "x": n.x,
                    "y": n.y,
                    "radius_x": n.radius_x,
                    "radius_y": n.radius_y,
                    "angle": n.angle,
                }
                for n in self.nutrients
            ],
            "pickups": [
                {
                    "x": p.x,
                    "y": p.y,
                    "kind": p.kind,
                    "radius": p.radius,
                    "spike_angle": p.spike_angle,
                    "attached_to": p.attached_to,
                }
                for p in self.pickups
            ],
            "enemies": [
                {
                    "x": e.x,
                    "y": e.y,
                    "radius": e.radius,
                    "health": e.health,
                    "max_health": e.display_max_health,
                    "state": e.state,
                    "is_boss": e.is_boss,
                    "kind": e.kind,
                    "boss_kind": e.boss_kind if e.is_boss else None,
                    "burst_left": e.burst_left,
                    "color": get_enemy_def(e.kind).get("color", "#22c55e"),
                    "title": get_enemy_def(e.kind).get("title", e.kind),
                    "speed": math.hypot(e.vx, e.vy),
                }
                for e in self.enemies
            ],
            "game_over": self.game_over,
            "phase": self.phase,
            "match_timer": self.match_timer,
            "match_timer_total": float(cfg("match_timer_sec")),
            "whirlpool_time_left": self.whirlpool_time_left,
            "whirlpool_duration": float(cfg("whirlpool_duration_sec")),
            "whirlpool_angle": self.whirlpool_angle,
            "whirlpool_radius": float(cfg("whirlpool_radius")),
            "hazard_kind": self._hazard_kind,
            "hazard_title": stage_data.get("hazard_title", "Событие"),
            "hazard_zones": list(self._hazard_zones),
            "hazard_rings": list(self._hazard_rings),
            "boss_active": any(e.is_boss for e in self.enemies),
            "active_boss": self._active_boss_state(),
            "exit_open": self.exit_open,
            "exit": (
                {
                    "x": self.bowl_center_x,
                    "y": self.bowl_center_y,
                    "radius": float(cfg("exit_portal_radius")),
                }
                if self.exit_open
                else None
            ),
            "boss_fight_timer": self.boss_fight_timer,
            "boss_escape_sec": float(cfg("boss_escape_sec")),
        }

    def _active_boss_state(self) -> dict | None:
        stage_data = get_stage(self.stage)
        for enemy in self.enemies:
            if not enemy.is_boss:
                continue
            return {
                "kind": enemy.boss_kind,
                "title": stage_data.get("boss_title") or boss_title(enemy.boss_kind),
                "health": enemy.health,
                "max_health": enemy.display_max_health,
            }
        return None

    def _add_score(self, key: str, amount: int | None = None) -> None:
        gain = int(amount) if amount is not None else score_value(key)
        if gain > 0:
            self.score += gain

    def update(self, dt: float, move_x: float, move_y: float, action: bool, sprint: bool = False) -> None:
        if self.game_over or self.victory or self.pending_perk_select:
            return

        if self.player.action_cooldown > 0:
            self.player.action_cooldown = max(0.0, self.player.action_cooldown - dt)
        if self.player.ram_cooldown > 0:
            self.player.ram_cooldown = max(0.0, self.player.ram_cooldown - dt)

        if self.phase == "normal":
            self.match_timer += dt
            if self.match_timer >= float(cfg("match_timer_sec")):
                self._start_hazard()

        if self.phase == "hazard":
            self._update_hazard(dt)

        if self.phase in ("boss", "exit"):
            self._update_boss_phase(dt)

        self._update_edge_spawns(dt)
        self._apply_player_input(dt, move_x, move_y, sprint)

        if action:
            self._try_player_action()

        self._update_pickups(dt)
        self._update_boss_abilities(dt)
        self._update_enemies(dt)
        self._apply_boss_auras(dt)
        self._apply_enemy_auras(dt)
        self._integrate_all_bodies(dt)
        self._resolve_physics_collisions()
        self._enforce_bowl_bounds()
        self._update_tentacle_grab(dt)
        self._check_ram_collisions()
        self._process_eating()
        self._sync_score_from_kills()
        self._check_boss_cleared()
        self._check_enemy_hits()
        self._check_exit_entry()
        self._check_perk_milestone()
        self._check_game_over()

    def _update_edge_spawns(self, dt: float) -> None:
        if not cfg("edge_spawn_enabled"):
            return

        self._green_spawn_timer += dt
        self._red_spawn_timer += dt
        self._yellow_spawn_timer += dt
        self._enemy_spawn_timer += dt

        occupied = self._occupied_points()
        outer_rx, outer_ry = self._bowl_outer_radii()

        if self._green_spawn_timer >= float(cfg("edge_spawn_green_interval_sec")):
            self._green_spawn_timer = 0.0
            try_spawn_green_batch(
                self.pickups,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
                self.player.x,
                self.player.y,
                occupied,
                self._rng,
            )

        if self._red_spawn_timer >= float(cfg("edge_spawn_red_interval_sec")):
            self._red_spawn_timer = 0.0
            try_spawn_red_batch(
                self.pickups,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
                self.player.x,
                self.player.y,
                occupied,
                self._rng,
            )

        if self._yellow_spawn_timer >= float(cfg("edge_spawn_yellow_interval_sec")):
            self._yellow_spawn_timer = 0.0
            try_spawn_yellow_batch(
                self.pickups,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
                self.player.x,
                self.player.y,
                occupied,
                self._rng,
            )

        if self._enemy_spawn_timer >= float(cfg("edge_spawn_enemy_interval_sec")):
            self._enemy_spawn_timer = 0.0
            try_spawn_enemy_batch(
                self.enemies,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
                self.player.x,
                self.player.y,
                occupied,
                self.bowl_radius_x,
                self.bowl_radius_y,
                self._rng,
                stage=self.stage,
            )

    def _apply_player_input(self, dt: float, move_x: float, move_y: float, sprint: bool) -> None:
        nx, ny = normalize(move_x, move_y)
        if nx != 0.0 or ny != 0.0:
            self.player.facing_angle = math.atan2(ny, nx)
        max_stamina = float(cfg("stamina_max"))
        is_moving = nx != 0.0 or ny != 0.0
        is_sprinting = sprint and is_moving and self.player.stamina > 0.0
        self.player.is_sprinting = is_sprinting
        dash_bonus, stamina_drain_mult, _iframe = perk_dash_stats(self.player.perk_levels)
        if is_sprinting:
            sprint_mult = float(cfg("sprint_speed_mult")) + dash_bonus
            self.player.stamina = max(
                0.0,
                self.player.stamina
                - float(cfg("stamina_drain_per_sec")) * stamina_drain_mult * dt,
            )
        else:
            self.player.stamina = min(
                max_stamina,
                self.player.stamina + float(cfg("stamina_regen_per_sec")) * dt,
            )
        # Крейсерская скорость не зависит от веса: иначе герой вязнет по мере роста.
        cruise = float(cfg("player_speed")) * perk_speed_mult(self.player.perk_levels)
        accel_scale = float(cfg("physics_player_accel")) / 9000.0
        cruise *= max(0.45, accel_scale)
        if is_sprinting:
            cruise *= sprint_mult
        drive_mass = 24.0
        drive_accel = cruise * float(cfg("physics_friction")) * drive_mass
        self.player.vx, self.player.vy = apply_acceleration(
            self.player.vx,
            self.player.vy,
            nx,
            ny,
            drive_accel,
            drive_mass,
            dt,
        )
        if self.phase == "hazard" and self._hazard_kind == "flush":
            pull = float(cfg("whirlpool_pull_speed")) * self._whirlpool_pull_factor(
                self.player.x,
                self.player.y,
            )
            pull *= 1.0 - perk_pull_resist(self.player.perk_levels)
            dx, dy = normalize(
                self.bowl_center_x - self.player.x,
                self.bowl_center_y - self.player.y,
            )
            if dx != 0.0 or dy != 0.0:
                self.player.vx += dx * pull * dt
                self.player.vy += dy * pull * dt
                if nx != 0.0 or ny != 0.0:
                    flee = float(cfg("whirlpool_flee_speed"))
                    away = -(nx * dx + ny * dy)
                    if away > 0.15:
                        self.player.vx += nx * flee * away * dt
                        self.player.vy += ny * flee * away * dt
        elif self.phase == "hazard":
            self._apply_directional_hazard_to_player(dt, nx, ny)

    def _whirlpool_pull_factor(self, x: float, y: float) -> float:
        radius = float(cfg("whirlpool_radius"))
        dist = distance(x, y, self.bowl_center_x, self.bowl_center_y)
        if radius <= 1e-6:
            return 1.0
        if dist >= radius * 2.5:
            return 0.2
        t = min(dist / radius, 1.0)
        return 0.3 + 0.7 * (1.0 - t * t)

    def _bowl_outer_radii(self) -> tuple[float, float]:
        return get_bowl_outer_radii(self.bowl_radius_x, self.bowl_radius_y)

    def _enforce_bowl_bounds(self) -> None:
        outer_rx, outer_ry = self._bowl_outer_radii()
        cx, cy = self.bowl_center_x, self.bowl_center_y

        self.player.x, self.player.y, self.player.vx, self.player.vy = constrain_circle_in_ellipse(
            self.player.x,
            self.player.y,
            self.player.vx,
            self.player.vy,
            self.player.radius,
            cx,
            cy,
            outer_rx,
            outer_ry,
        )
        for enemy in self.enemies:
            enemy.x, enemy.y, enemy.vx, enemy.vy = constrain_circle_in_ellipse(
                enemy.x,
                enemy.y,
                enemy.vx,
                enemy.vy,
                enemy.radius,
                cx,
                cy,
                outer_rx,
                outer_ry,
            )
        for pickup in self.pickups:
            if pickup.attached_to is not None:
                continue
            pickup.x, pickup.y, pickup.vx, pickup.vy = constrain_circle_in_ellipse(
                pickup.x,
                pickup.y,
                pickup.vx,
                pickup.vy,
                pickup.radius,
                cx,
                cy,
                outer_rx,
                outer_ry,
            )
        for obj in self.obstacles:
            obj.x, obj.y, obj.vx, obj.vy = constrain_circle_in_ellipse(
                obj.x,
                obj.y,
                obj.vx,
                obj.vy,
                obj.radius,
                cx,
                cy,
                outer_rx,
                outer_ry,
            )

    def _integrate_all_bodies(self, dt: float) -> None:
        friction = float(cfg("physics_friction"))
        max_speed = float(cfg("physics_max_speed"))
        obs_friction = float(cfg("obstacle_friction"))
        outer_rx, outer_ry = self._bowl_outer_radii()
        whirlpool_flee = float(cfg("whirlpool_flee_speed"))

        player_max_speed = float(cfg("player_speed"))
        if self.phase == "hazard" and self._hazard_kind == "flush":
            player_max_speed *= float(cfg("whirlpool_player_speed_mult"))
        if self.player.is_sprinting:
            player_max_speed *= float(cfg("sprint_speed_mult"))
        self.player.x, self.player.y, self.player.vx, self.player.vy = integrate_body(
            self.player.x,
            self.player.y,
            self.player.vx,
            self.player.vy,
            self.player.radius,
            dt,
            friction,
            player_max_speed,
            self.world_width,
            self.world_height,
            self.bowl_center_x,
            self.bowl_center_y,
            outer_rx,
            outer_ry,
            True,
        )

        for enemy in self.enemies:
            enemy_max_speed = enemy.move_speed if enemy.move_speed > 0 else max_speed
            if self.phase == "hazard" and self._hazard_kind == "flush":
                enemy_max_speed = max(enemy_max_speed, whirlpool_flee)
            enemy.x, enemy.y, enemy.vx, enemy.vy = integrate_body(
                enemy.x,
                enemy.y,
                enemy.vx,
                enemy.vy,
                enemy.radius,
                dt,
                friction,
                enemy_max_speed,
                self.world_width,
                self.world_height,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
                True,
            )

        for pickup in self.pickups:
            if pickup.attached_to is not None:
                continue
            pickup.x, pickup.y, pickup.vx, pickup.vy = integrate_body(
                pickup.x,
                pickup.y,
                pickup.vx,
                pickup.vy,
                pickup.radius,
                dt,
                friction,
                max_speed * 0.5,
                self.world_width,
                self.world_height,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
                True,
            )

        for obj in self.obstacles:
            obj.vx, obj.vy = apply_friction(obj.vx, obj.vy, obs_friction, dt)
            obj.x += obj.vx * dt
            obj.y += obj.vy * dt
            obj.x, obj.y, obj.vx, obj.vy = constrain_circle_in_ellipse(
                obj.x,
                obj.y,
                obj.vx,
                obj.vy,
                obj.radius,
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
            )

    def _resolve_physics_collisions(self) -> None:
        pm = entity_mass(self.player.radius, self.player.weight)
        for obj in self.obstacles:
            self.player.x, self.player.y, self.player.vx, self.player.vy = resolve_mover_obstacle(
                self.player.x,
                self.player.y,
                self.player.radius,
                self.player.vx,
                self.player.vy,
                pm,
                obj,
            )

        for enemy in self.enemies:
            em = entity_mass(enemy.radius)
            for obj in self.obstacles:
                enemy.x, enemy.y, enemy.vx, enemy.vy = resolve_mover_obstacle(
                    enemy.x, enemy.y, enemy.radius, enemy.vx, enemy.vy, em, obj
                )

        for pickup in self.pickups:
            if pickup.attached_to is not None:
                continue
            for obj in self.obstacles:
                pickup.x, pickup.y, pickup.vx, pickup.vy = resolve_mover_obstacle(
                    pickup.x,
                    pickup.y,
                    pickup.radius,
                    pickup.vx,
                    pickup.vy,
                    entity_mass(pickup.radius),
                    obj,
                )

        for i, enemy in enumerate(self.enemies):
            em = entity_mass(enemy.radius)
            self.player.x, self.player.y, self.player.vx, self.player.vy, enemy.x, enemy.y, enemy.vx, enemy.vy = (
                resolve_circle_bounce(
                    self.player.x,
                    self.player.y,
                    self.player.vx,
                    self.player.vy,
                    pm,
                    self.player.radius,
                    enemy.x,
                    enemy.y,
                    enemy.vx,
                    enemy.vy,
                    em,
                    enemy.radius,
                )
            )

        for i in range(len(self.enemies)):
            for j in range(i + 1, len(self.enemies)):
                a, b = self.enemies[i], self.enemies[j]
                am, bm = entity_mass(a.radius), entity_mass(b.radius)
                a.x, a.y, a.vx, a.vy, b.x, b.y, b.vx, b.vy = resolve_circle_bounce(
                    a.x, a.y, a.vx, a.vy, am, a.radius,
                    b.x, b.y, b.vx, b.vy, bm, b.radius,
                )

    def _process_red_hunts_green(self) -> None:
        consumed: set[int] = set()
        for red_idx, red in enumerate(self.pickups):
            if red.kind != "red" or red.attached_to is not None:
                continue
            for green_idx, green in enumerate(self.pickups):
                if green_idx in consumed or green.kind != "green" or green.attached_to is not None:
                    continue
                if distance(red.x, red.y, green.x, green.y) >= red.radius + green.radius:
                    continue
                apply_red_eats_green(red, green)
                consumed.add(green_idx)
                break
        if consumed:
            self.pickups = [p for i, p in enumerate(self.pickups) if i not in consumed]

    def _check_ram_collisions(self) -> None:
        if self.player.ram_cooldown > 0:
            return
        removed: list[int] = []
        new_greens: list[Pickup] = []
        for idx, enemy in enumerate(self.enemies):
            damage = try_ram_enemy(self.player, enemy)
            if damage <= 0:
                continue
            self.player.ram_cooldown = float(cfg("ram_cooldown"))
            dead = apply_ram_damage(enemy, damage)
            dx, dy = normalize(enemy.x - self.player.x, enemy.y - self.player.y)
            if dx != 0.0 or dy != 0.0:
                kb = float(cfg("knockback_distance")) * 0.4
                enemy.vx += dx * kb
                enemy.vy += dy * kb
                self.player.vx -= dx * kb * 0.12
                self.player.vy -= dy * kb * 0.12
            if not dead:
                continue
            new_greens.extend(split_enemy_to_greens(enemy, self._rng))
            removed.append(idx)
            self.player.enemies_eaten += 1
        if removed:
            self.enemies = [e for i, e in enumerate(self.enemies) if i not in removed]
            self.pickups.extend(new_greens)

    def _process_eating(self) -> None:
        self._process_red_hunts_green()
        remaining_pickups: list[Pickup] = []
        for pickup in self.pickups:
            eaten = False
            if pickup.kind == "green":
                if distance(self.player.x, self.player.y, pickup.x, pickup.y) < self.player.radius + pickup.radius:
                    apply_green_pickup(self.player, pickup)
                    self.player.eat_count += 1
                    self._add_score("green")
                    eaten = True
                else:
                    for enemy in self.enemies:
                        if distance(enemy.x, enemy.y, pickup.x, pickup.y) < enemy.radius + pickup.radius:
                            apply_green_pickup(enemy, pickup)
                            eaten = True
                            break
            elif pickup.kind == "yellow":
                if distance(self.player.x, self.player.y, pickup.x, pickup.y) < self.player.radius + pickup.radius:
                    apply_yellow_pickup(self.player, pickup)
                    self.player.eat_count += 1
                    self._add_score("yellow")
                    eaten = True
            elif pickup.kind == "red" and distance(self.player.x, self.player.y, pickup.x, pickup.y) < self.player.radius + pickup.radius:
                apply_red_pickup(self.player, pickup)
                self.player.eat_count += 1
                self._add_score("red")
                eaten = True
            if not eaten:
                remaining_pickups.append(pickup)
        self.pickups = remaining_pickups

        self._process_entity_combat()

    def _sync_score_from_kills(self) -> None:
        eaten_now = int(self.player.enemies_eaten)
        gained = eaten_now - self._prev_enemies_eaten
        if gained > 0:
            self._add_score("enemy", score_value("enemy") * gained)
        self._prev_enemies_eaten = eaten_now
        boss_alive = any(enemy.is_boss for enemy in self.enemies)
        if self._prev_boss_alive and not boss_alive and self._had_boss:
            self._add_score("boss_kill")
        self._prev_boss_alive = boss_alive

    def _process_entity_combat(self) -> None:
        for enemy in self.enemies:
            if can_eat_entity(enemy.radius, self.player.radius):
                if distance(enemy.x, enemy.y, self.player.x, self.player.y) < enemy.radius + self.player.radius:
                    self.game_over = True
                    return

        removed: set[int] = set()
        new_greens: list[Pickup] = []

        for idx, enemy in enumerate(self.enemies):
            if idx in removed:
                continue
            if try_consume_entity(self.player, enemy, True):
                removed.add(idx)
                continue
            for jdx, other in enumerate(self.enemies):
                if jdx == idx or jdx in removed:
                    continue
                if try_consume_entity(enemy, other, False):
                    removed.add(jdx)

        if removed:
            self.enemies = [e for i, e in enumerate(self.enemies) if i not in removed]

        spike_removed: list[int] = []
        for idx, enemy in enumerate(self.enemies):
            if enemy.health <= 0:
                new_greens.extend(split_enemy_to_greens(enemy, self._rng))
                spike_removed.append(idx)
                if not enemy.is_boss:
                    self.player.enemies_eaten += 1
        if spike_removed:
            self.enemies = [e for i, e in enumerate(self.enemies) if i not in spike_removed]
        self.pickups.extend(new_greens)

    def _skill_progress(self) -> int:
        return int(self.player.enemies_eaten) + int(self.player.skill_bonus)

    def _check_perk_milestone(self) -> None:
        step = int(cfg("enemies_per_perk"))
        if step <= 0 or self.pending_perk_select:
            return
        progress = self._skill_progress()
        next_mark = self._last_perk_milestone + step
        if progress < next_mark:
            return
        self._last_perk_milestone = next_mark
        self.level += 1
        self.pending_perk_select = True

    def _start_hazard(self) -> None:
        stage_data = get_stage(self.stage)
        self._hazard_kind = str(stage_data.get("hazard", "flush"))
        self.phase = "hazard"
        self.whirlpool_time_left = hazard_duration()
        self.whirlpool_angle = 0.0
        self._hazard_zones = []
        self._hazard_rings = []
        if self._hazard_kind == "gas":
            self._spawn_gas_clouds()
        elif self._hazard_kind == "chlorine":
            self._spawn_chlorine_rings()

    def _spawn_gas_clouds(self) -> None:
        count = int(cfg("gas_cloud_count"))
        radius = float(cfg("gas_cloud_radius"))
        for _ in range(count):
            x, y = random_point_in_ellipse(
                self.bowl_center_x,
                self.bowl_center_y,
                self.bowl_radius_x * 0.75,
                self.bowl_radius_y * 0.75,
                40.0,
                self._rng,
            )
            angle = self._rng.uniform(0.0, math.tau)
            self._hazard_zones.append(
                {
                    "x": x,
                    "y": y,
                    "radius": radius,
                    "vx": math.cos(angle) * float(cfg("gas_drift_speed")),
                    "vy": math.sin(angle) * float(cfg("gas_drift_speed")),
                }
            )

    def _spawn_chlorine_rings(self) -> None:
        count = int(cfg("chlorine_ring_count"))
        spacing = float(cfg("whirlpool_radius")) * 0.45
        for index in range(count):
            self._hazard_rings.append(
                {
                    "radius": 20.0 + index * spacing,
                    "max_radius": max(self.bowl_radius_x, self.bowl_radius_y) * 0.95,
                }
            )

    def _end_hazard(self) -> None:
        self._add_score("hazard")
        self.phase = "boss"
        self.whirlpool_time_left = 0.0
        self.boss_fight_timer = 0.0
        self.exit_open = False
        self._had_boss = True
        self._hazard_zones = []
        self._hazard_rings = []
        self.enemies = [e for e in self.enemies if not e.is_boss]
        self._spawn_boss()
        self._prev_boss_alive = True

    def _apply_directional_hazard_to_player(self, dt: float, nx: float, ny: float) -> None:
        push_x, push_y = self._hazard_push_vector()
        if push_x == 0.0 and push_y == 0.0:
            return
        resist = 1.0 - perk_pull_resist(self.player.perk_levels)
        self.player.vx += push_x * resist * dt
        self.player.vy += push_y * resist * dt

    def _hazard_push_vector(self) -> tuple[float, float]:
        if self._hazard_kind == "current":
            speed = float(cfg("current_push_speed"))
            return speed, 0.0
        if self._hazard_kind == "waves":
            period = max(float(cfg("waves_period_sec")), 0.1)
            wave = math.sin(self.whirlpool_angle * (math.tau / period))
            return 0.0, float(cfg("waves_push_speed")) * wave
        if self._hazard_kind == "chlorine":
            dx, dy = normalize(
                self.bowl_center_x - self.player.x,
                self.bowl_center_y - self.player.y,
            )
            strength = float(cfg("chlorine_pull_strength"))
            return dx * strength, dy * strength
        return 0.0, 0.0

    def _apply_push_to_body(self, body: object, dt: float) -> None:
        push_x, push_y = self._hazard_push_vector()
        if push_x == 0.0 and push_y == 0.0:
            return
        body.vx += push_x * dt  # type: ignore[attr-defined]
        body.vy += push_y * dt  # type: ignore[attr-defined]

    def _update_hazard(self, dt: float) -> None:
        self.whirlpool_time_left -= dt
        self.whirlpool_angle += float(cfg("whirlpool_spin_speed")) * dt
        if self._hazard_kind == "flush":
            self._update_flush_hazard(dt)
        elif self._hazard_kind == "gas":
            self._update_gas_hazard(dt)
        elif self._hazard_kind in ("current", "waves", "chlorine"):
            self._update_flow_hazard(dt)
        if self.whirlpool_time_left <= 0:
            self._end_hazard()

    def _update_flush_hazard(self, dt: float) -> None:
        self._update_whirlpool(dt, end_on_timeout=False)

    def _update_gas_hazard(self, dt: float) -> None:
        outer_rx, outer_ry = self._bowl_outer_radii()
        damage = float(cfg("gas_damage_per_sec")) * dt
        for zone in self._hazard_zones:
            zone["x"] = float(zone["x"]) + float(zone["vx"]) * dt
            zone["y"] = float(zone["y"]) + float(zone["vy"]) * dt
            zone["x"], zone["y"] = clamp_circle_in_ellipse(
                float(zone["x"]),
                float(zone["y"]),
                float(zone["radius"]),
                self.bowl_center_x,
                self.bowl_center_y,
                outer_rx,
                outer_ry,
            )
            if distance(self.player.x, self.player.y, float(zone["x"]), float(zone["y"])) < self.player.radius + float(zone["radius"]):
                self.player.red = max(0.0, self.player.red - damage)

    def _update_flow_hazard(self, dt: float) -> None:
        for obj in self.obstacles:
            self._apply_push_to_body(obj, dt)
        for pickup in self.pickups:
            if pickup.attached_to is None:
                self._apply_push_to_body(pickup, dt)
        for enemy in self.enemies:
            self._apply_push_to_body(enemy, dt)
        if self._hazard_kind == "chlorine":
            ring_speed = float(cfg("chlorine_ring_speed"))
            ring_width = float(cfg("chlorine_ring_width"))
            damage = float(cfg("chlorine_damage_per_sec")) * dt
            for ring in self._hazard_rings:
                ring["radius"] = float(ring["radius"]) + ring_speed * dt
                if float(ring["radius"]) > float(ring["max_radius"]):
                    ring["radius"] = 24.0
                dist = distance(self.player.x, self.player.y, self.bowl_center_x, self.bowl_center_y)
                if abs(dist - float(ring["radius"])) <= ring_width * 0.5 + self.player.radius * 0.35:
                    self.player.red = max(0.0, self.player.red - damage)

    def _update_boss_phase(self, dt: float) -> None:
        if self.exit_open:
            return
        self.boss_fight_timer += dt
        if self.boss_fight_timer >= float(cfg("boss_escape_sec")):
            self._open_exit(reason="escape")

    def _check_boss_cleared(self) -> None:
        if self.exit_open:
            return
        if self.phase not in ("boss", "exit"):
            return
        if not self._had_boss:
            return
        if any(enemy.is_boss for enemy in self.enemies):
            return
        self._open_exit(reason="kill")

    def _open_exit(self, reason: str = "escape") -> None:
        if self.exit_open:
            return
        self.exit_open = True
        self.phase = "exit"
        if reason == "kill":
            self.enemies = [e for e in self.enemies if not e.is_boss]

    def _check_exit_entry(self) -> None:
        if not self.exit_open:
            return
        exit_r = float(cfg("exit_portal_radius"))
        if distance(self.player.x, self.player.y, self.bowl_center_x, self.bowl_center_y) > exit_r + self.player.radius * 0.35:
            return
        if self.stage >= stage_count():
            self._add_score("stage_exit")
            self._add_score("victory")
            self.victory = True
            self.exit_open = False
            return
        self._add_score("stage_exit")
        self._advance_to_next_level()

    def _advance_to_next_level(self) -> None:
        self.stage = clamp_stage(self.stage + 1)
        self.phase = "normal"
        self.match_timer = 0.0
        self.whirlpool_time_left = 0.0
        self.whirlpool_angle = 0.0
        self.boss_fight_timer = 0.0
        self.exit_open = False
        self._had_boss = False
        self._hazard_zones = []
        self._hazard_rings = []
        self._green_spawn_timer = 0.0
        self._red_spawn_timer = 0.0
        self._yellow_spawn_timer = 0.0
        self._enemy_spawn_timer = 0.0
        self.player.x = self.bowl_center_x
        self.player.y = self.bowl_center_y
        self.player.vx = 0.0
        self.player.vy = 0.0
        self._release_grab()
        self.pickups = []
        self.nutrients = []
        self.enemies = []
        self.obstacles = []
        self._obstacle_id = 1
        self._prev_boss_alive = False
        self._spawn_obstacles()
        self._spawn_nutrients()
        self._spawn_pickups("green", int(cfg("green_pickup_count")))
        self._spawn_pickups("red", int(cfg("red_pickup_count")))
        self._spawn_pickups("yellow", int(cfg("yellow_pickup_count")))
        self._spawn_enemies(int(cfg("enemy_count")))

    def _spawn_boss(self) -> None:
        angle = self._rng.uniform(0.0, math.tau)
        dist = float(cfg("boss_spawn_distance"))
        boss_kind = str(get_stage(self.stage).get("boss", "titan"))
        if boss_kind not in ("titan", "stalker", "swarm", "leech", "vortex"):
            boss_kind = "titan"
        radius = float(cfg(f"boss_{boss_kind}_radius"))
        bx = self.bowl_center_x + math.cos(angle) * dist
        by = self.bowl_center_y + math.sin(angle) * dist
        outer_rx, outer_ry = self._bowl_outer_radii()
        bx, by = clamp_circle_in_ellipse(
            bx,
            by,
            radius,
            self.bowl_center_x,
            self.bowl_center_y,
            outer_rx,
            outer_ry,
        )
        self.enemies.append(create_boss(bx, by, boss_kind))

    def _spawn_swarm_minion(self, boss: Enemy) -> None:
        angle = self._rng.uniform(0.0, math.tau)
        offset = boss.radius * 0.9
        mx = boss.x + math.cos(angle) * offset
        my = boss.y + math.sin(angle) * offset
        radius = float(cfg("boss_swarm_minion_radius"))
        outer_rx, outer_ry = self._bowl_outer_radii()
        mx, my = clamp_circle_in_ellipse(
            mx,
            my,
            radius,
            self.bowl_center_x,
            self.bowl_center_y,
            outer_rx,
            outer_ry,
        )
        minion = Enemy(
            x=mx,
            y=my,
            radius=radius,
            health=radius,
            max_health=radius,
            kind="hunter",
            state="chase",
        )
        self.enemies.append(minion)

    def _update_boss_abilities(self, dt: float) -> None:
        for enemy in self.enemies:
            if not enemy.is_boss:
                continue
            enemy.boss_timer += dt
            if enemy.boss_kind != "swarm":
                continue
            max_minions = int(cfg("boss_swarm_max_minions"))
            if enemy.boss_spawn_count >= max_minions:
                continue
            enemy.boss_spawn_cooldown -= dt
            if enemy.boss_spawn_cooldown > 0.0:
                continue
            self._spawn_swarm_minion(enemy)
            enemy.boss_spawn_count += 1
            enemy.boss_spawn_cooldown = float(cfg("boss_swarm_spawn_interval"))

    def _apply_boss_auras(self, dt: float) -> None:
        for enemy in self.enemies:
            if enemy.is_boss:
                apply_vortex_pull(enemy, self.player, dt)

    def _apply_enemy_auras(self, dt: float) -> None:
        for enemy in self.enemies:
            if enemy.is_boss:
                continue
            aura = float(get_enemy_def(enemy.kind).get("aura", 0.0))
            if aura <= 0.0:
                continue
            dist = distance(self.player.x, self.player.y, enemy.x, enemy.y)
            if dist > aura + self.player.radius:
                continue
            dmg_mult, _kb = perk_shell_mults(self.player.perk_levels)
            damage = float(cfg("hit_damage")) * 0.35 * dmg_mult * dt
            self.player.red = max(0.0, self.player.red - damage)

    def _update_whirlpool(self, dt: float, end_on_timeout: bool = True) -> None:
        if end_on_timeout:
            self.whirlpool_time_left -= dt
            self.whirlpool_angle += float(cfg("whirlpool_spin_speed")) * dt
        base_pull = float(cfg("whirlpool_pull_speed"))
        flee = float(cfg("whirlpool_flee_speed"))
        spin = float(cfg("whirlpool_spin_speed"))
        cx, cy = self.bowl_center_x, self.bowl_center_y

        for obj in self.obstacles:
            factor = self._whirlpool_pull_factor(obj.x, obj.y)
            pull = base_pull * factor * dt
            dx, dy = normalize(cx - obj.x, cy - obj.y)
            if dx != 0.0 or dy != 0.0:
                obj.vx += dx * pull / max(obj.mass, 1.0)
                obj.vy += dy * pull / max(obj.mass, 1.0)
                obj.vx += -dy * spin * 0.35 / max(obj.mass, 1.0)
                obj.vy += dx * spin * 0.35 / max(obj.mass, 1.0)

        for pickup in self.pickups:
            if pickup.attached_to is not None:
                for obj in self.obstacles:
                    if obj.id == pickup.attached_to:
                        pickup.x, pickup.y = obj.x, obj.y
                        break
                continue
            factor = self._whirlpool_pull_factor(pickup.x, pickup.y)
            pull = base_pull * factor * dt
            dx, dy = normalize(cx - pickup.x, cy - pickup.y)
            if dx != 0.0 or dy != 0.0:
                pickup.vx += dx * pull
                pickup.vy += dy * pull
                pickup.vx += -dy * spin * 0.45
                pickup.vy += dx * spin * 0.45
                if pickup.kind == "green":
                    ax, ay = normalize(pickup.x - cx, pickup.y - cy)
                    pickup.vx += ax * flee * 0.55 * dt
                    pickup.vy += ay * flee * 0.55 * dt

        for enemy in self.enemies:
            factor = self._whirlpool_pull_factor(enemy.x, enemy.y)
            pull = base_pull * factor * dt
            dx, dy = normalize(cx - enemy.x, cy - enemy.y)
            if dx != 0.0 or dy != 0.0:
                enemy.vx += dx * pull
                enemy.vy += dy * pull
                enemy.vx += -dy * spin * 0.3
                enemy.vy += dx * spin * 0.3
                ax, ay = normalize(enemy.x - cx, enemy.y - cy)
                enemy.vx += ax * flee * 0.7 * dt
                enemy.vy += ay * flee * 0.7 * dt

        if end_on_timeout and self.whirlpool_time_left <= 0:
            self._end_hazard()

    def _occupied_points(self) -> list[tuple[float, float]]:
        points = [(self.player.x, self.player.y)]
        points.extend((p.x, p.y) for p in self.pickups)
        points.extend((e.x, e.y) for e in self.enemies)
        points.extend((o.x, o.y) for o in self.obstacles)
        points.extend((n.x, n.y) for n in self.nutrients)
        return points

    def _spawn_nutrients(self) -> None:
        self.nutrients = []
        y_ratio = float(cfg("nutrient_radius_y_ratio"))
        rx_min = float(cfg("nutrient_radius_x_min"))
        rx_max = float(cfg("nutrient_radius_x_max"))
        for _ in range(int(cfg("nutrient_count"))):
            for _attempt in range(60):
                x, y = random_point_in_ellipse(
                    self.bowl_center_x,
                    self.bowl_center_y,
                    self.bowl_radius_x,
                    self.bowl_radius_y,
                    50.0,
                    self._rng,
                )
                if is_far_enough(x, y, self._occupied_points(), float(cfg("min_spawn_distance")) * 0.85):
                    break
            else:
                continue
            radius_x = self._rng.uniform(rx_min, rx_max)
            radius_y = radius_x * y_ratio
            self.nutrients.append(
                Nutrient(
                    x=x,
                    y=y,
                    radius_x=radius_x,
                    radius_y=radius_y,
                    angle=self._rng.uniform(0.0, math.tau),
                )
            )

    def _spawn_obstacles(self) -> None:
        stage_data = get_stage(self.stage)
        kinds = stage_data.get("obstacle_kinds") or cfg("obstacle_kinds")
        for _ in range(int(cfg("obstacle_count"))):
            kind = self._rng.choice(list(kinds))
            for _attempt in range(60):
                x, y = random_point_in_ellipse(
                    self.bowl_center_x,
                    self.bowl_center_y,
                    self.bowl_radius_x,
                    self.bowl_radius_y,
                    40.0,
                    self._rng,
                )
                if is_far_enough(x, y, self._occupied_points(), float(cfg("min_spawn_distance"))):
                    break
            else:
                continue
            width, height, radius, mass, pushable = self._obstacle_stats(kind)
            self.obstacles.append(
                WorldObject(
                    id=self._obstacle_id,
                    x=x,
                    y=y,
                    kind=kind,
                    radius=radius,
                    angle=self._rng.uniform(0.0, math.tau),
                    width=width,
                    height=height,
                    mass=mass,
                    pushable=pushable,
                )
            )
            self._obstacle_id += 1

    def _obstacle_stats(self, kind: str) -> tuple[float, float, float, float, bool]:
        if kind == "paper":
            return 720.0, 560.0, 360.0, float(cfg("paper_mass")), False
        if kind == "toothbrush":
            return 240.0, 960.0, 480.0, float(cfg("toothbrush_mass")), True
        if kind == "pipe":
            return 520.0, 180.0, 280.0, float(cfg("pipe_mass")), False
        if kind == "log":
            return 640.0, 160.0, 320.0, float(cfg("log_mass")), True
        if kind == "grate":
            return 420.0, 420.0, 260.0, float(cfg("grate_mass")), False
        if kind == "rock":
            return 300.0, 260.0, 200.0, float(cfg("rock_mass")), False
        return 240.0, 960.0, 480.0, float(cfg("toothbrush_mass")), True

    def _spawn_pickups(self, kind: str, count: int) -> None:
        for _ in range(count):
            for _attempt in range(60):
                x, y = random_point_in_ellipse(
                    self.bowl_center_x,
                    self.bowl_center_y,
                    self.bowl_radius_x,
                    self.bowl_radius_y,
                    20.0,
                    self._rng,
                )
                if is_far_enough(x, y, self._occupied_points(), float(cfg("min_spawn_distance"))):
                    break
            else:
                continue
            radius = self._rng.uniform(float(cfg("pickup_radius_min")), float(cfg("pickup_radius_max")))
            spike_angle = self._rng.uniform(0.0, math.tau) if kind == "red" else 0.0
            self.pickups.append(Pickup(x=x, y=y, kind=kind, radius=radius, spike_angle=spike_angle))

    def _spawn_enemies(self, count: int) -> None:
        for _ in range(count):
            for _attempt in range(60):
                x, y = random_point_in_ellipse(
                    self.bowl_center_x,
                    self.bowl_center_y,
                    self.bowl_radius_x,
                    self.bowl_radius_y,
                    30.0,
                    self._rng,
                )
                if is_far_enough(x, y, self._occupied_points(), float(cfg("min_spawn_distance"))):
                    break
            else:
                continue
            self.enemies.append(
                create_enemy(
                    x,
                    y,
                    self.bowl_center_x,
                    self.bowl_center_y,
                    self.bowl_radius_x,
                    self.bowl_radius_y,
                    self._rng,
                    stage=self.stage,
                )
            )

    def _update_pickups(self, dt: float) -> None:
        for pickup in self.pickups:
            if pickup.kind == "green":
                update_green_pickup(
                    pickup,
                    self.player,
                    self.enemies,
                    self.nutrients,
                    dt,
                    self._rng,
                )
            elif pickup.kind == "red":
                update_red_pickup(pickup, self.pickups, dt, self._rng)
            elif pickup.kind == "yellow":
                update_yellow_pickup(pickup, self.player, dt, self._rng)
            if pickup.attached_to is not None:
                continue
            for obj in self.obstacles:
                if distance(pickup.x, pickup.y, obj.x, obj.y) < pickup.radius + obj.radius:
                    pickup.attached_to = obj.id
                    pickup.vx *= 0.2
                    pickup.vy *= 0.2
                    break

    def _update_enemies(self, dt: float) -> None:
        default_speed = float(cfg("enemy_speed_patrol"))
        whirlpool_flee = float(cfg("whirlpool_flee_speed"))
        friction = float(cfg("physics_friction"))
        drive_mass = 24.0
        cx, cy = self.bowl_center_x, self.bowl_center_y
        for enemy in self.enemies:
            if enemy.cooldown_left > 0:
                enemy.cooldown_left = max(0.0, enemy.cooldown_left - dt)
                if enemy.state == "cooldown" and enemy.cooldown_left <= 0:
                    enemy.state = "patrol"

            behavior = str(get_enemy_def(enemy.kind).get("behavior", enemy.kind))
            if behavior == "lurker" and enemy.burst_left > 0:
                enemy.burst_left = max(0.0, enemy.burst_left - dt)
            if enemy.is_boss and enemy.burst_left > 0:
                enemy.burst_left = max(0.0, enemy.burst_left - dt)

            if self.phase == "hazard" and self._hazard_kind == "flush":
                dx, dy = normalize(enemy.x - cx, enemy.y - cy)
                enemy.state = "flee"
                enemy.move_speed = whirlpool_flee
                if dx != 0.0 or dy != 0.0:
                    accel = whirlpool_flee * friction * drive_mass * 1.25
                    enemy.vx, enemy.vy = apply_acceleration(
                        enemy.vx,
                        enemy.vy,
                        dx,
                        dy,
                        accel,
                        drive_mass,
                        dt,
                    )
                continue

            intent = compute_mob_intent(enemy, self.player, self.enemies, self.pickups)
            enemy.state = intent.state
            enemy.move_speed = intent.speed if intent.speed > 0 else default_speed
            ax, ay = intent.ax, intent.ay
            if ax != 0.0 or ay != 0.0:
                wobble = math.sin(self.match_timer * 4.6 + enemy.x * 0.03 + enemy.y * 0.02)
                wobble += math.sin(self.match_timer * 9.1 + enemy.radius) * 0.45
                px, py = -ay, ax
                ax, ay = normalize(ax + px * wobble * 0.85, ay + py * wobble * 0.85)
                target_speed = max(enemy.move_speed, default_speed * 0.5)
                accel = target_speed * friction * drive_mass * 1.25
                enemy.vx, enemy.vy = apply_acceleration(
                    enemy.vx,
                    enemy.vy,
                    ax,
                    ay,
                    accel,
                    drive_mass,
                    dt,
                )

    def _check_enemy_hits(self) -> None:
        import random

        for enemy in self.enemies:
            if enemy.cooldown_left > 0:
                continue
            if distance(self.player.x, self.player.y, enemy.x, enemy.y) >= self.player.radius + enemy.radius:
                continue
            if can_eat_entity(enemy.radius, self.player.radius):
                continue
            _dash_bonus, _drain, iframe_chance = perk_dash_stats(self.player.perk_levels)
            if self.player.is_sprinting and iframe_chance > 0 and random.random() < iframe_chance:
                enemy.cooldown_left = float(cfg("enemy_hit_cooldown")) * 0.5
                continue
            dmg_mult, kb_mult = perk_shell_mults(self.player.perk_levels)
            if enemy.is_boss:
                apply_boss_hit(enemy, self.player, damage_mult=dmg_mult)
            else:
                enemy_def = get_enemy_def(enemy.kind)
                damage = float(cfg("hit_damage")) * float(enemy_def.get("damage_mult", 1.0)) * dmg_mult
                self.player.red = max(0.0, self.player.red - damage)
                drain = float(enemy_def.get("drain", 0.0))
                if drain > 0.0:
                    self.player.red = max(0.0, self.player.red - drain * dmg_mult)
            enemy.cooldown_left = float(cfg("enemy_hit_cooldown"))
            enemy.state = "cooldown"
            dx, dy = normalize(self.player.x - enemy.x, self.player.y - enemy.y)
            if dx != 0.0 or dy != 0.0:
                kb = float(cfg("knockback_distance")) * kb_mult
                self.player.vx += dx * kb * 0.5
                self.player.vy += dy * kb * 0.5

    def _player_move_angle(self) -> float:
        speed = math.hypot(self.player.vx, self.player.vy)
        if speed > 80.0:
            return math.atan2(self.player.vy, self.player.vx)
        return self.player.facing_angle

    def _release_grab(self) -> None:
        self.player.grab_kind = "none"
        self.player.grab_pickup_index = -1
        self.player.grab_obstacle_id = -1
        self.player.grab_time_left = 0.0

    def _grab_hold_distance(self) -> float:
        held_radius = 0.0
        if self.player.grab_kind == "pickup":
            index = self.player.grab_pickup_index
            if 0 <= index < len(self.pickups):
                held_radius = self.pickups[index].radius
        elif self.player.grab_kind == "obstacle":
            for obj in self.obstacles:
                if obj.id == self.player.grab_obstacle_id:
                    held_radius = obj.radius
                    break
        return self.player.radius + held_radius + 14.0

    def _update_tentacle_grab(self, dt: float) -> None:
        if self.player.grab_kind == "none":
            return

        grab_range, grab_duration, _ = perk_tentacle_stats(self.player.perk_levels)
        if grab_range <= 0.0 or grab_duration <= 0.0:
            self._release_grab()
            return

        facing = self.player.facing_angle
        hold_dist = self._grab_hold_distance()
        hold_x = self.player.x + math.cos(facing) * hold_dist
        hold_y = self.player.y + math.sin(facing) * hold_dist

        self.player.grab_time_left -= dt
        if self.player.grab_kind == "pickup":
            index = self.player.grab_pickup_index
            if 0 <= index < len(self.pickups):
                pickup = self.pickups[index]
                pickup.x = hold_x
                pickup.y = hold_y
                pickup.vx = self.player.vx
                pickup.vy = self.player.vy
            else:
                self._release_grab()
                return
        elif self.player.grab_kind == "obstacle":
            self._release_grab()
            return

        if self.player.grab_time_left <= 0.0:
            self._release_grab()

    def _try_start_grab(self) -> bool:
        grab_range, grab_duration, _ = perk_tentacle_stats(self.player.perk_levels)
        if grab_range <= 0.0 or grab_duration <= 0.0:
            return False
        if self.player.grab_kind != "none":
            return False
        target = find_grab_target_in_front(
            self.player.x,
            self.player.y,
            self.player.facing_angle,
            grab_range,
            self.pickups,
        )
        if target is None:
            return False
        kind, key = target
        if kind != "pickup":
            return False
        self.player.grab_kind = "pickup"
        self.player.grab_pickup_index = key
        self.player.grab_obstacle_id = -1
        self.player.grab_time_left = grab_duration
        self.player.action_cooldown = 0.35
        return True

    def _try_spike_attack(self) -> bool:
        damage, spike_length, spike_count, cooldown = perk_spike_contact_stats(self.player.perk_levels)
        if damage <= 0.0 or spike_length <= 0.0 or spike_count <= 0:
            return False

        direction = self._player_move_angle()
        segments = spike_segments(
            self.player.x,
            self.player.y,
            self.player.radius,
            direction,
            spike_length,
            spike_count,
        )
        hit_any = False
        spike_removed: list[int] = []
        for index, enemy in enumerate(self.enemies):
            if enemy.cooldown_left > 0:
                continue
            if not enemy_hits_spike_segments(enemy, segments):
                continue
            hit_any = True
            dead = apply_spike_damage(enemy, damage)
            if dead:
                self.pickups.extend(split_enemy_to_greens(enemy, self._rng))
                spike_removed.append(index)
                self.player.enemies_eaten += 1
        if spike_removed:
            self.enemies = [e for i, e in enumerate(self.enemies) if i not in spike_removed]
        self.player.action_cooldown = cooldown
        return hit_any or True

    def _try_player_action(self) -> None:
        if self.player.action_cooldown > 0:
            return
        if self._try_start_grab():
            return
        self._try_spike_attack()

    def _check_game_over(self) -> None:
        if self.player.weight <= 0:
            self.game_over = True

    @staticmethod
    def _normalize_color(color: str) -> str:
        if not isinstance(color, str) or not color.startswith("#"):
            return "#60a5fa"
        hex_part = color[1:]
        if len(hex_part) == 3 and all(c in "0123456789abcdefABCDEF" for c in hex_part):
            return color.lower()
        if len(hex_part) == 6 and all(c in "0123456789abcdefABCDEF" for c in hex_part):
            return color.lower()
        return "#60a5fa"


engine = GameEngine()
