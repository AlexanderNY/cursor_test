"""Unit tests for mock-interview chat sessions."""
from __future__ import annotations

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
