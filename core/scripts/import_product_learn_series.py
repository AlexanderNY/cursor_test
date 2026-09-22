#!/usr/bin/env python3
"""Merge Learn Product series .md into learn_seed.json."""
from __future__ import annotations

from pathlib import Path

from learn_series_import_lib import import_series

ROOT = Path(__file__).resolve().parents[2]
SERIES_DIR = ROOT / "deploy" / "ui-9to18" / "src" / "data" / "learn" / "product"


def main() -> None:
    import_series(
        series_dir=SERIES_DIR,
        glob_pattern="pm*.md",
        required_profiles=("product_owner",),
    )


if __name__ == "__main__":
    main()
