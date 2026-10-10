#!/usr/bin/env python3
"""Merge Learn Product series .md into learn_seed.json."""
from __future__ import annotations

from learn_series_import_lib import import_series, series_dir


def main() -> None:
    import_series(
        series_dir=series_dir("product"),
        glob_pattern="pm*.md",
        required_profiles=("product_owner",),
    )


if __name__ == "__main__":
    main()
