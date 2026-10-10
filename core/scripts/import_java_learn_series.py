#!/usr/bin/env python3
"""Merge Learn Java series .md into learn_seed.json."""
from __future__ import annotations

from learn_series_import_lib import import_series, series_dir


def main() -> None:
    import_series(
        series_dir=series_dir("java"),
        glob_pattern="jv*.md",
        required_profiles=("developer",),
    )


if __name__ == "__main__":
    main()
