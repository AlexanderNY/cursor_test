"""Tests for shared.async_fs."""

from pathlib import Path

import pytest

from shared import async_fs


@pytest.mark.asyncio
async def test_write_read_unlink_roundtrip(tmp_path: Path):
    target = tmp_path / "sample.bin"
    payload = b"hello-async-fs"
    await async_fs.write_bytes(target, payload)
    assert await async_fs.read_bytes(target) == payload
    await async_fs.unlink_quiet(target)
    assert not target.exists()


@pytest.mark.asyncio
async def test_write_temp_bytes_and_unlink():
    path = await async_fs.write_temp_bytes(b"temp-data", suffix=".jpg")
    assert Path(path).is_file()
    assert Path(path).read_bytes() == b"temp-data"
    await async_fs.unlink_quiet(path)
    assert not Path(path).exists()


@pytest.mark.asyncio
async def test_makedirs_and_rename(tmp_path: Path):
    nested = tmp_path / "a" / "b"
    await async_fs.makedirs(nested)
    assert nested.is_dir()
    src = nested / "src.txt"
    dst = nested / "dst.txt"
    await async_fs.write_bytes(src, b"x")
    await async_fs.rename(src, dst)
    assert dst.is_file()
    assert not src.exists()
