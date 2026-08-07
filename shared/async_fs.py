"""Async обёртки над sync disk I/O через asyncio.to_thread."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


def _write_bytes_sync(path: PathLike, data: bytes) -> None:
    Path(path).write_bytes(data)


def _read_bytes_sync(path: PathLike) -> bytes:
    return Path(path).read_bytes()


def _write_temp_bytes_sync(data: bytes, suffix: str = "") -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        f.write(data)
        return f.name
    finally:
        f.close()


def _unlink_quiet_sync(path: PathLike) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _makedirs_sync(path: PathLike, exist_ok: bool = True) -> None:
    Path(path).mkdir(parents=True, exist_ok=exist_ok)


def _rename_sync(src: PathLike, dst: PathLike) -> None:
    os.rename(src, dst)


async def write_bytes(path: PathLike, data: bytes) -> None:
    await asyncio.to_thread(_write_bytes_sync, path, data)


async def read_bytes(path: PathLike) -> bytes:
    return await asyncio.to_thread(_read_bytes_sync, path)


async def write_temp_bytes(data: bytes, suffix: str = "") -> str:
    """Пишет bytes во временный файл (delete=False). Возвращает путь."""
    return await asyncio.to_thread(_write_temp_bytes_sync, data, suffix)


async def unlink_quiet(path: PathLike) -> None:
    await asyncio.to_thread(_unlink_quiet_sync, path)


async def makedirs(path: PathLike, exist_ok: bool = True) -> None:
    await asyncio.to_thread(_makedirs_sync, path, exist_ok)


async def rename(src: PathLike, dst: PathLike) -> None:
    await asyncio.to_thread(_rename_sync, src, dst)
