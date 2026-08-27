#!/usr/bin/env python3
"""Поочерёдный подъём сервисов docker compose (меньше пик RAM на Windows).

Примеры:
  python deploy/scripts/compose_up_sequential.py
  # default: core + tg/vk/url/dzen/wp-bot
  python deploy/scripts/compose_up_sequential.py --interactive
  python deploy/scripts/compose_up_sequential.py --profiles bots --build --force-recreate --no-deps
  python deploy/scripts/compose_up_sequential.py --with 9to18,edge
  python deploy/scripts/compose_up_sequential.py --with e2e --build --delay 5
  python deploy/scripts/compose_up_sequential.py --only minio,auth,core,gateway,ui --no-deps
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yaml"

UI_9TO18_COMPOSE = REPO_ROOT / "deploy" / "ui-9to18" / "docker-compose.yml"
UI_EDGE_COMPOSE = REPO_ROOT / "deploy" / "ui-edge" / "docker-compose.yml"
E2E_COMPOSE = REPO_ROOT / "deploy" / "e2e-tester" / "docker-compose.yml"
E2E_ENV = REPO_ROOT / "deploy" / "e2e-tester" / ".env"

# Порядок с учётом depends_on и типичного bootstrap.
CORE_ORDER: list[str] = [
    "minio",
    "auth",
    "core",
    "gateway",
    "ui",
    "scheduler",
    "collector",
    "processor",
]

# Боты в сценарии по умолчанию (без --profiles bots).
DEFAULT_BOTS_ORDER: list[str] = [
    "tg-bot",
    "vk-bot",
    "url-bot",
    "dzen-bot",
    "wp-bot",
]

BOTS_ORDER: list[str] = [
    "wp-bot",
    "tg-bot",
    "vk-bot",
    "url-bot",
    "instagram-bot",
    "th-bot",
    "tw-bot",
    "dzen-bot",
    "tg-game",
]

AI_ORDER: list[str] = [
    "ollama",
    "ollama-init",
]

KNOWN = set(CORE_ORDER) | set(BOTS_ORDER) | set(AI_ORDER)

PROFILE_SERVICES: dict[str, list[str]] = {
    "bots": BOTS_ORDER,
    "ai": AI_ORDER,
}

SERVICE_PROFILE: dict[str, str] = {
    **{name: "bots" for name in BOTS_ORDER},
    **{name: "ai" for name in AI_ORDER},
}

# Внешние стеки (после основного compose).
EXTRA_ORDER: list[str] = ["9to18", "edge", "e2e"]
EXTRA_ALIASES: dict[str, str] = {
    "9to18": "9to18",
    "ui-9to18": "9to18",
    "edge": "edge",
    "ui-edge": "edge",
    "e2e": "e2e",
    "tester": "e2e",
    "e2e-tester": "e2e",
}


@dataclass
class UpFlags:
    build: bool = False
    no_deps: bool = False
    force_recreate: bool = False
    pull_always: bool = False
    remove_orphans: bool = False
    renew_anon_volumes: bool = False

    def as_args(self) -> list[str]:
        args: list[str] = []
        if self.build:
            args.append("--build")
        if self.no_deps:
            args.append("--no-deps")
        if self.force_recreate:
            args.append("--force-recreate")
        if self.pull_always:
            args.extend(["--pull", "always"])
        if self.remove_orphans:
            args.append("--remove-orphans")
        if self.renew_anon_volumes:
            args.append("--renew-anon-volumes")
        return args


@dataclass
class RunConfig:
    profiles: list[str] = field(default_factory=list)
    only: list[str] | None = None
    extras: list[str] = field(default_factory=list)
    flags: UpFlags = field(default_factory=UpFlags)
    delay: float = 3.0
    wait_health: bool = False
    wait_timeout: float = 120.0
    continue_on_error: bool = False
    dry_run: bool = False
    skip_main: bool = False
    ensure_edge_net: bool = True


def _docker_compose_bin() -> list[str]:
    if shutil.which("docker"):
        return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    raise SystemExit("Не найден docker / docker-compose в PATH")


def _run(cmd: list[str], *, dry_run: bool, cwd: Path | None = None) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    if dry_run:
        return 0
    completed = subprocess.run(cmd, cwd=cwd or REPO_ROOT)
    return int(completed.returncode)


def _parse_csv(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _normalize_extras(raw_items: list[str]) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        key = EXTRA_ALIASES.get(item.lower())
        if key is None:
            raise SystemExit(
                f"Неизвестный extra: {item}. Доступны: {', '.join(EXTRA_ORDER)} "
                f"(алиасы: ui-9to18, ui-edge, tester)"
            )
        if key not in seen:
            seen.add(key)
            resolved.append(key)
    # Стабильный порядок: 9to18 -> edge -> e2e
    return [name for name in EXTRA_ORDER if name in seen]


def _build_plan(profiles: list[str], only: list[str] | None) -> list[str]:
    plan = list(CORE_ORDER)
    # По умолчанию — основные боты; --profiles bots добавляет остальные.
    if "bots" in profiles:
        plan.extend(BOTS_ORDER)
    else:
        plan.extend(DEFAULT_BOTS_ORDER)
    for profile in profiles:
        if profile == "bots":
            continue
        plan.extend(PROFILE_SERVICES[profile])

    seen: set[str] = set()
    ordered: list[str] = []
    for name in plan:
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)

    if only is None:
        return ordered

    unknown = set(only) - KNOWN
    if unknown:
        raise SystemExit(f"Неизвестные сервисы: {', '.join(sorted(unknown))}")

    wanted = set(only)
    for name in only:
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return [name for name in ordered if name in wanted]


def _compose_cmd_for(service: str) -> list[str]:
    # Profiles в docker-compose.yaml сняты: обычный `compose up` поднимает все сервисы.
    return _docker_compose_bin() + ["-f", str(COMPOSE_FILE)]


def _wait_running(service: str, timeout_sec: float) -> bool:
    """Ждём running; для ollama-init — exited (0)."""
    deadline = time.monotonic() + timeout_sec
    base = _compose_cmd_for(service)
    while time.monotonic() < deadline:
        proc = subprocess.run(
            base + ["ps", "-a", "--format", "{{.Service}}\t{{.State}}\t{{.Status}}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            for line in (proc.stdout or "").splitlines():
                parts = line.strip().split("\t")
                if len(parts) < 2:
                    continue
                svc, state = parts[0], parts[1].lower()
                if svc != service:
                    continue
                if state == "running":
                    return True
                if service == "ollama-init" and state == "exited":
                    status = parts[2].lower() if len(parts) > 2 else ""
                    return "(0)" in status or status.startswith("exited (0)")
        time.sleep(2.0)
    return False


def _ensure_edge_net(*, dry_run: bool) -> int:
    print("\n[edge_net] ensure network...", flush=True)
    if dry_run:
        print("$ docker network create edge_net  # if missing")
        return 0
    listed = subprocess.run(
        ["docker", "network", "ls", "--format", "{{.Name}}"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if listed.returncode != 0:
        return listed.returncode
    names = {line.strip() for line in (listed.stdout or "").splitlines()}
    if "edge_net" in names:
        print("Network edge_net already exists.")
        return 0
    return _run(["docker", "network", "create", "edge_net"], dry_run=False)


def _up_stack(
    *,
    compose_file: Path,
    services: list[str] | None,
    flags: UpFlags,
    dry_run: bool,
    env_file: Path | None = None,
    cwd: Path | None = None,
) -> int:
    if not compose_file.is_file():
        print(f"FAILED: compose not found: {compose_file}", flush=True)
        return 1
    cmd = _docker_compose_bin() + ["-f", str(compose_file)]
    if env_file is not None:
        if not env_file.is_file():
            print(f"FAILED: env file required: {env_file}", flush=True)
            print("  cp deploy/e2e-tester/.env.example deploy/e2e-tester/.env", flush=True)
            return 1
        cmd.extend(["--env-file", str(env_file)])
    cmd.extend(["up", "-d", *flags.as_args()])
    if services:
        cmd.extend(services)
    return _run(cmd, dry_run=dry_run, cwd=cwd)


def _run_extra(name: str, cfg: RunConfig) -> int:
    if name == "9to18":
        print("\n[extra] ui-9to18...", flush=True)
        return _up_stack(
            compose_file=UI_9TO18_COMPOSE,
            services=["ui-9to18"],
            flags=cfg.flags,
            dry_run=cfg.dry_run,
            cwd=REPO_ROOT,
        )
    if name == "edge":
        print("\n[extra] ui-edge...", flush=True)
        return _up_stack(
            compose_file=UI_EDGE_COMPOSE,
            services=["ui-edge"],
            flags=cfg.flags,
            dry_run=cfg.dry_run,
            cwd=REPO_ROOT,
        )
    if name == "e2e":
        print("\n[extra] e2e-tester...", flush=True)
        # Sequential: db first, then app (меньше пик + явный порядок)
        code = _up_stack(
            compose_file=E2E_COMPOSE,
            services=["tester-db"],
            flags=cfg.flags,
            dry_run=cfg.dry_run,
            env_file=E2E_ENV,
            cwd=REPO_ROOT,
        )
        if code != 0:
            return code
        if cfg.delay > 0 and not cfg.dry_run:
            print(f"Sleep {cfg.delay:.1f}s...", flush=True)
            time.sleep(cfg.delay)
        return _up_stack(
            compose_file=E2E_COMPOSE,
            services=["tester"],
            flags=cfg.flags,
            dry_run=cfg.dry_run,
            env_file=E2E_ENV,
            cwd=REPO_ROOT,
        )
    raise SystemExit(f"Unknown extra: {name}")


def _prompt_yes(question: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    try:
        answer = input(f"{question} [{suffix}]: ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in ("y", "yes", "д", "да", "1")


def _prompt_csv(question: str, default: str = "") -> list[str]:
    hint = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{hint}: ").strip()
    except EOFError:
        answer = ""
    if not answer:
        answer = default
    return _parse_csv(answer)


def _interactive_config() -> RunConfig:
    print("=== Sequential compose up (interactive) ===\n")
    print("Default plan: core + tg-bot, vk-bot, url-bot, dzen-bot, wp-bot")
    print("Main stack profiles:")
    print(f"  bots: all bots ({', '.join(BOTS_ORDER)})")
    print(f"  ai:   {', '.join(AI_ORDER)}\n")

    profiles = _prompt_csv("Profiles (bots,ai)", "")
    only = _prompt_csv("Only services (empty = default/profiles plan)", "")
    extras = _prompt_csv("Extras after main (9to18,edge,e2e)", "")

    print("\nCompose up flags:")
    flags = UpFlags(
        build=_prompt_yes("--build", False),
        no_deps=_prompt_yes("--no-deps", False),
        force_recreate=_prompt_yes("--force-recreate", False),
        pull_always=_prompt_yes("--pull always", False),
        remove_orphans=_prompt_yes("--remove-orphans", False),
        renew_anon_volumes=_prompt_yes("--renew-anon-volumes", False),
    )

    delay_raw = ""
    try:
        delay_raw = input("Delay between services seconds [3]: ").strip()
    except EOFError:
        delay_raw = ""
    delay = float(delay_raw) if delay_raw else 3.0

    return RunConfig(
        profiles=profiles,
        only=only or None,
        extras=_normalize_extras(extras) if extras else [],
        flags=flags,
        delay=delay,
        wait_health=_prompt_yes("Wait until running after each up?", False),
        continue_on_error=_prompt_yes("Continue on error?", False),
        dry_run=_prompt_yes("Dry-run only?", False),
        skip_main=_prompt_yes("Skip main stack (extras only)?", False),
        ensure_edge_net=True,
    )


def _parse_args(argv: list[str] | None) -> RunConfig:
    parser = argparse.ArgumentParser(
        description="Поднимает сервисы docker compose по одному, с паузой между ними.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --interactive
  %(prog)s --build --force-recreate --no-deps
  %(prog)s --profiles bots --with 9to18,edge
  %(prog)s --skip-main --with e2e --build
  %(prog)s --only gateway,ui --no-deps --force-recreate
        """.strip(),
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Интерактивный выбор профилей, extras и флагов up",
    )
    parser.add_argument(
        "--profiles",
        default="",
        help="Через запятую: bots (все боты), ai. По умолчанию: core + tg/vk/url/dzen/wp-bot",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Только эти сервисы основного compose (через запятую)",
    )
    parser.add_argument(
        "--with",
        dest="extras",
        default="",
        help="Доп. стеки после main: 9to18, edge, e2e (через запятую)",
    )
    parser.add_argument(
        "--skip-main",
        action="store_true",
        help="Не поднимать основной docker-compose.yaml (только --with)",
    )
    parser.add_argument(
        "--no-edge-net",
        action="store_true",
        help="Не создавать edge_net автоматически",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Пауза между сервисами в секундах (default: 3)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="docker compose up --build",
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="docker compose up --no-deps",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="docker compose up --force-recreate",
    )
    parser.add_argument(
        "--pull-always",
        action="store_true",
        help="docker compose up --pull always",
    )
    parser.add_argument(
        "--remove-orphans",
        action="store_true",
        help="docker compose up --remove-orphans",
    )
    parser.add_argument(
        "--renew-anon-volumes",
        action="store_true",
        help="docker compose up --renew-anon-volumes",
    )
    parser.add_argument(
        "--wait-health",
        action="store_true",
        help="После up ждать running (до --wait-timeout сек)",
    )
    parser.add_argument(
        "--wait-timeout",
        type=float,
        default=120.0,
        help="Таймаут ожидания running (default: 120)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Не останавливаться при ошибке одного сервиса",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать команды",
    )
    args = parser.parse_args(argv)

    if args.interactive:
        return _interactive_config()

    profiles = _parse_csv(args.profiles)
    for profile in profiles:
        if profile not in PROFILE_SERVICES:
            raise SystemExit(
                f"Неизвестный профиль: {profile}. Доступны: {', '.join(PROFILE_SERVICES)}"
            )

    extras = _normalize_extras(_parse_csv(args.extras)) if args.extras else []
    only = _parse_csv(args.only) or None

    if args.skip_main and not extras:
        raise SystemExit("--skip-main требует --with 9to18,edge,e2e")

    return RunConfig(
        profiles=profiles,
        only=only,
        extras=extras,
        flags=UpFlags(
            build=args.build,
            no_deps=args.no_deps,
            force_recreate=args.force_recreate,
            pull_always=args.pull_always,
            remove_orphans=args.remove_orphans,
            renew_anon_volumes=args.renew_anon_volumes,
        ),
        delay=args.delay,
        wait_health=args.wait_health,
        wait_timeout=args.wait_timeout,
        continue_on_error=args.continue_on_error,
        dry_run=args.dry_run,
        skip_main=args.skip_main,
        ensure_edge_net=not args.no_edge_net,
    )


def _run_main_stack(cfg: RunConfig, failed: list[str]) -> int:
    plan = _build_plan(cfg.profiles, cfg.only)
    flag_preview = " ".join(cfg.flags.as_args()) or "(none)"
    print(f"Profiles: {cfg.profiles or f'(default bots: {", ".join(DEFAULT_BOTS_ORDER)})'}")
    print(f"Up flags: {flag_preview}")
    print(f"Plan ({len(plan)}): {' -> '.join(plan)}")

    for index, service in enumerate(plan):
        cmd = _compose_cmd_for(service) + ["up", "-d", *cfg.flags.as_args(), service]
        print(f"\n[{index + 1}/{len(plan)}] Starting {service}...", flush=True)
        code = _run(cmd, dry_run=cfg.dry_run)
        if code != 0:
            print(f"FAILED: {service} (exit {code})", flush=True)
            failed.append(service)
            if not cfg.continue_on_error:
                return code
        elif cfg.wait_health and not cfg.dry_run:
            ok = _wait_running(service, cfg.wait_timeout)
            if not ok:
                print(
                    f"WARN: {service} не перешёл в running за {cfg.wait_timeout:.0f}s",
                    flush=True,
                )
                failed.append(service)
                if not cfg.continue_on_error:
                    return 1
            else:
                print(f"OK: {service} running", flush=True)

        if index < len(plan) - 1 and cfg.delay > 0 and not cfg.dry_run:
            print(f"Sleep {cfg.delay:.1f}s...", flush=True)
            time.sleep(cfg.delay)
    return 0


def main(argv: list[str] | None = None) -> int:
    cfg = _parse_args(argv)

    if not COMPOSE_FILE.is_file():
        raise SystemExit(f"Не найден {COMPOSE_FILE}")

    print(f"Repo: {REPO_ROOT}")
    print(f"Compose: {COMPOSE_FILE.name}")

    failed: list[str] = []
    needs_edge_net = bool(cfg.extras) or (
        not cfg.skip_main and {"gateway", "ui"} & set(_build_plan(cfg.profiles, cfg.only))
    )

    if cfg.ensure_edge_net and (needs_edge_net or cfg.extras):
        code = _ensure_edge_net(dry_run=cfg.dry_run)
        if code != 0 and not cfg.continue_on_error:
            return code

    if not cfg.skip_main:
        code = _run_main_stack(cfg, failed)
        if code != 0:
            return code
        if cfg.extras and cfg.delay > 0 and not cfg.dry_run:
            print(f"\nSleep {cfg.delay:.1f}s before extras...", flush=True)
            time.sleep(cfg.delay)

    for index, extra in enumerate(cfg.extras):
        print(f"\n=== Extra [{index + 1}/{len(cfg.extras)}]: {extra} ===", flush=True)
        code = _run_extra(extra, cfg)
        if code != 0:
            print(f"FAILED: extra {extra} (exit {code})", flush=True)
            failed.append(f"extra:{extra}")
            if not cfg.continue_on_error:
                return code
        if index < len(cfg.extras) - 1 and cfg.delay > 0 and not cfg.dry_run:
            print(f"Sleep {cfg.delay:.1f}s...", flush=True)
            time.sleep(cfg.delay)

    print("\n=== Done ===")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        return 1
    print("All requested units started.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
