"""Каталог AI-действий и безопасный process (шаблоны, не свободный system-prompt)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Literal, Optional

logger = logging.getLogger(__name__)

ActionId = Literal["summarize", "categorize", "rewrite", "reply_draft"]

MAX_SOURCE_CHARS = 8000
MAX_NOTE_CHARS = 300
MAX_TONE_CHARS = 80
DEFAULT_CATEGORIES = ["новости", "реклама", "технологии", "финансы", "другое"]
MAX_CATEGORIES = 20
CATEGORY_MAX_LEN = 40

_INJECTION_PATTERNS = (
    re.compile(r"(?i)\bsystem\s*:"),
    re.compile(r"(?i)\bassistant\s*:"),
    re.compile(r"<\|im_start\|>"),
    re.compile(r"<\|im_end\|>"),
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions"),
    re.compile(r"(?i)забыть\s+(все\s+)?(предыдущие\s+)?инструкции"),
)

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

AI_ACTIONS: list[dict[str, Any]] = [
    {
        "id": "summarize",
        "title": "Саммари",
        "description": "Сократи текст и выдели суть",
        "params": ["max_len", "note"],
    },
    {
        "id": "categorize",
        "title": "Категория",
        "description": "Отнеси сообщение к одной из категорий",
        "params": ["categories", "note"],
    },
    {
        "id": "rewrite",
        "title": "Переписать",
        "description": "Перепиши текст, сохранив смысл",
        "params": ["tone", "network", "note"],
    },
    {
        "id": "reply_draft",
        "title": "Черновик ответа",
        "description": "Короткий ответ на входящее сообщение",
        "params": ["tone", "network", "note"],
    },
]

_ACTION_IDS = {a["id"] for a in AI_ACTIONS}


class AiAssistError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def list_actions() -> list[dict[str, Any]]:
    return [dict(a) for a in AI_ACTIONS]


def _strip_control(value: str) -> str:
    return _CONTROL_CHARS_RE.sub("", value)


def sanitize_note(raw: Optional[str]) -> str:
    if not raw:
        return ""
    text = _strip_control(str(raw)).strip()
    if len(text) > MAX_NOTE_CHARS:
        text = text[:MAX_NOTE_CHARS]
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("", text)
    return text.strip()


def sanitize_tone(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    text = _strip_control(str(raw)).strip()
    if len(text) > MAX_TONE_CHARS:
        text = text[:MAX_TONE_CHARS]
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("", text)
    text = text.strip()
    return text or None


def sanitize_source_text(raw: str) -> str:
    text = _strip_control(str(raw or "")).strip()
    if not text:
        raise AiAssistError("Text is required")
    if len(text) > MAX_SOURCE_CHARS:
        text = text[:MAX_SOURCE_CHARS]
    return text


def sanitize_categories(raw: Any) -> list[str]:
    if raw is None:
        return list(DEFAULT_CATEGORIES)
    if not isinstance(raw, list):
        raise AiAssistError("categories must be a list of strings")
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw[:MAX_CATEGORIES]:
        cat = _strip_control(str(item)).strip()[:CATEGORY_MAX_LEN]
        if not cat:
            continue
        key = cat.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(cat)
    if not cleaned:
        return list(DEFAULT_CATEGORIES)
    return cleaned


def _normalize_network(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    net = str(raw).strip().lower()
    aliases = {
        "telegram": "tg",
        "vkontakte": "vk",
        "twitter": "tw",
        "x": "tw",
        "wordpress": "wp",
        "insta": "instagram",
        "ig": "instagram",
        "zen": "dzen",
    }
    net = aliases.get(net, net)
    if net in ("tg", "vk", "tw", "threads", "instagram", "dzen", "wp"):
        return net
    return None


def _network_prompt_hint(network: Optional[str]) -> Optional[str]:
    if network == "tg":
        return "для Telegram (можно HTML, spoiler)"
    if network == "vk":
        return "для ВКонтакте (plain text без HTML)"
    if network == "tw":
        return "для Twitter/X (коротко, без HTML)"
    if network == "threads":
        return "для Threads (короткий plain text)"
    if network == "instagram":
        return "для Instagram (caption, plain text)"
    if network == "dzen":
        return "для Яндекс Дзен"
    if network == "wp":
        return "для WordPress (можно HTML)"
    return None


async def _insert_task(
    user_id: int,
    task_type: str,
    payload: dict[str, Any],
) -> int:
    from database import get_db_connection, release_db_connection

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO ai_tasks (user_id, task_type, status, payload)
                VALUES (%s, %s, 'pending', %s::jsonb)
                RETURNING id
                """,
                (user_id, task_type, json.dumps(payload, ensure_ascii=False)),
            )
            row = await cur.fetchone()
            return int(row[0])
    finally:
        await release_db_connection(conn)


async def _finish_task(
    task_id: int,
    *,
    status: str,
    result: Optional[dict[str, Any]] = None,
) -> None:
    from database import get_db_connection, release_db_connection

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE ai_tasks
                SET status = %s,
                    result = %s::jsonb,
                    processed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    status,
                    json.dumps(result, ensure_ascii=False) if result is not None else None,
                    task_id,
                ),
            )
    finally:
        await release_db_connection(conn)


async def process(
    user_id: int,
    action: str,
    text: str,
    params: Optional[dict[str, Any]] = None,
    *,
    source: Optional[str] = None,
    source_id: Optional[int] = None,
    brand_id: Optional[int] = None,
) -> dict[str, Any]:
    """Выполняет шаблонное AI-действие и сохраняет результат в ai_tasks."""
    if action not in _ACTION_IDS:
        raise AiAssistError(f"Unknown action: {action}")

    params = params or {}
    source_text = sanitize_source_text(text)
    note = sanitize_note(
        params.get("note") if isinstance(params.get("note"), str) else params.get("instruction")
    )
    tone = sanitize_tone(params.get("tone") if params.get("tone") is not None else None)
    network = _normalize_network(params.get("network"))

    # Brand TOV fills tone when the user did not pass an explicit one
    if not tone and brand_id is not None:
        from services.smm_service import compose_brand_voice, smm_service

        brand = await smm_service.get_brand(user_id, int(brand_id))
        tone = compose_brand_voice(brand)

    max_len_raw = params.get("max_len", 500)
    try:
        max_len = int(max_len_raw)
    except (TypeError, ValueError):
        max_len = 500
    max_len = max(50, min(max_len, 2000))

    categories = sanitize_categories(params.get("categories")) if action == "categorize" else None

    if source is not None and source not in ("inbox", "post"):
        raise AiAssistError("source must be inbox or post")

    payload = {
        "action": action,
        "text_preview": source_text[:200],
        "text_len": len(source_text),
        "note": note or None,
        "tone": tone,
        "network": network,
        "max_len": max_len if action == "summarize" else None,
        "categories": categories,
        "source": source,
        "source_id": source_id,
        "brand_id": brand_id,
    }

    task_id = await _insert_task(user_id, action, payload)
    model = os.getenv("AI_MODEL", "qwen2.5:1.5b")
    started = time.perf_counter()

    try:
        from shared import ai_client

        if not await ai_client.is_enabled():
            raise AiAssistError("AI is disabled", status_code=503)

        status = await ai_client.get_status()
        if not status.get("ready"):
            msg = {
                "circuit_open": "AI temporarily unavailable (circuit open)",
                "unavailable": "AI service unavailable (Ollama not running)",
            }.get(str(status.get("status")), "AI is not ready")
            raise AiAssistError(msg, status_code=503)

        result: dict[str, Any]
        if action == "summarize":
            if note:
                from shared.ai_client import SUMMARIZE_SYSTEM

                user_prompt = (
                    f"Сократи текст до ~{max_len} символов, сохрани ключевые факты."
                    f"\nУточнение: {note}\n\n{source_text}"
                )
                summary = await ai_client.complete(
                    user_prompt, system=SUMMARIZE_SYSTEM, max_tokens=512
                )
                summary = summary[:max_len] if len(summary) > max_len else summary
            else:
                summary = await ai_client.summarize(source_text, max_len)
            result = {"text": summary}

        elif action == "categorize":
            assert categories is not None
            classified = await ai_client.classify(source_text, categories, note=note or None)
            result = {
                "category": classified.get("category"),
                "confidence": classified.get("confidence", 0.0),
                "text": classified.get("category"),
                "meta": {"model": classified.get("model", model)},
            }

        elif action == "rewrite":
            if note:
                from shared.ai_client import REWRITE_SYSTEM

                parts = ["Перепиши следующий текст"]
                if tone:
                    parts.append(f"в тоне «{tone}»")
                hint = _network_prompt_hint(network)
                if hint:
                    parts.append(hint)
                parts.append(f"Уточнение: {note}")
                user_prompt = f"{' '.join(parts)}:\n\n{source_text}"
                rewritten = await ai_client.complete(
                    user_prompt, system=REWRITE_SYSTEM, max_tokens=1024
                )
            else:
                rewritten = await ai_client.rewrite(source_text, tone=tone, network=network)
            result = {"text": rewritten}

        elif action == "reply_draft":
            drafted = await ai_client.reply_draft(
                source_text,
                tone=tone or "живой, неформальный, короткий",
                note=note or None,
                network=network,
            )
            result = {"text": drafted}

        else:
            raise AiAssistError(f"Unknown action: {action}")

        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        out = {
            "task_id": task_id,
            "action": action,
            "result": result,
            "model": model,
            "latency_ms": latency_ms,
        }
        await _finish_task(
            task_id, status="done", result={**result, "model": model, "latency_ms": latency_ms}
        )
        return out

    except AiAssistError as exc:
        await _finish_task(task_id, status="error", result={"error": exc.message})
        raise
    except Exception as exc:
        logger.warning("AI assist process failed: %s", exc)
        await _finish_task(task_id, status="error", result={"error": str(exc)})
        raise AiAssistError(f"AI request failed: {exc}", status_code=502) from exc
