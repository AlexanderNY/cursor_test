from __future__ import annotations

from entities import Enemy, Pickup, Player, WorldObject


def export_state(
    version: int,
    player: Player,
    pickups: list[Pickup],
    enemies: list[Enemy],
    obstacles: list[WorldObject],
    world_width: float,
    world_height: float,
    game_over: bool,
    level: int,
    bowl_center_x: float,
    bowl_center_y: float,
    bowl_radius_x: float,
    bowl_radius_y: float,
    pending_perk_select: bool,
) -> dict:
    return {
        "version": version,
        "level": level,
        "pending_perk_select": pending_perk_select,
        "player": {
            "x": player.x,
            "y": player.y,
            "red": player.red,
            "green": player.green,
            "radius": player.radius,
            "vx": player.vx,
            "vy": player.vy,
            "perk_levels": dict(player.perk_levels),
            "facing_angle": player.facing_angle,
            "action_cooldown": player.action_cooldown,
            "eat_count": player.eat_count,
            "enemies_eaten": player.enemies_eaten,
            "color": player.color,
        },
        "pickups": [
            {
                "x": pickup.x,
                "y": pickup.y,
                "kind": pickup.kind,
                "radius": pickup.radius,
                "vx": pickup.vx,
                "vy": pickup.vy,
                "wander_timer": pickup.wander_timer,
                "spike_angle": pickup.spike_angle,
                "attached_to": pickup.attached_to,
            }
            for pickup in pickups
        ],
        "enemies": [
            {
                "x": enemy.x,
                "y": enemy.y,
                "radius": enemy.radius,
                "health": enemy.health,
                "vx": enemy.vx,
                "vy": enemy.vy,
                "state": enemy.state,
                "cooldown_left": enemy.cooldown_left,
                "waypoint_index": enemy.waypoint_index,
                "waypoints": [[wx, wy] for wx, wy in enemy.waypoints],
                "is_boss": enemy.is_boss,
            }
            for enemy in enemies
        ],
        "obstacles": [
            {
                "id": obj.id,
                "x": obj.x,
                "y": obj.y,
                "kind": obj.kind,
                "radius": obj.radius,
                "angle": obj.angle,
                "width": obj.width,
                "height": obj.height,
                "vx": obj.vx,
                "vy": obj.vy,
                "mass": obj.mass,
                "pushable": obj.pushable,
            }
            for obj in obstacles
        ],
        "world": {"width": world_width, "height": world_height},
        "bowl": {
            "cx": bowl_center_x,
            "cy": bowl_center_y,
            "rx": bowl_radius_x,
            "ry": bowl_radius_y,
        },
        "game_over": game_over,
    }


def _migrate_perk_levels(player_data: dict) -> dict[str, int]:
    if "perk_levels" in player_data:
        raw = player_data["perk_levels"]
        return {str(k): int(v) for k, v in raw.items()}
    perks = player_data.get("perks", [])
    if not perks and player_data.get("perk", "none") not in ("none", None):
        perks = [player_data["perk"]]
    return {str(p): 1 for p in perks}


def import_state(data: dict) -> tuple[
    Player,
    list[Pickup],
    list[Enemy],
    list[WorldObject],
    float,
    float,
    bool,
    int,
    float,
    float,
    float,
    float,
    bool,
]:
    player_data = data["player"]
    player = Player(
        x=float(player_data["x"]),
        y=float(player_data["y"]),
        red=float(player_data["red"]),
        green=float(player_data["green"]),
        radius=float(player_data.get("radius", 18.0)),
        vx=float(player_data.get("vx", 0.0)),
        vy=float(player_data.get("vy", 0.0)),
        perk_levels=_migrate_perk_levels(player_data),
        facing_angle=float(player_data.get("facing_angle", 0.0)),
        action_cooldown=float(player_data.get("action_cooldown", 0.0)),
        eat_count=int(player_data.get("eat_count", 0)),
        enemies_eaten=int(player_data.get("enemies_eaten", 0)),
        color=str(player_data.get("color", "#60a5fa")),
    )

    pickups = [
        Pickup(
            x=float(item["x"]),
            y=float(item["y"]),
            kind=item["kind"],
            radius=float(item.get("radius", 10.0)),
            vx=float(item.get("vx", 0.0)),
            vy=float(item.get("vy", 0.0)),
            wander_timer=float(item.get("wander_timer", 0.0)),
            spike_angle=float(item.get("spike_angle", 0.0)),
            attached_to=item.get("attached_to"),
        )
        for item in data.get("pickups", [])
    ]

    enemies: list[Enemy] = []
    for item in data.get("enemies", []):
        waypoints = [(float(wx), float(wy)) for wx, wy in item.get("waypoints", [])]
        radius = float(item.get("radius", 16.0))
        enemies.append(
            Enemy(
                x=float(item["x"]),
                y=float(item["y"]),
                radius=radius,
                health=float(item.get("health", radius)),
                vx=float(item.get("vx", 0.0)),
                vy=float(item.get("vy", 0.0)),
                state=item.get("state", "patrol"),
                cooldown_left=float(item.get("cooldown_left", 0.0)),
                waypoint_index=int(item.get("waypoint_index", 0)),
                waypoints=waypoints,
                is_boss=bool(item.get("is_boss", False)),
            )
        )

    obstacles: list[WorldObject] = []
    for item in data.get("obstacles", []):
        kind = item["kind"]
        default_mass = 90.0 if kind == "paper" else 28.0
        obstacles.append(
            WorldObject(
                id=int(item["id"]),
                x=float(item["x"]),
                y=float(item["y"]),
                kind=kind,
                radius=float(item["radius"]),
                angle=float(item.get("angle", 0.0)),
                width=float(item.get("width", item["radius"] * 2)),
                height=float(item.get("height", item["radius"] * 2)),
                vx=float(item.get("vx", 0.0)),
                vy=float(item.get("vy", 0.0)),
                mass=float(item.get("mass", default_mass)),
                pushable=bool(item.get("pushable", kind == "toothbrush")),
            )
        )

    world = data.get("world", {})
    world_width = float(world.get("width", 1600))
    world_height = float(world.get("height", 900))
    game_over = bool(data.get("game_over", False))
    level = int(data.get("level", 1))
    pending_perk_select = bool(data.get("pending_perk_select", False))

    bowl = data.get("bowl", {})
    bowl_center_x = float(bowl.get("cx", world_width / 2.0))
    bowl_center_y = float(bowl.get("cy", world_height / 2.0))
    bowl_radius_x = float(bowl.get("rx", min(world_width, world_height) * 0.42))
    bowl_radius_y = float(bowl.get("ry", min(world_width, world_height) * 0.42))

    return (
        player,
        pickups,
        enemies,
        obstacles,
        world_width,
        world_height,
        game_over,
        level,
        bowl_center_x,
        bowl_center_y,
        bowl_radius_x,
        bowl_radius_y,
        pending_perk_select,
    )
