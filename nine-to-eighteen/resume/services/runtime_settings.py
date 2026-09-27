"""Runtime настройки resume-сервиса (site_settings + in-memory cache).

Секреты (JWT, DATABASE_URL, S3 keys) остаются только в env — в админке не правятся.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

SETTINGS_KEY = "site_9to18_resume"
CACHE_TTL_SEC = 5.0

DEFAULT_SETTINGS: dict[str, Any] = {
    "rateLimits": {
        "ai": {"requests": 8, "windowSec": 60},
        "generate": {"requests": 20, "windowSec": 60},
        "preview": {"requests": 60, "windowSec": 60},
        "export": {"requests": 10, "windowSec": 60},
    },
    "ai": {
        "enabled": True,
        "serviceUrl": "",
        "model": "",
        "timeoutSec": 60,
    },
    "strength": {
        "photoPoints": 10,
        "aboutPoints": 15,
        "aboutMinLen": 40,
        "learnPointsPerModule": 20,
        "maxScore": 100,
    },
    "features": {
        "exportEnabled": True,
        "aiImproveAbout": True,
        "aiSkillGap": True,
        "aiCoverLetter": True,
        "aiMatchScore": True,
        "aiMockInterview": True,
    },
}

_cache: Optional[dict[str, Any]] = None
_cache_at: float = 0.0


def default_settings() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_SETTINGS)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in overlay.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
        ):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def validate_and_normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Merge with defaults and clamp numeric fields."""
    merged = _deep_merge(DEFAULT_SETTINGS, raw if isinstance(raw, dict) else {})

    for bucket, cfg in merged["rateLimits"].items():
        if not isinstance(cfg, dict):
            continue
        defaults_bucket = DEFAULT_SETTINGS["rateLimits"].get(bucket) or {
            "requests": 30,
            "windowSec": 60,
        }
        try:
            req = int(cfg["requests"]) if "requests" in cfg else int(defaults_bucket["requests"])
        except (TypeError, ValueError):
            req = int(defaults_bucket["requests"])
        try:
            win = int(cfg["windowSec"]) if "windowSec" in cfg else int(defaults_bucket["windowSec"])
        except (TypeError, ValueError):
            win = int(defaults_bucket["windowSec"])
        cfg["requests"] = max(1, min(10_000, req))
        cfg["windowSec"] = max(1, min(3600, win))

    ai = merged["ai"]
    ai["enabled"] = bool(ai.get("enabled", True))
    ai["serviceUrl"] = str(ai.get("serviceUrl") or "").strip()[:500]
    ai["model"] = str(ai.get("model") or "").strip()[:120]
    try:
        ai["timeoutSec"] = max(5, min(300, int(ai.get("timeoutSec") or 60)))
    except (TypeError, ValueError):
        ai["timeoutSec"] = 60

    strength = merged["strength"]
    for key, lo, hi in (
        ("photoPoints", 0, 100),
        ("aboutPoints", 0, 100),
        ("aboutMinLen", 1, 500),
        ("learnPointsPerModule", 0, 100),
        ("maxScore", 1, 100),
    ):
        try:
            strength[key] = max(lo, min(hi, int(strength.get(key))))
        except (TypeError, ValueError):
            strength[key] = DEFAULT_SETTINGS["strength"][key]

    features = merged["features"]
    for key in list(DEFAULT_SETTINGS["features"].keys()):
        features[key] = bool(features.get(key, True))

    return merged


def apply_process_env(settings_doc: dict[str, Any]) -> None:
    """Push AI knobs into process env for shared.ai_client (current worker only)."""
    ai = settings_doc.get("ai") or {}
    if "enabled" in ai:
        os.environ["AI_ENABLED"] = "true" if ai.get("enabled") else "false"
    url = str(ai.get("serviceUrl") or "").strip()
    if url:
        os.environ["AI_SERVICE_URL"] = url
    model = str(ai.get("model") or "").strip()
    if model:
        os.environ["AI_MODEL"] = model
    timeout = ai.get("timeoutSec")
    if timeout is not None:
        os.environ["AI_TIMEOUT_SEC"] = str(int(timeout))


def invalidate_cache() -> None:
    global _cache, _cache_at
    _cache = None
    _cache_at = 0.0


async def load_settings(*, force: bool = False) -> dict[str, Any]:
    global _cache, _cache_at
    now = time.monotonic()
    if (
        not force
        and _cache is not None
        and (now - _cache_at) < CACHE_TTL_SEC
    ):
        return copy.deepcopy(_cache)

    from database import get_db_connection, release_db_connection

    raw: Any = None
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT value FROM site_settings WHERE key = %s",
                (SETTINGS_KEY,),
            )
            row = await cur.fetchone()
            if row and row[0] is not None:
                raw = row[0]
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except json.JSONDecodeError:
                        raw = {}
    except Exception as exc:
        logger.warning("resume settings load failed, using defaults: %s", exc)
        raw = None
    finally:
        await release_db_connection(conn)

    doc = validate_and_normalize(raw if isinstance(raw, dict) else {})
    apply_process_env(doc)
    _cache = doc
    _cache_at = now
    return copy.deepcopy(doc)


async def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    doc = validate_and_normalize(payload)
    from database import get_db_connection, release_db_connection

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_settings (key, value, updated_at)
                VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (SETTINGS_KEY, json.dumps(doc, ensure_ascii=False)),
            )
    finally:
        await release_db_connection(conn)

    apply_process_env(doc)
    invalidate_cache()
    _cache_at = time.monotonic()
    global _cache
    _cache = doc
    return copy.deepcopy(doc)


def rate_limit_override(bucket: str) -> Optional[tuple[int, int]]:
    """Sync peek at cached limits (None → env/defaults)."""
    if _cache is None:
        return None
    cfg = (_cache.get("rateLimits") or {}).get(bucket)
    if not isinstance(cfg, dict):
        return None
    try:
        return int(cfg["requests"]), int(cfg["windowSec"])
    except (KeyError, TypeError, ValueError):
        return None


def strength_override() -> dict[str, int]:
    if _cache is None:
        return copy.deepcopy(DEFAULT_SETTINGS["strength"])
    return copy.deepcopy(_cache.get("strength") or DEFAULT_SETTINGS["strength"])


def feature_enabled(name: str, default: bool = True) -> bool:
    if _cache is None:
        return bool(DEFAULT_SETTINGS["features"].get(name, default))
    return bool((_cache.get("features") or {}).get(name, default))


def public_settings_view(doc: dict[str, Any]) -> dict[str, Any]:
    """API response: camelCase already in doc; mark env-only secrets."""
    return {
        "settings": doc,
        "envOnly": [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
            "S3_ENDPOINT_URL",
            "S3_BUCKET",
        ],
        "defaults": default_settings(),
    }
