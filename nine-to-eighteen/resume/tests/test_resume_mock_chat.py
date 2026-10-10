"""Unit tests for mock-interview chat sessions."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

_SPEC = importlib.util.spec_from_file_location(
    "resume_mock_chat_ut",
    API_DIR / "services" / "resume_mock_chat.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_mock_chat_ut"] = _mod
_SPEC.loader.exec_module(_mod)

create_session = _mod.create_session
get_session = _mod.get_session
append_user_message = _mod.append_user_message
session_public = _mod.session_public
clear_sessions_for_tests = _mod.clear_sessions_for_tests
drop_sessions_for_resume = _mod.drop_sessions_for_resume


@pytest.fixture(autouse=True)
def _clean():
    clear_sessions_for_tests()
    yield
    clear_sessions_for_tests()


def test_start_creates_session_with_assistant_message():
    sess = create_session(
        user_id=1,
        resume_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        specialization="Python",
        skills=[{"key": "python", "name": "Python"}],
        first_question="Вопрос про Python?",
        max_turns=3,
    )
    public = session_public(sess)
    assert public["sessionId"]
    assert public["turn"] == 1
    assert public["maxTurns"] == 3
    assert public["done"] is False
    assert public["messages"][0]["role"] == "assistant"
    assert "Python" in public["messages"][0]["content"]


def test_get_session_wrong_user_returns_none():
    sess = create_session(
        user_id=1,
        resume_id="rid",
        specialization="",
        skills=[{"key": "fastapi", "name": "FastAPI"}],
    )
    assert get_session(sess.session_id, 2) is None
    assert get_session("missing", 1) is None


@pytest.mark.asyncio
async def test_message_advances_and_finishes():
    skills = [
        {"key": "python", "name": "Python"},
        {"key": "fastapi", "name": "FastAPI"},
        {"key": "docker", "name": "Docker"},
    ]
    sess = create_session(
        user_id=7,
        resume_id="rid",
        specialization="Backend",
        skills=skills,
        max_turns=2,
    )

    async def evaluate_fn(*, question: str, answer: str, skill_key: str):
        return {"score": 4, "feedback": "Ок", "passed": True}

    async def reply_fn(*, sess, last_score: int, feedback: str):
        return "Следующий вопрос про FastAPI?"

    out1 = await append_user_message(
        sess,
        "Делал API на Python",
        evaluate_fn=evaluate_fn,
        reply_fn=reply_fn,
    )
    assert out1["done"] is False
    assert out1["lastScore"] == 4
    assert out1["turn"] == 2
    assert out1["messages"][-1]["role"] == "assistant"

    out2 = await append_user_message(
        get_session(sess.session_id, 7),
        "Использовал FastAPI",
        evaluate_fn=evaluate_fn,
        reply_fn=reply_fn,
    )
    assert out2["done"] is True
    assert out2["overallScore"] == 4.0
    assert out2["summary"]


@pytest.mark.asyncio
async def test_empty_message_raises():
    sess = create_session(
        user_id=1,
        resume_id="rid",
        specialization="",
        skills=[{"key": "git", "name": "Git"}],
    )

    async def evaluate_fn(**_kwargs):
        return {"score": 3, "feedback": "", "passed": True}

    async def reply_fn(**_kwargs):
        return "ok"

    with pytest.raises(ValueError):
        await append_user_message(sess, "  ", evaluate_fn=evaluate_fn, reply_fn=reply_fn)


@pytest.mark.asyncio
async def test_concurrent_messages_serialize():
    skills = [{"key": "python", "name": "Python"}, {"key": "sql", "name": "SQL"}]
    sess = create_session(
        user_id=3,
        resume_id="rid-concurrent",
        specialization="Backend",
        skills=skills,
        max_turns=3,
    )

    async def evaluate_fn(*, question: str, answer: str, skill_key: str):
        await asyncio.sleep(0.03)
        return {"score": 4, "feedback": "ok", "passed": True}

    async def reply_fn(*, sess, last_score: int, feedback: str):
        await asyncio.sleep(0.01)
        return "Следующий вопрос?"

    await asyncio.gather(
        append_user_message(
            sess, "Ответ A", evaluate_fn=evaluate_fn, reply_fn=reply_fn
        ),
        append_user_message(
            get_session(sess.session_id, 3),
            "Ответ B",
            evaluate_fn=evaluate_fn,
            reply_fn=reply_fn,
        ),
    )
    final = get_session(sess.session_id, 3)
    assert final is not None
    user_msgs = [m for m in final.messages if m["role"] == "user"]
    assert len(user_msgs) == 2
    assert len(final.scores) == 2
    assert final.turn == 3


def test_drop_sessions_for_resume():
    create_session(
        user_id=1,
        resume_id="keep-me",
        specialization="",
        skills=[{"key": "git", "name": "Git"}],
    )
    drop = create_session(
        user_id=1,
        resume_id="drop-me",
        specialization="",
        skills=[{"key": "git", "name": "Git"}],
    )
    assert drop_sessions_for_resume("drop-me") == 1
    assert get_session(drop.session_id, 1) is None
    assert _mod._sessions  # keep-me still present
