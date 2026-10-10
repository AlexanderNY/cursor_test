"""Unit tests for resume storage helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]

# Minimal stubs so storage_client can import config without env.
_config = type(sys)("config")
_config.settings = type(
    "Settings",
    (),
    {
        "S3_ENDPOINT_URL": "",
        "S3_ACCESS_KEY": "",
        "S3_SECRET_KEY": "",
        "S3_BUCKET": "",
        "S3_REGION": "us-east-1",
        "S3_PUBLIC_ENDPOINT_URL": "",
        "S3_USE_SSL": False,
    },
)()
sys.modules["config"] = _config

_SPEC = importlib.util.spec_from_file_location(
    "storage_client",
    API_DIR / "storage_client.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["storage_client"] = _mod
_SPEC.loader.exec_module(_mod)

content_disposition_attachment = _mod.content_disposition_attachment
safe_filename = _mod.safe_filename
ResumeStorage = _mod.ResumeStorage
LOCAL_EXPORT_ROOT = _mod.LOCAL_EXPORT_ROOT


def test_content_disposition_ascii_only():
    value = content_disposition_attachment("resume.pdf")
    assert value == 'attachment; filename="resume.pdf"; filename*=UTF-8\'\'resume.pdf'
    value.encode("latin-1")


def test_content_disposition_cyrillic_is_latin1_safe():
    file_name = safe_filename("Backend-разработчик", "pdf")
    value = content_disposition_attachment(file_name)
    value.encode("latin-1")  # must not raise
    assert "filename*=UTF-8''" in value
    assert "Backend" in value
    assert ".pdf" in value


@pytest.mark.asyncio
async def test_delete_ref_local(tmp_path, monkeypatch):
    monkeypatch.setattr(_mod, "LOCAL_EXPORT_ROOT", tmp_path)
    storage = ResumeStorage()
    storage._s3 = None
    key = "1/rid/test.bin"
    path = tmp_path / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"hello")
    assert await storage.delete_ref(f"local:{key}") is True
    assert not path.exists()
    assert await storage.delete_ref(f"local:{key}") is False


@pytest.mark.asyncio
async def test_delete_ref_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(_mod, "LOCAL_EXPORT_ROOT", tmp_path)
    storage = ResumeStorage()
    storage._s3 = None
    assert await storage.delete_ref("local:../secret") is False
