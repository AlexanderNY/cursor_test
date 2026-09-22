"""Minimal async filesystem helpers (no shared package dependency)."""
from __future__ import annotations

import asyncio
from pathlib import Path


async def makedirs(path: Path | str) -> None:
    target = Path(path)
    await asyncio.to_thread(target.mkdir, parents=True, exist_ok=True)


async def write_bytes(path: Path | str, data: bytes) -> None:
    target = Path(path)
    await asyncio.to_thread(target.write_bytes, data)
