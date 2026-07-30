"""Единый AI-клиент (OpenAI-compatible API) с circuit breaker и runtime-флагом."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import httpx

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = (
    "Ты помощник для сокращения текстов. Сохраняй ключевые факты, имена и цифры. "
    "Отвечай только сокращённым текстом без пояснений."
)
CLASSIFY_SYSTEM = "Ты классификатор сообщений. Отвечай только валидным JSON."
ENRICH_SYSTEM = "Ты аналитик сообщений. Отвечай только валидным JSON."


@dataclass
class SentimentResult:
    sentiment: Literal["positive", "negative", "neutral"]
    score: float = 0.0


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_sec: float = 60.0
    failure_count: int = 0
    opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at >= self.recovery_timeout_sec:
            self.opened_at = None
            self.failure_count = 0
            return False
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time.monotonic()
            logger.warning("AI circuit breaker opened after %d failures", self.failure_count)


@dataclass
class AIClientConfig:
    service_url: str = field(default_factory=lambda: os.getenv("AI_SERVICE_URL", "http://ollama:11434"))
    model: str = field(default_factory=lambda: os.getenv("AI_MODEL", "qwen2.5:3b"))
    timeout_sec: float = field(default_factory=lambda: float(os.getenv("AI_TIMEOUT_SEC", "60")))
    realtime_timeout_sec: float = field(default_factory=lambda: float(os.getenv("AI_REALTIME_TIMEOUT_SEC", "15")))
    max_retries: int = 2
    settings_url: str = field(
        default_factory=lambda: os.getenv(
            "AI_SETTINGS_URL",
            f"{os.getenv('CORE_SERVICE_URL', 'http://core:8002').rstrip('/')}/internal/ai-enabled",
        )
    )
    settings_cache_ttl_sec: float = field(
        default_factory=lambda: float(os.getenv("AI_SETTINGS_CACHE_TTL_SEC", "5"))
    )


_circuit = CircuitBreaker()
_config = AIClientConfig()
_cached_enabled: Optional[bool] = None
_cached_enabled_at: float = 0.0


def _env_ai_enabled() -> bool:
    return os.getenv("AI_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")


async def is_enabled() -> bool:
    """True, если вызовы к Ollama разрешены (env + runtime-флаг из core)."""
    global _cached_enabled, _cached_enabled_at

    if not _env_ai_enabled():
        return False

    now = time.monotonic()
    if (
        _cached_enabled is not None
        and (now - _cached_enabled_at) < _config.settings_cache_ttl_sec
    ):
        return _cached_enabled

    enabled = True
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(_config.settings_url)
            if response.status_code == 200:
                data = response.json()
                enabled = bool(data.get("enabled", True))
    except Exception as exc:
        logger.debug("AI settings poll failed, assuming enabled: %s", exc)
        enabled = True

    _cached_enabled = enabled
    _cached_enabled_at = now
    return enabled


def invalidate_enabled_cache() -> None:
    global _cached_enabled, _cached_enabled_at
    _cached_enabled = None
    _cached_enabled_at = 0.0


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


async def _chat_completion(
    prompt: str,
    system: str,
    max_tokens: int,
    timeout_sec: Optional[float] = None,
) -> str:
    if not await is_enabled():
        raise RuntimeError("AI is disabled")

    if _circuit.is_open():
        raise RuntimeError("AI circuit breaker is open")

    timeout = timeout_sec or _config.timeout_sec
    url = f"{_config.service_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": _config.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    last_error: Optional[Exception] = None
    for attempt in range(_config.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                _circuit.record_success()
                return str(content).strip()
        except Exception as exc:
            last_error = exc
            logger.warning("AI request failed (attempt %d): %s", attempt + 1, exc)
            if attempt < _config.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

    _circuit.record_failure()
    raise RuntimeError(f"AI request failed: {last_error}")


async def complete(prompt: str, system: str = "", max_tokens: int = 512) -> str:
    return await _chat_completion(prompt, system or "You are a helpful assistant.", max_tokens)


async def summarize(text: str, max_length: int) -> str:
    if not text:
        return text
    prompt = f"Сократи текст до ~{max_length} символов, сохрани ключевые факты:\n\n{text}"
    try:
        result = await _chat_completion(prompt, SUMMARIZE_SYSTEM, max_tokens=512)
        return result[:max_length] if len(result) > max_length else result
    except Exception as exc:
        logger.warning("Summarize fallback: %s", exc)
        return text[:max_length] + ("..." if len(text) > max_length else "")


async def classify(text: str, categories: list[str]) -> dict[str, Any]:
    if not text or not categories:
        return {"category": categories[0] if categories else "другое", "confidence": 0.0}
    cats = ", ".join(categories)
    prompt = (
        f'Классифицируй сообщение в одну из категорий: {cats}.\n'
        f'Ответь JSON: {{"category": "...", "confidence": 0.0-1.0}}\n\n'
        f"Сообщение: {text[:3000]}"
    )
    try:
        raw = await _chat_completion(prompt, CLASSIFY_SYSTEM, max_tokens=128)
        data = _extract_json(raw)
        category = str(data.get("category", "другое"))
        if category not in categories:
            category = "другое" if "другое" in categories else categories[-1]
        confidence = float(data.get("confidence", 0.5))
        return {"category": category, "confidence": max(0.0, min(1.0, confidence)), "model": _config.model}
    except Exception as exc:
        logger.warning("Classify fallback: %s", exc)
        return {"category": "другое" if "другое" in categories else categories[0], "confidence": 0.0}


async def sentiment(text: str) -> SentimentResult:
    if not text:
        return SentimentResult(sentiment="neutral", score=0.0)
    prompt = (
        'Определи тональность сообщения. Ответь JSON: '
        '{"sentiment": "positive|negative|neutral", "score": -1.0..1.0}\n\n'
        f"Сообщение: {text[:3000]}"
    )
    try:
        raw = await _chat_completion(
            prompt,
            ENRICH_SYSTEM,
            max_tokens=64,
            timeout_sec=_config.realtime_timeout_sec,
        )
        data = _extract_json(raw)
        label = str(data.get("sentiment", "neutral"))
        if label not in ("positive", "negative", "neutral"):
            label = "neutral"
        score = float(data.get("score", 0.0))
        return SentimentResult(sentiment=label, score=max(-1.0, min(1.0, score)))
    except Exception as exc:
        logger.warning("Sentiment fallback: %s", exc)
        return SentimentResult(sentiment="neutral", score=0.0)


async def enrich(text: str, categories: list[str]) -> dict[str, Any]:
    if not text:
        return {
            "category": categories[0] if categories else "другое",
            "confidence": 0.0,
            "sentiment": "neutral",
            "score": 0.0,
            "model": _config.model,
        }
    cats = ", ".join(categories)
    prompt = (
        f"Проанализируй сообщение. Категории: {cats}.\n"
        'Ответь JSON: {"category": "...", "confidence": 0.0-1.0, '
        '"sentiment": "positive|negative|neutral", "score": -1.0..1.0}\n\n'
        f"Сообщение: {text[:3000]}"
    )
    try:
        raw = await _chat_completion(prompt, ENRICH_SYSTEM, max_tokens=128)
        data = _extract_json(raw)
        category = str(data.get("category", "другое"))
        if category not in categories:
            category = "другое" if "другое" in categories else categories[-1]
        label = str(data.get("sentiment", "neutral"))
        if label not in ("positive", "negative", "neutral"):
            label = "neutral"
        return {
            "category": category,
            "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
            "sentiment": label,
            "score": max(-1.0, min(1.0, float(data.get("score", 0.0)))),
            "model": _config.model,
        }
    except Exception as exc:
        logger.warning("Enrich fallback: %s", exc)
        return {
            "category": "другое" if "другое" in categories else (categories[0] if categories else "другое"),
            "confidence": 0.0,
            "sentiment": "neutral",
            "score": 0.0,
            "model": _config.model,
        }


def reset_circuit_breaker_for_tests() -> None:
    _circuit.failure_count = 0
    _circuit.opened_at = None
    invalidate_enabled_cache()
