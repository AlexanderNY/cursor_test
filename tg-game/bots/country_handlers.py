"""Хендлеры режимов викторины по странам (тренировка, флаги, карта)."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.game_engine import (
    BuildCountryQuizInput,
    build_country_quiz_rounds,
    build_training_order,
    format_country_card,
    iso2_to_flag_emoji,
)
from services.game_repository import GameCountryRow, GameModeRow, game_repository
from services.media_storage import extract_media_filename, fetch_media_bytes

logger = logging.getLogger(__name__)

country_router = Router(name="country")


def _training_keyboard(session_id: int, step_index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Дальше",
                    callback_data=f"cn|{session_id}|{step_index}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Меню",
                    callback_data=f"menu|{session_id}",
                )
            ],
        ]
    )


def _quiz_keyboard(
    session_id: int,
    step_index: int,
    options: list[GameCountryRow],
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for country in options:
        label = country.name_ru
        if len(label) > 64:
            label = label[:61] + "..."
        cb = f"ca|{session_id}|{step_index}|{country.id}"
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Меню",
                callback_data=f"menu|{session_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _load_photo(
    image_url: str | None,
    image_file_id: str | None,
) -> tuple[str | BufferedInputFile | None, bool]:
    """Возвращает (photo, is_bytes_upload)."""
    if image_file_id:
        return image_file_id, False
    filename = extract_media_filename(image_url)
    if not filename:
        return None, False
    result = await fetch_media_bytes(filename)
    if not result:
        logger.warning("Country media not found in storage: %s", filename)
        return None, False
    body, _content_type = result
    return BufferedInputFile(body, filename=filename), True


async def start_country_mode(
    bot,
    chat_id: int,
    mode: GameModeRow,
    *,
    player_id: int,
) -> None:
    countries = await game_repository.list_ready_countries()
    if len(countries) < 6:
        await bot.send_message(
            chat_id,
            "Справочник стран ещё не загружен (нужны флаги и карты). "
            "Администратор должен запустить seed_countries.",
        )
        return

    by_id = {c.id: c for c in countries}
    country_ids = [c.id for c in countries]

    if mode.mode_type == "country_training":
        ordered = build_training_order(country_ids)
        steps = [(cid, []) for cid in ordered]
        session_id = await game_repository.create_country_session_with_steps(
            player_id=player_id,
            mode_id=mode.id,
            steps=steps,
        )
        await bot.send_message(
            chat_id,
            f"Режим: {mode.title}\nСтран: {len(ordered)}. Листайте карточки.",
        )
        await _send_training_card(bot, chat_id, session_id, 0)
        return

    rounds = build_country_quiz_rounds(
        BuildCountryQuizInput(
            country_ids=country_ids,
            questions_per_game=mode.questions_per_game,
            options_per_question=6,
        )
    ).rounds
    if not rounds:
        await bot.send_message(
            chat_id,
            "Недостаточно стран для викторины (нужно минимум 6).",
        )
        return

    steps = [(r.country_id, list(r.option_country_ids)) for r in rounds]
    session_id = await game_repository.create_country_session_with_steps(
        player_id=player_id,
        mode_id=mode.id,
        steps=steps,
    )
    await bot.send_message(
        chat_id,
        f"Режим: {mode.title}\nВопросов: {len(steps)}. Удачи!",
    )
    await _send_quiz_question(bot, chat_id, session_id, 0, mode.mode_type, by_id)


async def _send_training_card(bot, chat_id: int, session_id: int, step: int) -> None:
    step_row = await game_repository.get_country_step(session_id, step)
    if not step_row:
        await bot.send_message(chat_id, "Внутренняя ошибка: страна не найдена.")
        return

    country = await game_repository.get_country(step_row.country_id)
    if not country:
        await bot.send_message(chat_id, "Ошибка загрузки страны.")
        return

    try:
        flag = iso2_to_flag_emoji(country.iso2)
    except ValueError:
        logger.warning("Country %s has invalid iso2=%r", country.id, country.iso2)
        flag = ""

    caption = format_country_card(
        name_ru=country.name_ru,
        capital_ru=country.capital_ru,
        area_km2=country.area_km2,
        population=country.population,
        flag=flag,
    )
    kb = _training_keyboard(session_id, step)

    flag_photo, flag_is_upload = await _load_photo(
        country.flag_image_url, country.flag_image_file_id
    )
    if flag_photo is not None:
        try:
            sent_flag = await bot.send_photo(chat_id, photo=flag_photo)
            if flag_is_upload and sent_flag.photo:
                await game_repository.set_country_flag_file_id(
                    country.id, sent_flag.photo[-1].file_id
                )
        except TelegramBadRequest as exc:
            logger.warning("Failed to send flag photo country_id=%s: %s", country.id, exc)

    map_photo, map_is_upload = await _load_photo(
        country.map_image_url, country.map_image_file_id
    )
    try:
        if map_photo is not None:
            sent_map = await bot.send_photo(
                chat_id,
                photo=map_photo,
                caption=caption[:1024],
                reply_markup=kb,
            )
            if map_is_upload and sent_map.photo:
                await game_repository.set_country_map_file_id(
                    country.id, sent_map.photo[-1].file_id
                )
            return
    except TelegramBadRequest as exc:
        logger.warning("Failed to send map photo country_id=%s: %s", country.id, exc)

    await bot.send_message(chat_id, text=caption, reply_markup=kb)


async def _send_quiz_question(
    bot,
    chat_id: int,
    session_id: int,
    step: int,
    mode_type: str,
    countries_by_id: dict[int, GameCountryRow] | None = None,
) -> None:
    step_row = await game_repository.get_country_step(session_id, step)
    if not step_row:
        await bot.send_message(chat_id, "Внутренняя ошибка: вопрос не найден.")
        return

    if countries_by_id is None:
        need_ids = [step_row.country_id, *step_row.option_country_ids]
        countries_by_id = await game_repository.get_countries_by_ids(need_ids)

    country = countries_by_id.get(step_row.country_id)
    if not country:
        country = await game_repository.get_country(step_row.country_id)
    if not country:
        await bot.send_message(chat_id, "Ошибка загрузки вопроса.")
        return

    options: list[GameCountryRow] = []
    missing = [cid for cid in step_row.option_country_ids if cid not in countries_by_id]
    if missing:
        countries_by_id.update(await game_repository.get_countries_by_ids(missing))
    for cid in step_row.option_country_ids:
        opt = countries_by_id.get(cid)
        if opt:
            options.append(opt)
    if len(options) != 6:
        await bot.send_message(chat_id, "Ошибка загрузки вариантов ответа.")
        return

    use_map = mode_type == "country_map"
    image_url = country.map_image_url if use_map else country.flag_image_url
    image_file_id = country.map_image_file_id if use_map else country.flag_image_file_id
    caption = "Какая это страна?"
    kb = _quiz_keyboard(session_id, step, options)

    photo, is_upload = await _load_photo(image_url, image_file_id)
    try:
        if photo is not None:
            sent = await bot.send_photo(
                chat_id,
                photo=photo,
                caption=caption,
                reply_markup=kb,
            )
            if is_upload and sent.photo:
                file_id = sent.photo[-1].file_id
                if use_map:
                    await game_repository.set_country_map_file_id(country.id, file_id)
                else:
                    await game_repository.set_country_flag_file_id(country.id, file_id)
            return
    except TelegramBadRequest as exc:
        logger.warning(
            "Failed to send country quiz photo country_id=%s: %s",
            country.id,
            exc,
        )

    await bot.send_message(chat_id, text=caption, reply_markup=kb)


@country_router.callback_query(F.data.startswith("cn|"))
async def cb_training_next(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return
    try:
        session_id = int(parts[1])
        step_index = int(parts[2])
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
        await query.answer("Сессия уже завершена", show_alert=True)
        return

    if sess.current_step != step_index:
        await query.answer("Устаревшая карточка", show_alert=True)
        return

    result = await game_repository.advance_country_training_step(session_id)
    if result.get("error"):
        await query.answer(str(result.get("error")), show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot
    if result.get("session_completed"):
        await query.message.answer("Страны закончились.")
        from bots.game_handlers import _reply_main_menu

        await _reply_main_menu(
            bot,
            query.message.chat.id,
            game_bot_id=game_bot_id,
            telegram_user_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
        )
        return

    next_step = int(result.get("current_step", 0))
    await _send_training_card(bot, query.message.chat.id, session_id, next_step)


@country_router.callback_query(F.data.startswith("ca|"))
async def cb_country_answer(query: CallbackQuery) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 4:
        await query.answer("Ошибка данных", show_alert=True)
        return
    try:
        session_id = int(parts[1])
        step_index = int(parts[2])
        selected_country_id = int(parts[3])
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

    mode = await game_repository.get_mode(sess.mode_id)
    if not mode or mode.mode_type not in {"country_flags", "country_map"}:
        await query.answer("Режим недоступен", show_alert=True)
        return

    result = await game_repository.submit_country_answer_and_advance(
        session_id=session_id,
        step_index=step_index,
        selected_country_id=selected_country_id,
    )

    if result.get("error") == "wrong_step":
        await query.answer("Устаревший вопрос", show_alert=True)
        return

    if result.get("duplicate"):
        await query.answer("Вы уже ответили на этот вопрос.", show_alert=True)
        return

    if result.get("error"):
        await query.answer(str(result.get("error")), show_alert=True)
        return

    is_correct = bool(result.get("is_correct"))
    await query.answer("Верно!" if is_correct else "Неверно.", show_alert=False)

    correct_id = int(result.get("correct_country_id", 0))
    correct_country = await game_repository.get_country(correct_id)
    correct_name = correct_country.name_ru if correct_country else "—"
    if is_correct:
        feedback = f"✅ Верно!\nПравильный ответ: {correct_name}"
    else:
        selected = await game_repository.get_country(selected_country_id)
        selected_name = selected.name_ru if selected else "—"
        feedback = (
            f"❌ Неверно.\n"
            f"Ваш ответ: {selected_name}\n"
            f"Правильный ответ: {correct_name}"
        )
    await query.message.answer(feedback)

    bot = query.bot or query.message.bot
    if result.get("session_completed"):
        score = int(result.get("score", 0))
        correct = int(result.get("correct_count", 0))
        total = int(result.get("total_questions", 0))
        await query.message.answer(
            f"🎉 Игра окончена!\n"
            f"Верных ответов: {correct} из {total}\n"
            f"Очки: {score}\n\n"
            f"/rating — таблица рейтинга\n"
            f"/start — новая игра",
        )
        return

    next_step = int(result.get("current_step", 0))
    await _send_quiz_question(
        bot,
        query.message.chat.id,
        session_id,
        next_step,
        mode.mode_type,
    )
