"""Диагностика работоспособности игрового Telegram-бота."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from config import settings
from schemas_game import DiagnosticCheck, GameBotDiagnosticsOut
from services.bot_manager import is_bot_polling
from services.bot_telegram import fetch_bot_info, fetch_webhook_info
from services.game_repository import game_repository
from services.media_storage import get_media_storage
from services.menu_repository import menu_repository


def _overall_status(checks: list[DiagnosticCheck]) -> Literal["ok", "warning", "error"]:
    if any(check.status == "error" for check in checks):
        return "error"
    if any(check.status == "warning" for check in checks):
        return "warning"
    return "ok"


async def _check_s3_storage() -> DiagnosticCheck:
    endpoint = (settings.S3_ENDPOINT_URL or "").strip()
    bucket = (settings.S3_BUCKET or "").strip()
    if not endpoint or not bucket:
        return DiagnosticCheck(
            key="s3",
            label="Хранилище S3",
            status="warning",
            message="S3 не настроен — загрузка изображений недоступна",
        )

    storage = get_media_storage()
    if not storage:
        return DiagnosticCheck(
            key="s3",
            label="Хранилище S3",
            status="error",
            message="Не удалось инициализировать S3-клиент",
        )

    try:
        import aioboto3

        session = aioboto3.Session()
        async with session.client(**storage._client_kwargs()) as client:
            await client.head_bucket(Bucket=storage.bucket)
        return DiagnosticCheck(
            key="s3",
            label="Хранилище S3",
            status="ok",
            message=f"Бакет «{bucket}» доступен",
        )
    except Exception as exc:
        return DiagnosticCheck(
            key="s3",
            label="Хранилище S3",
            status="error",
            message=f"Ошибка подключения к S3: {exc}",
        )


async def run_bot_diagnostics(bot_id: int) -> GameBotDiagnosticsOut:
    bot = await game_repository.get_bot(bot_id)
    if not bot:
        raise ValueError("Bot not found")

    checks: list[DiagnosticCheck] = []
    hints: list[str] = []

    checks.append(
        DiagnosticCheck(
            key="database",
            label="База данных",
            status="ok",
            message="Подключение к PostgreSQL активно",
        )
    )

    if bot.is_active:
        checks.append(
            DiagnosticCheck(
                key="bot_active",
                label="Статус в админке",
                status="ok",
                message="Бот включён",
            )
        )
    else:
        checks.append(
            DiagnosticCheck(
                key="bot_active",
                label="Статус в админке",
                status="warning",
                message="Бот выключен",
            )
        )
        hints.append("Включите бота в настройках, чтобы запустить polling.")

    is_polling = is_bot_polling(bot_id)
    if bot.is_active and is_polling:
        checks.append(
            DiagnosticCheck(
                key="polling",
                label="Long polling",
                status="ok",
                message="Polling запущен в tg-game",
            )
        )
    elif bot.is_active:
        checks.append(
            DiagnosticCheck(
                key="polling",
                label="Long polling",
                status="error",
                message="Polling не запущен",
            )
        )
        hints.append("Перезапустите tg-game или сохраните настройки бота для перезагрузки polling.")
    else:
        checks.append(
            DiagnosticCheck(
                key="polling",
                label="Long polling",
                status="warning",
                message="Polling не требуется (бот выключен)",
            )
        )

    try:
        tg_info = await fetch_bot_info(bot.token)
        username = tg_info.get("username")
        display = f"@{username}" if username else str(tg_info.get("id", "бот"))
        checks.append(
            DiagnosticCheck(
                key="telegram_api",
                label="Telegram Bot API",
                status="ok",
                message=f"Токен валиден ({display})",
            )
        )
    except Exception as exc:
        checks.append(
            DiagnosticCheck(
                key="telegram_api",
                label="Telegram Bot API",
                status="error",
                message=str(exc),
            )
        )
        hints.append("Проверьте токен в @BotFather и обновите его в настройках бота.")

    try:
        webhook = await fetch_webhook_info(bot.token)
        webhook_url = (webhook.get("url") or "").strip()
        if webhook_url:
            checks.append(
                DiagnosticCheck(
                    key="webhook",
                    label="Webhook",
                    status="error",
                    message=f"Установлен webhook: {webhook_url}",
                )
            )
            hints.append(
                "Удалите webhook через deleteWebhook — бот работает через long polling, не webhook.",
            )
        else:
            pending = int(webhook.get("pending_update_count") or 0)
            detail = f"Webhook не установлен (pending updates: {pending})"
            checks.append(
                DiagnosticCheck(
                    key="webhook",
                    label="Webhook",
                    status="ok",
                    message=detail,
                )
            )
    except Exception as exc:
        checks.append(
            DiagnosticCheck(
                key="webhook",
                label="Webhook",
                status="warning",
                message=f"Не удалось проверить: {exc}",
            )
        )

    active_modes = await game_repository.admin_list_modes(include_inactive=False, bot_id=bot_id)
    if not active_modes:
        checks.append(
            DiagnosticCheck(
                key="modes",
                label="Режимы игры",
                status="warning",
                message="Нет активных режимов",
            )
        )
        hints.append("Создайте и включите хотя бы один режим (викторина или меню).")
    else:
        quiz_modes = [mode for mode in active_modes if mode.mode_type == "quiz"]
        menu_modes = [mode for mode in active_modes if mode.mode_type == "menu"]
        checks.append(
            DiagnosticCheck(
                key="modes",
                label="Режимы игры",
                status="ok",
                message=(
                    f"{len(active_modes)} активных "
                    f"({len(quiz_modes)} викторина, {len(menu_modes)} меню)"
                ),
            )
        )

        for mode in quiz_modes:
            questions = await game_repository.admin_list_questions(mode.id)
            active_questions = [question for question in questions if question.get("is_active")]
            required = mode.questions_per_game
            if len(active_questions) < required:
                status: Literal["ok", "warning", "error"] = (
                    "error" if len(active_questions) == 0 else "warning"
                )
                checks.append(
                    DiagnosticCheck(
                        key=f"quiz_questions_{mode.id}",
                        label=f"Вопросы: {mode.title}",
                        status=status,
                        message=f"{len(active_questions)} активных, нужно минимум {required}",
                    )
                )
                hints.append(f"Добавьте вопросы в режим «{mode.title}» (минимум {required}).")
            else:
                checks.append(
                    DiagnosticCheck(
                        key=f"quiz_questions_{mode.id}",
                        label=f"Вопросы: {mode.title}",
                        status="ok",
                        message=f"{len(active_questions)} активных вопросов",
                    )
                )

        for mode in menu_modes:
            nodes = await menu_repository.admin_list_nodes(mode.id)
            active_nodes = [node for node in nodes if node.get("is_active")]
            if not active_nodes:
                checks.append(
                    DiagnosticCheck(
                        key=f"menu_nodes_{mode.id}",
                        label=f"Меню: {mode.title}",
                        status="warning",
                        message="Нет активных пунктов меню",
                    )
                )
                hints.append(f"Добавьте пункты в режим меню «{mode.title}».")
            else:
                checks.append(
                    DiagnosticCheck(
                        key=f"menu_nodes_{mode.id}",
                        label=f"Меню: {mode.title}",
                        status="ok",
                        message=f"{len(active_nodes)} активных пунктов",
                    )
                )

    checks.append(await _check_s3_storage())

    public_base = (settings.GAME_MEDIA_PUBLIC_BASE_URL or "").strip()
    if not public_base:
        checks.append(
            DiagnosticCheck(
                key="public_media_url",
                label="Публичные URL медиа",
                status="warning",
                message="GAME_MEDIA_PUBLIC_BASE_URL не задан",
            )
        )
        hints.append("Задайте GAME_MEDIA_PUBLIC_BASE_URL с адресом, доступным Telegram.")
    elif "localhost" in public_base or "127.0.0.1" in public_base:
        checks.append(
            DiagnosticCheck(
                key="public_media_url",
                label="Публичные URL медиа",
                status="warning",
                message=f"Локальный адрес: {public_base}",
            )
        )
        hints.append("Укажите публичный URL (например https://www.copyparse.ru) для картинок в Telegram.")
    else:
        checks.append(
            DiagnosticCheck(
                key="public_media_url",
                label="Публичные URL медиа",
                status="ok",
                message=public_base,
            )
        )

    admin_token = (settings.GAME_ADMIN_API_TOKEN or "").strip()
    if admin_token:
        checks.append(
            DiagnosticCheck(
                key="admin_api",
                label="Админ API",
                status="ok",
                message="Токен админки настроен",
            )
        )
    else:
        checks.append(
            DiagnosticCheck(
                key="admin_api",
                label="Админ API",
                status="warning",
                message="GAME_ADMIN_API_TOKEN не задан",
            )
        )

    return GameBotDiagnosticsOut(
        bot_id=bot_id,
        bot_name=bot.name,
        collected_at=datetime.now(timezone.utc).isoformat(),
        overall_status=_overall_status(checks),
        checks=checks,
        hints=hints,
    )
