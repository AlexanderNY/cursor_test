"""In-memory multi-turn mock-interview chat sessions.

Single-process only: sessions and locks live in this worker's memory.
Do not scale resume-api horizontally without sticky sessions or a shared store.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

MAX_TURNS = 5
SESSION_TTL_SEC = 45 * 60
MAX_SESSIONS = 2_000

_lock = threading.Lock()
_sessions: dict[str, "MockChatSession"] = {}
_async_locks: dict[str, asyncio.Lock] = {}


@dataclass
class MockChatSession:
    session_id: str
    user_id: int
    resume_id: str
    specialization: str
    skills: list[dict[str, Any]]
    messages: list[dict[str, str]] = field(default_factory=list)
    turn: int = 0
    max_turns: int = MAX_TURNS
    scores: list[int] = field(default_factory=list)
    done: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


def _cleanup_locked(now: float) -> None:
    stale = [
        sid
        for sid, sess in _sessions.items()
        if now - sess.updated_at > SESSION_TTL_SEC
    ]
    for sid in stale:
        _sessions.pop(sid, None)
        _async_locks.pop(sid, None)
    if len(_sessions) <= MAX_SESSIONS:
        return
    ordered = sorted(_sessions.items(), key=lambda kv: kv[1].updated_at)
    overflow = len(_sessions) - MAX_SESSIONS
    for sid, _ in ordered[:overflow]:
        _sessions.pop(sid, None)
        _async_locks.pop(sid, None)


def _async_lock_for(session_id: str) -> asyncio.Lock:
    """Per-session asyncio lock; created under the threading lock."""
    with _lock:
        lock = _async_locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            _async_locks[session_id] = lock
        return lock


def _template_first_question(skills: list[dict[str, Any]]) -> str:
    if not skills:
        return "Расскажите о своём самом интересном техническом проекте."
    skill = skills[0]
    name = skill.get("name") or skill.get("key") or "технологии"
    return f"Расскажите, как вы применяли {name} на практике. Приведите конкретный пример."


def _template_followup(
    *,
    turn: int,
    skills: list[dict[str, Any]],
    last_score: int,
) -> str:
    if turn >= MAX_TURNS:
        return "Спасибо за ответы. Это был финальный вопрос."
    idx = min(turn, len(skills) - 1) if skills else 0
    skill = skills[idx] if skills else {}
    name = skill.get("name") or skill.get("key") or "систему"
    if last_score >= 4:
        return f"Хорошо. Углубимся: какие trade-off вы учитывали, работая с {name}?"
    return (
        f"Давайте уточним. Опишите, как бы вы отладили проблему, связанную с {name}, "
        "если в проде внезапно выросла latency."
    )


def create_session(
    *,
    user_id: int,
    resume_id: str,
    specialization: str,
    skills: list[dict[str, Any]],
    first_question: Optional[str] = None,
    max_turns: int = MAX_TURNS,
) -> MockChatSession:
    now = time.time()
    session_id = str(uuid.uuid4())
    question = (first_question or "").strip() or _template_first_question(skills)
    sess = MockChatSession(
        session_id=session_id,
        user_id=user_id,
        resume_id=resume_id,
        specialization=specialization or "",
        skills=list(skills or []),
        messages=[{"role": "assistant", "content": question}],
        turn=1,
        max_turns=max(1, min(int(max_turns), MAX_TURNS)),
        created_at=now,
        updated_at=now,
    )
    with _lock:
        _cleanup_locked(now)
        _sessions[session_id] = sess
        _async_locks.setdefault(session_id, asyncio.Lock())
    return sess


def get_session(session_id: str, user_id: int) -> Optional[MockChatSession]:
    with _lock:
        sess = _sessions.get(session_id)
        if sess is None:
            return None
        if sess.user_id != user_id:
            return None
        if time.time() - sess.updated_at > SESSION_TTL_SEC:
            _sessions.pop(session_id, None)
            _async_locks.pop(session_id, None)
            return None
        return sess


def drop_sessions_for_resume(resume_id: str) -> int:
    """Drop in-memory chat sessions tied to a deleted resume."""
    rid = str(resume_id)
    with _lock:
        to_drop = [sid for sid, sess in _sessions.items() if sess.resume_id == rid]
        for sid in to_drop:
            _sessions.pop(sid, None)
            _async_locks.pop(sid, None)
        return len(to_drop)


def session_public(sess: MockChatSession) -> dict[str, Any]:
    overall = None
    summary = None
    if sess.done and sess.scores:
        overall = round(sum(sess.scores) / len(sess.scores), 1)
        summary = (
            f"Средняя оценка {overall}/5 по {len(sess.scores)} ответам. "
            + (
                "Уверенный уровень — можно идти на собес."
                if overall >= 3.5
                else "Есть пробелы — повторите темы с низкими оценками."
            )
        )
    elif sess.done:
        overall = 0
        summary = "Собеседование завершено без оценённых ответов."
    return {
        "sessionId": sess.session_id,
        "messages": list(sess.messages),
        "turn": sess.turn,
        "maxTurns": sess.max_turns,
        "done": sess.done,
        "scores": list(sess.scores),
        "overallScore": overall,
        "summary": summary,
    }


async def append_user_message(
    sess: MockChatSession,
    content: str,
    *,
    evaluate_fn: Any,
    reply_fn: Any,
) -> dict[str, Any]:
    """Append user reply, score it, add assistant follow-up or finish.

    Serialized per session_id so concurrent chat/message calls cannot corrupt
    turn/scores/messages while AI evaluate/reply are awaited.
    """
    text = (content or "").strip()
    if not text:
        raise ValueError("Пустой ответ")

    alock = _async_lock_for(sess.session_id)
    async with alock:
        with _lock:
            current = _sessions.get(sess.session_id)
            if current is None or current.user_id != sess.user_id:
                raise ValueError("Сессия не найдена или истекла")
            if current.done:
                raise ValueError("Сессия уже завершена")
            working = current

        working.messages.append({"role": "user", "content": text[:4000]})
        last_score = 3
        feedback = ""
        try:
            skill_key = ""
            if working.skills:
                idx = min(max(working.turn - 1, 0), len(working.skills) - 1)
                skill_key = str(working.skills[idx].get("key") or "")
            question = ""
            for msg in reversed(working.messages[:-1]):
                if msg.get("role") == "assistant":
                    question = msg.get("content") or ""
                    break
            result = await evaluate_fn(
                question=question, answer=text, skill_key=skill_key
            )
            last_score = int(result.get("score") or 3)
            feedback = str(result.get("feedback") or "").strip()
        except Exception:
            logger.exception("chat evaluate failed; default score")
            last_score = 3
            feedback = "Оценка по шаблону: ответ принят."

        last_score = max(1, min(5, last_score))
        working.scores.append(last_score)

        finished = working.turn >= working.max_turns
        if finished:
            working.done = True
            closing = feedback or "Спасибо за ответы!"
            if not closing.endswith("."):
                closing += "."
            closing += " Собеседование завершено."
            working.messages.append({"role": "assistant", "content": closing[:800]})
        else:
            try:
                follow = await reply_fn(
                    sess=working,
                    last_score=last_score,
                    feedback=feedback,
                )
            except Exception:
                logger.exception("chat follow-up failed; template")
                follow = _template_followup(
                    turn=working.turn,
                    skills=working.skills,
                    last_score=last_score,
                )
            prefix = f"Оценка {last_score}/5. {feedback} ".strip() if feedback else ""
            body = (prefix + (follow or "")).strip()[:900]
            working.messages.append(
                {
                    "role": "assistant",
                    "content": body
                    or _template_followup(
                        turn=working.turn,
                        skills=working.skills,
                        last_score=last_score,
                    ),
                }
            )
            working.turn += 1

        working.updated_at = time.time()
        with _lock:
            if working.session_id in _sessions:
                _sessions[working.session_id] = working

        public = session_public(working)
        public["lastScore"] = last_score
        public["reply"] = working.messages[-1]
        return public


def clear_sessions_for_tests() -> None:
    with _lock:
        _sessions.clear()
        _async_locks.clear()
