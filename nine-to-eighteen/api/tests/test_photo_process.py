"""Tests for profile photo MIME check and JPEG compression."""
from __future__ import annotations

import io
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

API_DIR = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "photo_process",
    API_DIR / "services" / "photo_process.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["photo_process"] = _mod
_SPEC.loader.exec_module(_mod)

detect_image_kind = _mod.detect_image_kind
process_profile_photo = _mod.process_profile_photo


def _tiny_png() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (32, 24), color=(20, 40, 60)).save(buf, format="PNG")
    return buf.getvalue()


def test_detect_rejects_non_image():
    with pytest.raises(HTTPException) as exc:
        detect_image_kind(b"not-an-image")
    assert exc.value.status_code == 400


def test_detect_png_magic():
    assert detect_image_kind(_tiny_png()) == "png"


def test_process_outputs_jpeg_smaller_or_valid():
    raw = _tiny_png()
    out = process_profile_photo(raw)
    assert out[:3] == b"\xff\xd8\xff"
    assert detect_image_kind(out) == "jpeg"


def test_extension_lie_still_ok_if_magic_valid():
    # Filename might say .jpg but body is PNG — magic wins.
    out = process_profile_photo(_tiny_png())
    assert out.startswith(b"\xff\xd8\xff")


def test_resize_large_image():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (2000, 1500), color=(1, 2, 3)).save(buf, format="JPEG", quality=95)
    out = process_profile_photo(buf.getvalue(), max_side=1280)
    img = Image.open(io.BytesIO(out))
    assert max(img.size) <= 1280
