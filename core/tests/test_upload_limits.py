"""Tests for bounded upload reads."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, UploadFile

from upload_limits import enforce_upload_count, read_upload_limited


class _FakeUpload(UploadFile):
    def __init__(self, data: bytes, *, filename: str = "x.bin", size=None):
        super().__init__(file=io.BytesIO(data), filename=filename, size=size)


@pytest.mark.asyncio
async def test_read_upload_within_limit():
    data = b"hello" * 100
    upload = _FakeUpload(data)
    out = await read_upload_limited(upload, max_bytes=1024, label="Image")
    assert out == data


@pytest.mark.asyncio
async def test_read_upload_rejects_oversize_stream():
    data = b"x" * 2048
    upload = _FakeUpload(data)
    with pytest.raises(HTTPException) as exc:
        await read_upload_limited(upload, max_bytes=1024, label="Image")
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_read_upload_rejects_declared_size():
    upload = _FakeUpload(b"tiny", size=10_000_000)
    with pytest.raises(HTTPException) as exc:
        await read_upload_limited(upload, max_bytes=1024, label="Image")
    assert exc.value.status_code == 413


def test_enforce_upload_count():
    files = [AsyncMock(filename="a.jpg") for _ in range(3)]
    enforce_upload_count(files, max_files=5)
    with pytest.raises(HTTPException) as exc:
        enforce_upload_count(files, max_files=2)
    assert exc.value.status_code == 413
