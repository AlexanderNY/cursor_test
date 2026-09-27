"""Unit tests for resume storage helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]

# Minimal stubs so storage_client can import config without env.
_config = type(sys)("config")
_config.settings = type(
    "Settings",
    (),
    {
        "s3_endpoint": "",
        "s3_access_key": "",
        "s3_secret_key": "",
        "s3_bucket": "",
        "s3_region": "us-east-1",
        "s3_public_endpoint": "",
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
