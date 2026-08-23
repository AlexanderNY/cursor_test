from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    raw = (settings.TESTER_SECRET_KEY or "").strip()
    if not raw:
        raise RuntimeError("TESTER_SECRET_KEY is not set")
    try:
        # Accept a real Fernet key
        return Fernet(raw.encode() if isinstance(raw, str) else raw)
    except (ValueError, Exception):
        # Derive a stable Fernet key from an arbitrary secret string
        digest = hashlib.sha256(raw.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)


def encrypt_payload(data: dict[str, Any]) -> str:
    token = _fernet().encrypt(json.dumps(data).encode("utf-8"))
    return token.decode("utf-8")


def decrypt_payload(ciphertext: str) -> dict[str, Any]:
    try:
        plain = _fernet().decrypt(ciphertext.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("failed to decrypt credentials payload") from exc
    return json.loads(plain.decode("utf-8"))
