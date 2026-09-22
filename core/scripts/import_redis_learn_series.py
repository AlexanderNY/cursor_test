#!/usr/bin/env python3
"""Merge Learn Redis series .md into learn_seed.json."""
from __future__ import annotations

from pathlib import Path

from learn_series_import_lib import import_series

ROOT = Path(__file__).resolve().parents[2]
SERIES_DIR = ROOT / "deploy" / "ui-9to18" / "src" / "data" / "learn" / "redis"


def main() -> None:
    import_series(
        series_dir=SERIES_DIR,
        glob_pattern="rd*.md",
        required_profiles=("developer", "analyst"),
    )


if __name__ == "__main__":
    main()
