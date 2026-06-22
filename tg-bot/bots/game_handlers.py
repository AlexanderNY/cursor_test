"""Хендлеры игрового бота (aiogram 3)."""

from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import settings
from services.game_engine import PickQuestionsInput, pick_random_questions
from services.game_repository import GameOptionRow, game_repository
from services.rating_service import get_leaderboard

logger = logging.getLogger(__name__)

game_router = Router(name="game")


def _parse_admin_telegram_ids() -> set[int]:
    raw = (settings.GAME_ADMIN_TELEGRAM_IDS or "").strip()
    if not raw:
        return set()
    out: set[int] = set()
    for part in raw.split(","):
        p = part.strip()
        if p.isdigit():
            out.add(int(p))
    return out


def _is_admin_user(telegram_user_id: int) -> bool:
    return telegram_user_id in _parse_admin_telegram_ids()


def _mode_keyboard(mode_rows: list) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for m in mode_rows:
        rows.append(
            [
                InlineKeyboardButton(
                    text=m.title[:64],
                    callback_data=f"m|{m.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _answer_keyboard(session_id: int, question_id: int, options: list[GameOptionRow]) -> InlineKeyboardMarkup:
    sorted_opts = sorted(options, key=lambda o: o.option_index)
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for o in sorted_opts:
        label = f"{o.option_index}. {o.option_text[:40]}"
        if len(label) > 64:
            label = label[:61] + "..."
        cb = f"a|{session_id}|{question_id}|{o.id}"
        if len(cb) > 64:
            logger.warning("callback_data too long: %s", cb)
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _send_question(bot, chat_id: int, session_id: int, step: int) -> None:
    qid = await game_repository.get_session_question_at_step(session_id, step)
    if not qid:
        await bot.send_message(chat_id, "Внутренняя ошибка: вопрос не найден.")
        return

    question, options = await game_repository.get_question_with_options(qid)
    if not question or len(options) != 6:
        await bot.send_message(chat_id, "Ошибка загрузки вопроса.")
        return

    caption = question.prompt_text[:1024]
    kb = _answer_keyboard(session_id, question.id, options)

    if question.image_file_id:
        await bot.send_photo(
            chat_id,
            photo=question.image_file_id,
            caption=caption,
            reply_markup=kb,
        )
    elif question.image_url:
        await bot.send_photo(
            chat_id,
            photo=question.image_url,
            caption=caption,
            reply_markup=kb,
        )
    else:
        await bot.send_message(chat_id, text=caption, reply_markup=kb)


@game_router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return

    uid = message.from_user.id
    is_adm = _is_admin_user(uid)
    player_id = await game_repository.upsert_player(
        telegram_user_id=uid,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        is_admin=is_adm,
    )
    logger.debug("Player upsert id=%s tg=%s", player_id, uid)

    modes = await game_repository.list_active_modes()
    if not modes:
        await message.answer(
            "Режимы игры пока не настроены. Обратитесь к администратору.",
        )
        return

    await message.answer(
        "Выберите режим игры:",
        reply_markup=_mode_keyboard(modes),
    )


@game_router.message(Command("rating"))
async def cmd_rating(message: Message) -> None:
    rows = await get_leaderboard(limit=20)
    if not rows:
        await message.answer("Пока нет завершённых игр в рейтинге.")
        return

    lines = ["Топ игроков (лучший результат):", ""]
    for i, r in enumerate(rows, start=1):
        name = r.get("username") or str(r.get("telegram_user_id"))
        dur = r.get("duration_sec")
        dur_s = f", {dur} с" if dur is not None else ""
        lines.append(f"{i}. {name} — {r['score']} очков{dur_s}")
    await message.answer("\n".join(lines))


@game_router.callback_query(F.data.startswith("m|"))
async def cb_pick_mode(query: CallbackQuery) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    try:
        _, mode_s = query.data.split("|", 1)
        mode_id = int(mode_s)
    except (ValueError, AttributeError):
        await query.answer("Некорректные данные", show_alert=True)
        return

    uid = query.from_user.id
    is_adm = _is_admin_user(uid)
    player_id = await game_repository.upsert_player(
        telegram_user_id=uid,
        username=query.from_user.username,
        first_name=query.from_user.first_name,
        is_admin=is_adm,
    )

    mode = await game_repository.get_mode(mode_id)
    if not mode or not mode.is_active:
        await query.answer("Режим недоступен", show_alert=True)
        return

    ready_ids = await game_repository.get_question_ids_ready_for_mode(mode_id)
    picked = pick_random_questions(
        PickQuestionsInput(
            question_ids=ready_ids,
            questions_per_game=mode.questions_per_game,
        )
    ).selected_ids

    if not picked:
        await query.answer()
        await query.message.answer(
            f"В режиме «{mode.title}» нет вопросов с 6 вариантами ответа. "
            "Администратор должен добавить вопросы.",
        )
        return

    session_id = await game_repository.create_session_with_questions(
        player_id=player_id,
        mode_id=mode_id,
        ordered_question_ids=picked,
    )

    await query.answer()
    await query.message.answer(
        f"Режим: {mode.title}\nВопросов: {len(picked)}. Удачи!",
    )
    bot = query.bot or query.message.bot
    await _send_question(bot, query.message.chat.id, session_id, 0)


@game_router.callback_query(F.data.startswith("a|"))
async def cb_answer(query: CallbackQuery) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 4:
        await query.answer("Ошибка данных", show_alert=True)
        return

    _, session_s, question_s, option_s = parts
    try:
        session_id = int(session_s)
        question_id = int(question_s)
        option_id = int(option_s)
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    sess = await game_repository.get_session(session_id)
    if not sess:
        await query.answer("Сессия не найдена", show_alert=True)
        return

    owner_tg = await game_repository.get_telegram_user_id_for_player(sess.player_id)
    if owner_tg != query.from_user.id:
        await query.answer("Это не ваша игра", show_alert=True)
        return

    if sess.status != "in_progress":
        await query.answer("Игра уже завершена", show_alert=True)
        return

    expected_qid = await game_repository.get_session_question_at_step(session_id, sess.current_step)
    if expected_qid != question_id:
        await query.answer("Устаревший вопрос", show_alert=True)
        return

    opt = await game_repository.get_option(option_id)
    if not opt or opt.question_id != question_id:
        await query.answer("Некорректный вариант", show_alert=True)
        return

    result = await game_repository.submit_answer_and_advance(
        session_id=session_id,
        question_id=question_id,
        selected_option_id=option_id,
    )

    if result.get("error") == "wrong_question_for_step":
        await query.answer("Шаг игры изменился", show_alert=True)
        return

    if result.get("duplicate"):
        await query.answer("Вы уже ответили на этот вопрос.", show_alert=True)
        return

    if result.get("error"):
        await query.answer(str(result.get("error")), show_alert=True)
        return

    is_correct = bool(result.get("is_correct"))
    await query.answer("Верно!" if is_correct else "Неверно.", show_alert=False)

    if result.get("session_completed"):
        score = int(result.get("score", 0))
        correct = int(result.get("correct_count", 0))
        total = int(result.get("total_questions", 0))
        await query.message.answer(
            f"Игра окончена!\nОчки: {score}\nВерных ответов: {correct} из {total}.\n"
            f"Команда /rating — рейтинг.\n/start — новая игра.",
        )
        return

    next_step = int(result.get("current_step", 0))
    bot = query.bot or query.message.bot
    await _send_question(bot, query.message.chat.id, session_id, next_step)
