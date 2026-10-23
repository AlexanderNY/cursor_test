#!/usr/bin/env python3
"""Import interview-gap Learn series into both learn_seed.json copies."""
from __future__ import annotations

from learn_series_import_lib import import_series, series_dir

SERIES = (
    ("algo", "algo-*.md", ("developer",)),
    ("design", "sd-*.md", ("developer",)),
    ("postgres", "pg-*.md", ("developer", "analyst")),
    ("networks", "net-*.md", ("developer",)),
    ("security", "sec-*.md", ("developer",)),
    ("behavior", "beh-*.md", ("developer", "analyst", "devops", "tester", "product_owner")),
    ("observe", "obs-*.md", ("developer", "devops")),
    ("java-core", "jc-*.md", ("developer",)),
    ("frontend", "fe-*.md", ("developer",)),
    ("devops", "ops-*.md", ("devops", "developer")),
)


def main() -> None:
    for name, pattern, profiles in SERIES:
        import_series(
            series_dir=series_dir(name),
            glob_pattern=pattern,
            required_profiles=profiles,
        )


if __name__ == "__main__":
    main()
