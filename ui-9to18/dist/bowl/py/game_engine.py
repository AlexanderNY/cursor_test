from __future__ import annotations

import json
import math
import random

from ai.mob_brain import compute_mob_intent
from combat import (
    apply_green_pickup,
    apply_red_pickup,
    apply_spike_damage,
    can_eat_entity,
    find_spike_target,
    init_enemy_health,
    split_enemy_to_greens,
    try_consume_entity,
)
from config import cfg, load_config_from_json
from entities import (
    Enemy,
    Pickup,
    Player,
    WorldObject,
    clamp_circle_in_ellipse,
    clamp_circle_in_rect,
    distance,
    is_far_enough,
    normalize,
    random_point_in_ellipse,
)
from perks import (
    active_perk_ids,
    can_upgrade,
    perk_hook_stats,
    perk_speed_mult,
    perk_spike_stats,
    perk_visibility,
    upgrade_perk,
    load_perks_from_json,
)
from physics import (
    apply_acceleration,
    apply_friction,
    entity_mass,
    integrate_body,
    resolve_circle_bounce,
    resolve_mover_obstacle,
)
from save_codec import export_state, import_state
from spawn_system import try_spawn_enemy_batch, try_spawn_green_batch, try_spawn_red_batch

GamePhase = str


class GameEngine:
    def __init__(self) -> None:
        self.player = Player(x=0.0, y=0.0)
        self.pickups: list[Pickup] = []
        self.enemies: list[Enemy] = []
        self.obstacles: list[WorldObject] = []
        self.world_width = 1600.0
        self.world_height = 900.0
        self.game_over = False
        self.level = 1
        self.pending_perk_select = False
        self.bowl_center_x = 800.0
        self.bowl_center_y = 450.0
        self.bowl_radius_x = 400.0
        self.bowl_radius_y = 400.0
        self.phase: GamePhase = "normal"
        self.match_timer = 0.0
        self.whirlpool_time_left = 0.0
        self.whirlpool_angle = 0.0
        self._last_perk_milestone = 0
        self._green_spawn_timer = 0.0
        self._red_spawn_timer = 0.0
        self._enemy_spawn_timer = 0.0
        self._obstacle_id = 1
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
    ) -> None:
        self._rng = random.Random()
        self.world_width = viewport_width * cfg("world_scale")
        self.world_height = viewport_height * cfg("world_scale")
        self.bowl_center_x = self.world_width / 2.0
        self.bowl_center_y = self.world_height / 2.0
        self.bowl_radius_x = min(self.world_width, self.world_height) * 0.42
        self.bowl_radius_y = min(self.world_width, self.world_height) * 0.42
        self.level = 1
        self.game_over = False
        self.phase = "normal"
        self.match_timer = 0.0
        self.whirlpool_time_left = 0.0
        self.whirlpool_angle = 0.0
        self._last_perk_milestone = 0
        self._green_spawn_timer = 0.0
        self._red_spawn_timer = 0.0
        self._enemy_spawn_timer = 0.0
        self.player = Player(
            x=self.bowl_center_x,
            y=self.bowl_center_y,
            radius=float(cfg("base_player_radius")),
            color=self._normalize_color(color),
        )
        self.pickups = []
        self.enemies = []
        self.obstacles = []
        self._obstacle_id = 1
        self._spawn_obstacles()
        self._spawn_pickups("green", int(cfg("green_pickup_count")))
        self._spawn_pickups("red", int(cfg("red_pickup_count")))
        self._spawn_enemies(int(cfg("enemy_count")))
        if perk and perk != "none":
            self.player.perk_levels = {perk: 1}
            self.pending_perk_select = False
        else:
            self.pending_perk_select = True

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
        self._last_perk_milestone = int(data.get("last_perk_milestone", 0))
        self._green_spawn_timer = float(data.get("green_spawn_timer", 0.0))
        self._red_spawn_timer = float(data.get("red_spawn_timer", 0.0))
        self._enemy_spawn_timer = float(data.get("enemy_spawn_timer", 0.0))
        max_id = max((obj.id for obj in self.obstacles), default=0)
        self._obstacle_id = max_id + 1

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
        state["last_perk_milestone"] = self._last_perk_milestone
        state["green_spawn_timer"] = self._green_spawn_timer
        state["red_spawn_timer"] = self._red_spawn_timer
        state["enemy_spawn_timer"] = self._enemy_spawn_timer
        return state

    def get_render_state(self, viewport_width: float, viewport_height: float) -> dict:
        base_vis = float(cfg("base_visibility_radius"))
        visibility, lightness = perk_visibility(self.player.perk_levels, base_vis)

        camera_x = self.player.x - viewport_width / 2.0
        camera_y = self.player.y - viewport_height / 2.0
        camera_x = max(0.0, min(self.world_width - viewport_width, camera_x))
        camera_y = max(0.0, min(self.world_height - viewport_height, camera_y))

        per_enemy = int(cfg("enemies_per_perk"))
        eaten_mod = self.player.enemies_eaten % per_enemy if per_enemy else 0

        return {
            "level": self.level,
            "eat_count": self.player.eat_count,
            "enemies_eaten": self.player.enemies_eaten,
            "enemies_eaten_mod": eaten_mod,
            "enemies_per_perk": per_enemy,
            "pending_perk_select": self.pending_perk_select,
            "world": {"width": self.world_width, "height": self.world_height},
            "bowl": {
                "cx": self.bowl_center_x,
                "cy": self.bowl_center_y,
                "rx": self.bowl_radius_x,
                "ry": self.bowl_radius_y,
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
                "perk_levels": dict(self.player.perk_levels),
                "perks": active_perk_ids(self.player.perk_levels),
                "facing_angle": self.player.facing_angle,
                "color": self.player.color,
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
                    "max_health": e.radius,
                    "state": e.state,
                    "is_boss": e.is_boss,
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
            "boss_active": any(e.is_boss for e in self.enemies),
        }

    def update(self, dt: float, move_x: float, move_y: float, action: bool) -> None:
        if self.game_over or self.pending_perk_select:
            return

        if self.player.action_cooldown > 0:
            self.player.action_cooldown = max(0.0, self.player.action_cooldown - dt)

        if self.phase == "normal":
            self.match_timer += dt
            if self.match_timer >= float(cfg("match_timer_sec")):
                self._start_whirlpool()

        if self.phase == "whirlpool":
            self._update_whirlpool(dt)

        self._update_edge_spawns(dt)
        self._apply_player_input(dt, move_x, move_y)

        if action:
            if self.player.has_perk("tentacle"):
                self._try_hook()
            elif self.player.has_perk("spike"):
                self._try_spike()

        self._update_pickups(dt)
        self._update_enemies(dt)
        self._integrate_all_bodies(dt)
        self._resolve_physics_collisions()
        self._process_eating()
        self._check_enemy_hits()
        self._check_perk_milestone()
        self._check_game_over()

    def _update_edge_spawns(self, dt: float) -> None:
        if not cfg("edge_spawn_enabled"):
            return

        self._green_spawn_timer += dt
        self._red_spawn_timer += dt
        self._enemy_spawn_timer += dt

        occupied = self._occupied_points()

        if self._green_spawn_timer >= float(cfg("edge_spawn_green_interval_sec")):
            self._green_spawn_timer = 0.0
            try_spawn_green_batch(
                self.pickups,
                self.world_width,
                self.world_height,
                self.player.x,
                self.player.y,
                occupied,
                self._rng,
            )

        if self._red_spawn_timer >= float(cfg("edge_spawn_red_interval_sec")):
            self._red_spawn_timer = 0.0
            try_spawn_red_batch(
                self.pickups,
                self.world_width,
                self.world_height,
                self.player.x,
                self.player.y,
                occupied,
                self._rng,
            )

        if self._enemy_spawn_timer >= float(cfg("edge_spawn_enemy_interval_sec")):
            self._enemy_spawn_timer = 0.0
            try_spawn_enemy_batch(
                self.enemies,
                self.world_width,
                self.world_height,
                self.player.x,
                self.player.y,
                occupied,
                self.bowl_center_x,
                self.bowl_center_y,
                self.bowl_radius_x,
                self.bowl_radius_y,
                self._rng,
            )

    def _apply_player_input(self, dt: float, move_x: float, move_y: float) -> None:
        nx, ny = normalize(move_x, move_y)
        if nx != 0.0 or ny != 0.0:
            self.player.facing_angle = math.atan2(ny, nx)
        mass = entity_mass(self.player.radius, self.player.weight)
        accel = float(cfg("physics_player_accel")) * perk_speed_mult(self.player.perk_levels)
        self.player.vx, self.player.vy = apply_acceleration(
            self.player.vx,
            self.player.vy,
            nx,
            ny,
            accel,
            mass,
            dt,
        )
        if self.phase == "whirlpool":
            flee = float(cfg("whirlpool_flee_speed"))
            dx, dy = normalize(self.player.x - self.bowl_center_x, self.player.y - self.bowl_center_y)
            self.player.vx += dx * flee * dt
            self.player.vy += dy * flee * dt

    def _integrate_all_bodies(self, dt: float) -> None:
        friction = float(cfg("physics_friction"))
        max_speed = float(cfg("physics_max_speed"))
        obs_friction = float(cfg("obstacle_friction"))

        self.player.x, self.player.y, self.player.vx, self.player.vy = integrate_body(
            self.player.x,
            self.player.y,
            self.player.vx,
            self.player.vy,
            self.player.radius,
            dt,
            friction,
            float(cfg("player_speed")),
            self.world_width,
            self.world_height,
            self.bowl_center_x,
            self.bowl_center_y,
            self.bowl_radius_x,
            self.bowl_radius_y,
            False,
        )

        for enemy in self.enemies:
            enemy.x, enemy.y, enemy.vx, enemy.vy = integrate_body(
                enemy.x,
                enemy.y,
                enemy.vx,
                enemy.vy,
                enemy.radius,
                dt,
                friction,
                max_speed,
                self.world_width,
                self.world_height,
                self.bowl_center_x,
                self.bowl_center_y,
                self.bowl_radius_x,
                self.bowl_radius_y,
                not enemy.is_boss,
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
                self.bowl_radius_x,
                self.bowl_radius_y,
                True,
            )

        for obj in self.obstacles:
            obj.vx, obj.vy = apply_friction(obj.vx, obj.vy, obs_friction, dt)
            obj.x += obj.vx * dt
            obj.y += obj.vy * dt
            obj.x, obj.y = clamp_circle_in_rect(
                obj.x, obj.y, obj.radius, self.world_width, self.world_height
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

    def _process_eating(self) -> None:
        remaining_pickups: list[Pickup] = []
        for pickup in self.pickups:
            eaten = False
            if pickup.kind == "green":
                if distance(self.player.x, self.player.y, pickup.x, pickup.y) < self.player.radius + pickup.radius:
                    apply_green_pickup(self.player, pickup)
                    self.player.eat_count += 1
                    eaten = True
                else:
                    for enemy in self.enemies:
                        if distance(enemy.x, enemy.y, pickup.x, pickup.y) < enemy.radius + pickup.radius:
                            apply_green_pickup(enemy, pickup)
                            eaten = True
                            break
            elif distance(self.player.x, self.player.y, pickup.x, pickup.y) < self.player.radius + pickup.radius:
                apply_red_pickup(self.player, pickup)
                self.player.eat_count += 1
                eaten = True
            if not eaten:
                remaining_pickups.append(pickup)
        self.pickups = remaining_pickups

        self._process_entity_combat()

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
        if spike_removed:
            self.enemies = [e for i, e in enumerate(self.enemies) if i not in spike_removed]
        self.pickups.extend(new_greens)

    def _check_perk_milestone(self) -> None:
        step = int(cfg("enemies_per_perk"))
        eaten = self.player.enemies_eaten
        if eaten <= 0 or step <= 0:
            return
        if eaten % step != 0:
            return
        if eaten == self._last_perk_milestone:
            return
        self._last_perk_milestone = eaten
        self.level += 1
        self.pending_perk_select = True

    def _start_whirlpool(self) -> None:
        self.phase = "whirlpool"
        self.whirlpool_time_left = float(cfg("whirlpool_duration_sec"))
        self.whirlpool_angle = 0.0

    def _end_whirlpool(self) -> None:
        self.phase = "boss"
        self.whirlpool_time_left = 0.0
        self.enemies = [e for e in self.enemies if not e.is_boss]
        self._spawn_boss()

    def _spawn_boss(self) -> None:
        angle = self._rng.uniform(0.0, math.tau)
        dist = float(cfg("boss_spawn_distance"))
        radius = float(cfg("boss_radius"))
        bx = self.bowl_center_x + math.cos(angle) * dist
        by = self.bowl_center_y + math.sin(angle) * dist
        bx, by = clamp_circle_in_rect(bx, by, radius, self.world_width, self.world_height)
        self.enemies.append(
            Enemy(
                x=bx,
                y=by,
                radius=radius,
                health=radius,
                state="chase",
                is_boss=True,
            )
        )

    def _update_whirlpool(self, dt: float) -> None:
        self.whirlpool_time_left -= dt
        self.whirlpool_angle += float(cfg("whirlpool_spin_speed")) * dt
        pull = float(cfg("whirlpool_pull_speed")) * dt
        flee = float(cfg("whirlpool_flee_speed")) * dt

        for obj in self.obstacles:
            dx, dy = normalize(self.bowl_center_x - obj.x, self.bowl_center_y - obj.y)
            if dx != 0.0 or dy != 0.0:
                obj.vx += dx * pull / max(obj.mass, 1.0)
                obj.vy += dy * pull / max(obj.mass, 1.0)

        for pickup in self.pickups:
            if pickup.attached_to is not None:
                for obj in self.obstacles:
                    if obj.id == pickup.attached_to:
                        pickup.x, pickup.y = obj.x, obj.y
                        break
            else:
                dx, dy = normalize(pickup.x - self.bowl_center_x, pickup.y - self.bowl_center_y)
                pickup.vx += dx * flee
                pickup.vy += dy * flee

        for enemy in self.enemies:
            dx, dy = normalize(enemy.x - self.bowl_center_x, enemy.y - self.bowl_center_y)
            enemy.vx += dx * flee
            enemy.vy += dy * flee

        if self.whirlpool_time_left <= 0:
            self._end_whirlpool()

    def _occupied_points(self) -> list[tuple[float, float]]:
        points = [(self.player.x, self.player.y)]
        points.extend((p.x, p.y) for p in self.pickups)
        points.extend((e.x, e.y) for e in self.enemies)
        points.extend((o.x, o.y) for o in self.obstacles)
        return points

    def _spawn_obstacles(self) -> None:
        kinds = cfg("obstacle_kinds")
        for _ in range(int(cfg("obstacle_count"))):
            kind = self._rng.choice(kinds)
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
            if kind == "paper":
                width, height = 36.0, 28.0
                radius = 18.0
                mass = float(cfg("paper_mass"))
                pushable = False
            else:
                width, height = 12.0, 48.0
                radius = 24.0
                mass = float(cfg("toothbrush_mass"))
                pushable = True
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
            radius = self._rng.uniform(float(cfg("enemy_radius_min")), float(cfg("enemy_radius_max")))
            waypoints = [
                random_point_in_ellipse(
                    self.bowl_center_x,
                    self.bowl_center_y,
                    self.bowl_radius_x,
                    self.bowl_radius_y,
                    30.0,
                    self._rng,
                )
                for _ in range(int(cfg("waypoints_per_enemy")))
            ]
            self.enemies.append(
                Enemy(
                    x=x,
                    y=y,
                    radius=radius,
                    health=init_enemy_health(radius),
                    waypoints=waypoints,
                )
            )

    def _update_pickups(self, dt: float) -> None:
        for pickup in self.pickups:
            if pickup.kind != "green" or pickup.attached_to is not None:
                continue
            pickup.wander_timer -= dt
            if pickup.wander_timer <= 0:
                pickup.wander_timer = float(cfg("pickup_wander_interval"))
                angle = self._rng.uniform(0.0, math.tau)
                speed = float(cfg("green_pickup_speed"))
                pickup.vx += math.cos(angle) * speed * 0.35
                pickup.vy += math.sin(angle) * speed * 0.35
            for obj in self.obstacles:
                if distance(pickup.x, pickup.y, obj.x, obj.y) < pickup.radius + obj.radius:
                    pickup.attached_to = obj.id
                    pickup.vx *= 0.2
                    pickup.vy *= 0.2
                    break

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            if enemy.cooldown_left > 0:
                enemy.cooldown_left = max(0.0, enemy.cooldown_left - dt)
                if enemy.state == "cooldown" and enemy.cooldown_left <= 0:
                    enemy.state = "patrol"

            intent = compute_mob_intent(enemy, self.player, self.enemies, self.pickups)
            enemy.state = intent.state
            if intent.ax != 0.0 or intent.ay != 0.0:
                em = entity_mass(enemy.radius)
                enemy.vx, enemy.vy = apply_acceleration(
                    enemy.vx,
                    enemy.vy,
                    intent.ax,
                    intent.ay,
                    float(cfg("physics_enemy_accel")),
                    em,
                    dt,
                )

    def _check_enemy_hits(self) -> None:
        for enemy in self.enemies:
            if enemy.cooldown_left > 0:
                continue
            if distance(self.player.x, self.player.y, enemy.x, enemy.y) >= self.player.radius + enemy.radius:
                continue
            if can_eat_entity(enemy.radius, self.player.radius):
                continue
            damage = float(cfg("boss_hit_damage") if enemy.is_boss else cfg("hit_damage"))
            self.player.red = max(0.0, self.player.red - damage)
            enemy.cooldown_left = float(cfg("enemy_hit_cooldown"))
            enemy.state = "cooldown"
            dx, dy = normalize(self.player.x - enemy.x, self.player.y - enemy.y)
            if dx != 0.0 or dy != 0.0:
                kb = float(cfg("knockback_distance"))
                self.player.vx += dx * kb * 0.5
                self.player.vy += dy * kb * 0.5

    def _try_hook(self) -> None:
        if self.player.action_cooldown > 0:
            return
        hook_range, hook_pull, hook_cd = perk_hook_stats(self.player.perk_levels)
        if hook_range <= 0:
            return
        best: Pickup | None = None
        best_dist = hook_range
        for pickup in self.pickups:
            if pickup.kind != "green":
                continue
            dist = distance(self.player.x, self.player.y, pickup.x, pickup.y)
            if dist < best_dist:
                best_dist = dist
                best = pickup
        if best is None:
            return
        dx, dy = normalize(self.player.x - best.x, self.player.y - best.y)
        if dx == 0.0 and dy == 0.0:
            return
        best.vx += dx * hook_pull * 0.4
        best.vy += dy * hook_pull * 0.4
        best.x += dx * hook_pull * 0.6
        best.y += dy * hook_pull * 0.6
        self.player.action_cooldown = hook_cd

    def _try_spike(self) -> None:
        if self.player.action_cooldown > 0:
            return
        damage, spike_range, spike_arc, spike_cd = perk_spike_stats(self.player.perk_levels)
        if damage <= 0:
            return
        target = find_spike_target(
            self.player.x,
            self.player.y,
            self.player.facing_angle,
            spike_range,
            spike_arc,
            self.enemies,
        )
        if target is None:
            return
        dead = apply_spike_damage(target, damage)
        if dead:
            self.pickups.extend(split_enemy_to_greens(target, self._rng))
            self.enemies = [e for e in self.enemies if e is not target]
            self.player.enemies_eaten += 1
        self.player.action_cooldown = spike_cd

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
