"""Правила сертификата сезона: выпуски, порог квиза и номер бланка."""
from __future__ import annotations

import hashlib
import re
from typing import Any

CERT_QUIZ_PERCENT = 70
INTERVIEW_TRACK_ID = "interview"
INTERVIEW_TRACK_TITLE = "Quiz · Собеседование"
INTERVIEW_CERT_PERCENT = 100
# Минимум вопросов в попытке, чтобы 5/5 не открывало диплом.
INTERVIEW_MIN_TOTAL = 10
CODE_RE = re.compile(r"^9T18-[A-Z0-9]{1,12}-[0-9A-F]{6}$")

TRACKS: tuple[tuple[str, str], ...] = (
    ("b", "Сезон B · Первое приложение"),
    ("s01", "Сезон 1 · Слои и стенд"),
    ("py", "Python · Junior → Senior"),
    ("qa", "QA · Junior → Senior"),
    ("map", "Карта · листья собеса"),
    ("other", "Другие выпуски"),
)


def episode_track_id(episode: str) -> str:
    ep = (episode or "").strip().upper()
    if len(ep) > 1 and ep[0] == "B" and ep[1].isdigit():
        return "b"
    if ep.startswith("S01"):
        return "s01"
    if ep.startswith("PY"):
        return "py"
    if ep.startswith("QA"):
        return "qa"
    if ep.startswith("MAP"):
        return "map"
    return "other"


def has_quiz(structured: object) -> bool:
    if not isinstance(structured, dict):
        return False
    quiz = structured.get("quiz")
    if not isinstance(quiz, list):
        return False
    for item in quiz:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if question and answer:
            return True
    return False


def blank_code(user_id: int, track_id: str) -> str:
    raw = f"{int(user_id)}|{track_id}|9to18-cert"
    token = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:6].upper()
    return f"9T18-{track_id.upper()}-{token}"


def is_cert_code(raw: str) -> bool:
    return bool(CODE_RE.match((raw or "").strip().upper()))


def best_quiz_percents(attempts: list[dict[str, Any]]) -> dict[str, int]:
    best: dict[str, int] = {}
    for item in attempts:
        key = str(item.get("source_key") or "")
        if not key.lower().startswith("learn/"):
            continue
        slug = key.split("/", 1)[1].strip().lower()
        total = int(item.get("total") or 0)
        if not slug or total <= 0:
            continue
        percent = round(int(item.get("score") or 0) / total * 100)
        previous = best.get(slug)
        if previous is None or percent > previous:
            best[slug] = percent
    return best


def assess_tracks(
    posts: list[dict[str, Any]],
    completed_slugs: set[str] | list[str],
    quiz_best: dict[str, int],
) -> list[dict[str, Any]]:
    completed = {str(slug).strip().lower() for slug in completed_slugs if str(slug).strip()}
    buckets: dict[str, list[dict[str, Any]]] = {track_id: [] for track_id, _title in TRACKS}
    seen: dict[str, set[str]] = {track_id: set() for track_id, _title in TRACKS}
    for post in posts:
        track_id = episode_track_id(str(post.get("episode") or ""))
        slug = str(post.get("slug") or "").strip().lower()
        if not slug or slug in seen[track_id]:
            continue
        seen[track_id].add(slug)
        buckets[track_id].append(
            {"slug": slug, "has_quiz": bool(post.get("has_quiz"))}
        )

    board: list[dict[str, Any]] = []
    for track_id, title in TRACKS:
        items = buckets[track_id]
        if not items:
            continue
        slugs = [item["slug"] for item in items]
        done = sum(1 for slug in slugs if slug in completed)
        quiz_slugs = [item["slug"] for item in items if item["has_quiz"]]
        passed = [slug for slug in quiz_slugs if quiz_best.get(slug, 0) >= CERT_QUIZ_PERCENT]
        missing = [slug for slug in quiz_slugs if slug not in set(passed)]
        episodes_done = done == len(slugs)
        quiz_ok = len(passed) == len(quiz_slugs)
        if quiz_slugs:
            quiz_percent = round(sum(quiz_best.get(slug, 0) for slug in quiz_slugs) / len(quiz_slugs))
        else:
            quiz_percent = 0
        board.append(
            {
                "id": track_id,
                "title": title,
                "done": done,
                "total": len(slugs),
                "earned": episodes_done and quiz_ok,
                "quiz_required": len(quiz_slugs),
                "quiz_passed": len(passed),
                "quiz_percent": quiz_percent,
                "quiz_missing": missing,
            }
        )
    return board


def is_interview_source_key(source_key: str) -> bool:
    key = (source_key or "").strip().lower()
    return key == "learn/interview" or key.startswith("learn/interview/")


def best_interview_quiz_percent(attempts: list[dict[str, Any]]) -> int:
    """Лучший процент по quiz_page попыткам собеседования (не короче min total)."""
    best = 0
    for item in attempts:
        if not is_interview_source_key(str(item.get("source_key") or "")):
            continue
        total = int(item.get("total") or 0)
        if total < INTERVIEW_MIN_TOTAL:
            continue
        percent = round(int(item.get("score") or 0) / total * 100)
        if percent > best:
            best = percent
    return best


def assess_interview_track(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Синтетический трек: диплом за 100% квиза собеседования на /game/quiz."""
    percent = best_interview_quiz_percent(attempts)
    earned = percent >= INTERVIEW_CERT_PERCENT
    return {
        "id": INTERVIEW_TRACK_ID,
        "title": INTERVIEW_TRACK_TITLE,
        "done": 1 if earned else 0,
        "total": 1,
        "earned": earned,
        "quiz_required": 1,
        "quiz_passed": 1 if earned else 0,
        "quiz_percent": percent,
        "quiz_missing": [] if earned else ["interview"],
    }
