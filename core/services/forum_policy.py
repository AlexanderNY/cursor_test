"""Правила форума: область, вид ветки, доступ. Без I/O."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

SCOPES = frozenset({"workspace", "platform"})
KINDS = frozenset({"discussion", "bug_report", "suggestion", "contact_author"})
IDEA_STATUSES = frozenset({"new", "accepted", "in_progress", "done"})
OWNER_ROLES = frozenset({"owner", "admin", "manager"})

MAX_TITLE_LENGTH = 255
MAX_BODY_LENGTH = 8000
AVATAR_MAX_BYTES = 2 * 1024 * 1024
EDIT_WINDOW_SECONDS = 15 * 60
QUOTE_MAX_LENGTH = 500
SEARCH_MAX_LENGTH = 80
_MENTION = re.compile(r"(?<![\w@])@([\w.\-]{2,32})")

NO_WORKSPACE = (
    "Нет активного Workspace. Создайте команду или откройте ветку на платформе."
)
THREAD_CLOSED = "Ветка закрыта"
VOTE_KIND_ONLY = "Голосовать можно только за идеи"
THREAD_NOT_FOUND = "Ветка не найдена"
POST_NOT_FOUND = "Сообщение не найдено"
FORBIDDEN = "Недостаточно прав"
EMPTY_TEXT = "Введите текст"
UNKNOWN_SCOPE = "Неизвестная область"
UNKNOWN_KIND = "Неизвестный тип ветки"
UNKNOWN_STATUS = "Неизвестный статус идеи"
STATUS_KIND_ONLY = "Статус есть только у идей"
PIN_SCOPE_ONLY = "Закрепить можно ветку команды"
EDIT_EXPIRED = "Сообщение можно править 15 минут после отправки"
QUOTE_NOT_IN_THREAD = "Цитата не из этой ветки"
ATTACHMENT_KIND_ONLY = "Скриншот можно приложить к ошибке"


def parse_scope(raw: Optional[str]) -> Optional[str]:
    """Возвращает scope или None, если значение неизвестно."""
    if raw is None:
        return None
    value = raw.strip().lower()
    if value not in SCOPES:
        return None
    return value


def parse_kind_filter(raw: Optional[str]) -> tuple[bool, Optional[str]]:
    """Фильтр списка: (ok, kind). kind=None — все типы."""
    if raw is None or raw.strip() == "":
        return True, None
    value = raw.strip().lower()
    if value not in KINDS:
        return False, None
    return True, value


def votes_allowed(kind: str) -> bool:
    """Голос есть только у идей — бывший список «Что далее»."""
    return kind == "suggestion"


def parse_status(raw: Optional[str]) -> Optional[str]:
    """Статус идеи или None, если значение неизвестно."""
    if raw is None:
        return None
    value = raw.strip().lower()
    if value not in IDEA_STATUSES:
        return None
    return value


def can_set_status(*, kind: str, is_platform_admin: bool) -> bool:
    """Статус идеи меняет admin платформы."""
    return kind == "suggestion" and is_platform_admin


def can_pin(*, scope: str, workspace_role: Optional[str]) -> bool:
    """Один закреп в команде ставит владелец Workspace."""
    return scope == "workspace" and workspace_role in OWNER_ROLES


def can_attach(*, kind: str, is_closed: bool, can_moderate_thread: bool) -> bool:
    """Скриншот — у открытой ошибки, автор или модератор."""
    return kind == "bug_report" and not is_closed and can_moderate_thread


def can_edit_post(
    *,
    post_author_id: int,
    user_id: int,
    created_at: datetime,
    now: datetime,
    is_closed: bool,
) -> bool:
    """Автор правит своё сообщение 15 минут, пока ветка открыта."""
    if is_closed or post_author_id <= 0 or post_author_id != user_id:
        return False
    created = created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=timezone.utc)
    current = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
    return (current - created).total_seconds() <= EDIT_WINDOW_SECONDS


def extract_mentions(body: str) -> list[str]:
    """Уникальные @имена в порядке появления, без учёта регистра."""
    found: list[str] = []
    seen: set[str] = set()
    for match in _MENTION.finditer(body or ""):
        name = match.group(1).lower()
        if name in seen:
            continue
        seen.add(name)
        found.append(name)
    return found


def search_pattern(raw: Optional[str]) -> str:
    """Шаблон ILIKE. Пустая строка — фильтр не применяется."""
    text = " ".join((raw or "").split())[:SEARCH_MAX_LENGTH]
    if not text:
        return ""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def quote_excerpt(body: str) -> str:
    flat = " ".join((body or "").split())
    return flat[:QUOTE_MAX_LENGTH]


def attachment_storage_key(thread_id: int) -> str:
    return f"forum-attachments/{int(thread_id)}"


def attachment_public_path(thread_id: int) -> str:
    return f"/core/forum/attachments/{int(thread_id)}"


def thread_href(*, scope: str, thread_id: int) -> str:
    return f"/forum?scope={scope}&thread={int(thread_id)}"


def reply_notice(*, author_name: str, title: str, href: str, mentioned: bool) -> str:
    """Строка оповещения. HTML только из экранированных полей и ссылки на ветку."""
    who = html.escape(author_name or "участник")
    label = html.escape(title or "ветка")
    link = html.escape(href, quote=True)
    verb = "упомянул вас" if mentioned else "ответил"
    return (
        f"<p><strong>{who}</strong> {verb} в «{label}». "
        f'<a href="{link}">Открыть</a></p>'
    )


def clean_title(title: str) -> str:
    collapsed = " ".join(title.split())
    return collapsed[:MAX_TITLE_LENGTH]


def clean_body(body: str) -> str:
    return body.strip()[:MAX_BODY_LENGTH]


def avatar_storage_key(user_id: int) -> str:
    """Ключ объекта в хранилище. Один файл на пользователя, новая загрузка заменяет его."""
    return f"avatars/{int(user_id)}"


def avatar_public_path(user_id: int) -> str:
    """Стабильный путь через gateway. Картинка отдаётся без JWT, чтобы её мог показать <img>."""
    return f"/core/forum/avatars/{int(user_id)}"


def sniff_image_type(data: bytes) -> Optional[str]:
    """Тип по сигнатуре файла. None, если это не JPEG, PNG, GIF или WEBP."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def can_read_thread(*, scope: str, group_id: Optional[int], is_member: bool) -> bool:
    """Платформа видна всем авторизованным. Workspace — только участникам группы."""
    if scope == "platform":
        return True
    if scope != "workspace" or group_id is None:
        return False
    return is_member


def can_open_thread(*, scope: str, workspace_role: Optional[str]) -> bool:
    """Любой участник Workspace может открыть ветку. Платформа — любой пользователь."""
    if scope == "platform":
        return True
    return workspace_role is not None


def can_moderate(
    *,
    author_id: int,
    user_id: int,
    is_platform_admin: bool,
    workspace_role: Optional[str],
) -> bool:
    """Автор, владелец Workspace или admin платформы."""
    if author_id > 0 and user_id == author_id:
        return True
    if is_platform_admin:
        return True
    return workspace_role in OWNER_ROLES


def thread_permissions(
    *,
    author_id: int,
    user_id: int,
    is_platform_admin: bool,
    workspace_role: Optional[str],
    is_closed: bool,
    kind: str,
    scope: Optional[str] = None,
) -> dict[str, bool]:
    moderate = can_moderate(
        author_id=author_id,
        user_id=user_id,
        is_platform_admin=is_platform_admin,
        workspace_role=workspace_role,
    )
    return {
        "can_reply": not is_closed,
        "can_vote": votes_allowed(kind) and not is_closed,
        "can_close": moderate,
        "can_delete": moderate,
        "can_set_status": can_set_status(kind=kind, is_platform_admin=is_platform_admin),
        "can_pin": can_pin(scope=scope or "", workspace_role=workspace_role),
        "can_attach": can_attach(
            kind=kind,
            is_closed=is_closed,
            can_moderate_thread=moderate,
        ),
    }


def can_delete_post(
    *,
    post_author_id: int,
    user_id: int,
    is_platform_admin: bool,
    workspace_role: Optional[str],
) -> bool:
    return can_moderate(
        author_id=post_author_id,
        user_id=user_id,
        is_platform_admin=is_platform_admin,
        workspace_role=workspace_role,
    )


def thread_from_row(row: Sequence[Any]) -> dict[str, Any]:
    """Поля ветки из SQL-строки без флагов доступа."""
    group_id = row[2]
    return {
        "id": int(row[0]),
        "scope": str(row[1]),
        "group_id": int(group_id) if group_id is not None else None,
        "group_name": row[3],
        "kind": str(row[4]),
        "title": str(row[5]),
        "body": str(row[6]),
        "author_id": int(row[7]),
        "author_name": str(row[8] or "участник"),
        "is_closed": bool(row[9]),
        "vote_count": int(row[10] or 0),
        "voted": bool(row[11]),
        "reply_count": int(row[12] or 0),
        "created_at": row[13],
        "updated_at": row[14],
        "author_avatar": row[15] or None,
        "status": str(row[16] or "new"),
        "is_pinned": bool(row[17]),
        "attachment_path": row[18] or None,
        "unread": bool(row[19]),
    }


def post_from_row(row: Sequence[Any]) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "thread_id": int(row[1]),
        "body": str(row[2]),
        "author_id": int(row[3]),
        "author_name": str(row[4] or "участник"),
        "created_at": row[5],
        "author_avatar": row[6] or None,
        "updated_at": row[7],
        "quote_author": row[8] or None,
        "quote_body": row[9] or None,
    }
