"""Mock OpenAI-compatible server for local dev without GPU."""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List, Optional
import json
import re
import uvicorn

app = FastAPI(title="AI Mock Server")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "qwen3-8b-instruct"
    messages: List[ChatMessage]
    max_tokens: int = 512
    temperature: float = 0.2


def _mock_response(content: str) -> dict[str, Any]:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "model": "mock",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest):
    user_msg = ""
    for msg in reversed(body.messages):
        if msg.role == "user":
            user_msg = msg.content
            break

    if "дайджест" in user_msg.lower() or "digest" in user_msg.lower():
        return _mock_response("Краткий дайджест: основные темы обсуждались в канале.")

    if "сократи" in user_msg.lower() or "summarize" in user_msg.lower():
        text = user_msg.split("\n\n")[-1][:200]
        return _mock_response(text + "…")

    if "sentiment" in user_msg.lower() or "тональность" in user_msg.lower():
        label = "negative" if any(w in user_msg.lower() for w in ("плох", "ужас", "negative")) else "neutral"
        return _mock_response(json.dumps({"sentiment": label, "score": -0.3 if label == "negative" else 0.1}))

    if "классифицируй" in user_msg.lower() or "category" in user_msg.lower():
        category = "новости"
        if "реклам" in user_msg.lower():
            category = "реклама"
        return _mock_response(json.dumps({"category": category, "confidence": 0.85, "sentiment": "neutral", "score": 0.0}))

    if "json" in user_msg.lower():
        return _mock_response(json.dumps({"category": "другое", "confidence": 0.5, "sentiment": "neutral", "score": 0.0}))

    return _mock_response(user_msg[: min(len(user_msg), body.max_tokens)])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
