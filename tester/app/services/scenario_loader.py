from __future__ import annotations

import ast
import json
from typing import Any

import yaml

FORBIDDEN_MODULES = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "socket",
        "pathlib",
        "shutil",
        "ctypes",
        "importlib",
        "builtins",
        "pickle",
        "http",
        "urllib",
        "requests",
        "aiohttp",
        "httpx",
    }
)


def parse_scenario_document(source: str, fmt: str) -> dict[str, Any]:
    if fmt == "yaml":
        data = yaml.safe_load(source)
    elif fmt == "json":
        data = json.loads(source)
    else:
        raise ValueError(f"cannot parse structured scenario for format={fmt}")
    if not isinstance(data, dict):
        raise ValueError("scenario root must be a mapping")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("scenario must include a non-empty steps list")
    return data


def validate_playwright_script(source: str) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"invalid Python script: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_MODULES:
                    raise ValueError(f"forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN_MODULES:
                    raise ValueError(f"forbidden import: {node.module}")
        elif isinstance(node, (ast.Call,)):
            # block __import__ and eval/exec
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__", "open"}:
                raise ValueError(f"forbidden call: {node.func.id}")
