"""Validate and compress profile photos before storage."""
from __future__ import annotations

import io
from typing import Literal

from fastapi import HTTPException

AllowedKind = Literal["jpeg", "png", "webp"]

MAX_SIDE_PX = 1280
JPEG_QUALITY = 85


def detect_image_kind(data: bytes) -> AllowedKind:
    """MIME via magic bytes (ignore client filename/content-type)."""
    if len(data) >= 3 and data[0:3] == b"\xff\xd8\xff":
        return "jpeg"
    if len(data) >= 8 and data[0:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if (
        len(data) >= 12
        and data[0:4] == b"RIFF"
        and data[8:12] == b"WEBP"
    ):
        return "webp"
    raise HTTPException(
        status_code=400,
        detail="Invalid image: expected JPEG, PNG, or WEBP content",
    )


def process_profile_photo(data: bytes, *, max_side: int = MAX_SIDE_PX) -> bytes:
    """Validate magic bytes, resize, compress to JPEG."""
    detect_image_kind(data)
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Image processing unavailable (Pillow not installed)",
        ) from exc

    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA", "P"):
                rgba = img.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[-1])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            width, height = img.size
            longest = max(width, height)
            if longest > max_side:
                scale = max_side / float(longest)
                img = img.resize(
                    (max(1, int(width * scale)), max(1, int(height * scale))),
                    Image.Resampling.LANCZOS,
                )

            out = io.BytesIO()
            img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            return out.getvalue()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot process image: {exc}") from exc
