"""Правила форума: область, вид ветки, доступ. Без I/O."""

from __future__ import annotations

from typing import Any, Optional, Sequence

SCOPES = frozenset({"workspace", "platform"})
KINDS = frozenset({"discussion", "bug_report", "suggestion", "contact_author"})
OWNER_ROLES = frozenset({"owner", "admin", "manager"})

MAX_TITLE_LENGTH = 255
MAX_BODY_LENGTH = 8000

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


def clean_title(title: str) -> str:
    collapsed = " ".join(title.split())
    return collapsed[:MAX_TITLE_LENGTH]


def clean_body(body: str) -> str:
    return body.strip()[:MAX_BODY_LENGTH]


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
    }


def post_from_row(row: Sequence[Any]) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "thread_id": int(row[1]),
        "body": str(row[2]),
        "author_id": int(row[3]),
        "author_name": str(row[4] or "участник"),
        "created_at": row[5],
    }
