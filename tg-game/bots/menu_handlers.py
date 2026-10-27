"""Хендлеры иерархического меню (режим mode_type=menu)."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from aiogram import BaseMiddleware, F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from services.cart_repository import CartItemRow, cart_repository
from services.game_repository import GameModeRow, game_repository
from services.media_storage import extract_media_filename, fetch_media_bytes
from services.menu_repository import GameMenuNodeRow, GameMenuNodeView, menu_repository
from services.order_desk import PAYMENT_METHODS, payment_label
from services.order_repository import order_repository
from services.profile_repository import profile_repository

logger = logging.getLogger(__name__)

menu_router = Router(name="game_menu")


class OrderDeskStates(StatesGroup):
    waiting_address = State()


class _LeaveAddressPromptMiddleware(BaseMiddleware):
    """Любая кнопка, кроме ввода адреса, выходит из ожидания текста адреса."""

    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery):
            payload = event.data or ""
            if not payload.startswith("pa|") and not payload.startswith("px|"):
                state: FSMContext | None = data.get("state")
                if state is not None and await state.get_state() == OrderDeskStates.waiting_address.state:
                    await state.clear()
        return await handler(event, data)


menu_router.callback_query.middleware(_LeaveAddressPromptMiddleware())


def _ctx_marker(parent_id: int | None) -> int:
    return 0 if parent_id is None else parent_id


def _cart_button_label(cart_total: int) -> str:
    if cart_total > 0:
        return f"🛒 Корзина ({cart_total})"
    return "🛒 Корзина"


def _format_price(price: Decimal | float) -> str:
    value = Decimal(str(price))
    if value == value.to_integral_value():
        return f"{int(value)} ₽"
    return f"{value:.2f} ₽"


async def _load_node_photo(node: GameMenuNodeRow) -> BufferedInputFile | None:
    filename = extract_media_filename(node.image_url)
    if not filename:
        return None
    result = await fetch_media_bytes(filename)
    if not result:
        return None
    body, _content_type = result
    return BufferedInputFile(body, filename=filename)


async def _send_with_node_photo(
    bot,
    chat_id: int,
    node: GameMenuNodeRow | None,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    max_caption_len: int = 1024,
    max_message_len: int = 4096,
) -> None:
    caption = text[:max_caption_len]
    if node:
        try:
            if node.image_file_id:
                await bot.send_photo(
                    chat_id,
                    photo=node.image_file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                )
                return
            photo_file = await _load_node_photo(node)
            if photo_file:
                sent = await bot.send_photo(
                    chat_id,
                    photo=photo_file,
                    caption=caption,
                    reply_markup=reply_markup,
                )
                if sent.photo:
                    await menu_repository.set_node_image_file_id(node.id, sent.photo[-1].file_id)
                return
        except TelegramBadRequest as exc:
            logger.warning(
                "Failed to send menu photo node_id=%s: %s",
                node.id,
                exc,
            )
    await bot.send_message(chat_id, text[:max_message_len], reply_markup=reply_markup)


def _format_cart_text(
    items: list[CartItemRow],
    *,
    address: str,
    payment_code: str | None,
) -> str:
    address_line = address.strip() if address.strip() else "не указан — откройте профиль"
    lines = [
        "🛒 Корзина",
        f"Адрес: {address_line}",
        f"Оплата: {payment_label(payment_code)}",
        "─" * 20,
    ]
    if not items:
        lines.append("")
        lines.append("Корзина пуста. Выберите товар в категории.")
        return "\n".join(lines)[:4096]
    total_qty = 0
    total_amount = Decimal("0")
    lines.append("")
    for idx, item in enumerate(items, start=1):
        line_total = item.line_total
        total_qty += item.quantity
        total_amount += line_total
        lines.append(
            f"{idx}. {item.title}\n"
            f"   {item.quantity} × {_format_price(item.unit_price)} = {_format_price(line_total)}"
        )
    lines.extend(
        [
            "",
            "─" * 20,
            f"Позиций: {total_qty}",
            f"Итого: {_format_price(total_amount)}",
            "",
            "Кнопки ➖ и ➕ меняют количество, ✕ убирает позицию.",
        ]
    )
    return "\n".join(lines)[:4096]


def _format_order_text(
    order_number: str,
    items: list[dict],
    total_amount: float,
    *,
    address: str,
    payment_code: str | None,
) -> str:
    lines = [f"✅ Заказ {order_number}", "─" * 20, ""]
    for idx, item in enumerate(items, start=1):
        unit_price = item.get("unit_price", 0)
        line_total = item.get("line_total", unit_price * item["quantity"])
        lines.append(
            f"{idx}. {item['title']}\n"
            f"   {item['quantity']} × {_format_price(unit_price)} = {_format_price(line_total)}"
        )
    lines.extend(
        [
            "",
            "─" * 20,
            f"Итого: {_format_price(total_amount)}",
            f"Адрес: {address.strip() or '—'}",
            f"Оплата: {payment_label(payment_code)}",
        ]
    )
    return "\n".join(lines)[:4096]


async def _get_cart_total(game_bot_id: int, telegram_user_id: int, mode_id: int) -> int:
    return await cart_repository.get_cart_total(
        bot_id=game_bot_id,
        telegram_user_id=telegram_user_id,
        mode_id=mode_id,
    )


def _nav_footer_rows(
    mode_id: int,
    parent_id: int | None,
    cart_total: int,
    *,
    include_cart: bool = True,
) -> list[list[InlineKeyboardButton]]:
    ctx = _ctx_marker(parent_id)
    back_parent = ctx
    rows: list[list[InlineKeyboardButton]] = []
    if include_cart:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_cart_button_label(cart_total)[:64],
                    callback_data=f"cv|{mode_id}|{ctx}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"mb|{mode_id}|{back_parent}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="home|0",
            )
        ]
    )
    return rows


def _desk_action_rows(mode_id: int, cart_total: int) -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                text="Профиль",
                callback_data=f"pf|{mode_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text=_cart_button_label(cart_total)[:64],
                callback_data=f"cv|{mode_id}|0",
            )
        ],
    ]


def _menu_keyboard(
    mode_id: int,
    parent_id: int | None,
    node_views: list[GameMenuNodeView],
    cart_total: int,
) -> InlineKeyboardMarkup:
    ctx = _ctx_marker(parent_id)
    rows: list[list[InlineKeyboardButton]] = []
    for nv in node_views:
        node = nv.node
        if nv.has_children:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"▶ {node.title[:40]}",
                        callback_data=f"mo|{mode_id}|{node.id}",
                    )
                ]
            )
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=node.title[:35],
                    callback_data=f"mo|{mode_id}|{node.id}",
                ),
                InlineKeyboardButton(
                    text="➕",
                    callback_data=f"ca|{mode_id}|{node.id}|{ctx}",
                ),
            ]
        )
    if parent_id is None:
        rows.extend(_desk_action_rows(mode_id, cart_total))
    rows.extend(_nav_footer_rows(mode_id, parent_id, cart_total, include_cart=parent_id is not None))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _leaf_keyboard(
    mode_id: int,
    node_id: int,
    parent_id: int | None,
    cart_total: int,
    *,
    can_add: bool = True,
) -> InlineKeyboardMarkup:
    ctx = _ctx_marker(parent_id)
    rows: list[list[InlineKeyboardButton]] = []
    if can_add:
        rows.append(
            [
                InlineKeyboardButton(
                    text="➕ В заказ",
                    callback_data=f"ca|{mode_id}|{node_id}|{ctx}",
                )
            ]
        )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text=_cart_button_label(cart_total)[:64],
                    callback_data=f"cv|{mode_id}|{ctx}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"ml|{mode_id}|{ctx}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В главное меню",
                    callback_data="home|0",
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _cart_keyboard(
    mode_id: int,
    ctx: int,
    items: list[CartItemRow],
    payment_code: str | None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in items:
        short_title = item.title[:18]
        rows.append(
            [
                InlineKeyboardButton(
                    text="➖",
                    callback_data=f"ci|{mode_id}|{item.node_id}|m|{ctx}",
                ),
                InlineKeyboardButton(
                    text="➕",
                    callback_data=f"ci|{mode_id}|{item.node_id}|p|{ctx}",
                ),
                InlineKeyboardButton(
                    text=f"✕ {short_title}"[:64],
                    callback_data=f"cd|{mode_id}|{item.node_id}|{ctx}",
                ),
            ]
        )
    payment_row: list[InlineKeyboardButton] = []
    for code, label in PAYMENT_METHODS:
        title = f"✓ {label}" if code == payment_code else label
        payment_row.append(
            InlineKeyboardButton(
                text=title[:64],
                callback_data=f"py|{mode_id}|{ctx}|{code}",
            )
        )
    rows.append(payment_row)
    rows.append(
        [
            InlineKeyboardButton(
                text="Профиль",
                callback_data=f"pf|{mode_id}",
            )
        ]
    )
    if items:
        rows.append(
            [
                InlineKeyboardButton(
                    text="✅ Оформить",
                    callback_data=f"cf|{mode_id}|{ctx}",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="🗑 Сбросить всё",
                    callback_data=f"cc|{mode_id}|{ctx}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"ml|{mode_id}|{ctx}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="home|0",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _validate_menu_mode(mode_id: int, game_bot_id: int) -> Optional[GameModeRow]:
    mode = await game_repository.get_mode(mode_id)
    if not mode or not mode.is_active or mode.bot_id != game_bot_id or mode.mode_type != "menu":
        return None
    return mode


async def _send_menu_level(
    bot,
    chat_id: int,
    mode_id: int,
    parent_id: int | None,
    *,
    game_bot_id: int,
    telegram_user_id: int,
    header_override: str | None = None,
    category_node: GameMenuNodeRow | None = None,
) -> None:
    mode = await game_repository.get_mode(mode_id)
    if not mode:
        await bot.send_message(chat_id, "Режим не найден.")
        return

    cart_total = await _get_cart_total(game_bot_id, telegram_user_id, mode_id)
    node_views = await menu_repository.list_children_views(mode_id, parent_id)

    if parent_id is None:
        header = f"{mode.title}\n\nВыберите категорию, профиль или корзину."
        category_node = None
    else:
        if category_node is None:
            category_node = await menu_repository.get_node(parent_id)
        if header_override:
            header = header_override
        elif category_node:
            header = category_node.body_text or category_node.title
        else:
            header = mode.title

    if not node_views:
        empty_rows = _nav_footer_rows(
            mode_id,
            parent_id,
            cart_total,
            include_cart=parent_id is not None,
        )
        if parent_id is None:
            empty_rows = _desk_action_rows(mode_id, cart_total) + empty_rows
        empty_kb = InlineKeyboardMarkup(inline_keyboard=empty_rows)
        await _send_with_node_photo(
            bot,
            chat_id,
            category_node,
            f"{header}\n\nВ этом разделе пока нет пунктов.",
            empty_kb,
        )
        return

    text = header.strip()
    kb = _menu_keyboard(mode_id, parent_id, node_views, cart_total)
    await _send_with_node_photo(bot, chat_id, category_node, text, kb)


async def _send_leaf(
    bot,
    chat_id: int,
    node: GameMenuNodeRow,
    *,
    game_bot_id: int,
    telegram_user_id: int,
) -> None:
    parts = [node.title]
    if node.body_text:
        parts.append(node.body_text.strip())
    if await menu_repository.is_orderable_leaf(node.id):
        parts.append(_format_price(node.price))
    else:
        parts.append("(раздел — выберите позицию ниже)")
    text = "\n\n".join(parts)[:1024]
    cart_total = await _get_cart_total(game_bot_id, telegram_user_id, node.mode_id)
    can_add = await menu_repository.is_orderable_leaf(node.id)
    kb = _leaf_keyboard(node.mode_id, node.id, node.parent_id, cart_total, can_add=can_add)
    await _send_with_node_photo(bot, chat_id, node, text, kb)


async def _send_profile(
    bot,
    chat_id: int,
    mode_id: int,
    *,
    game_bot_id: int,
    telegram_user_id: int,
) -> None:
    address = await profile_repository.get_address(bot_id=game_bot_id, telegram_user_id=telegram_user_id)
    shown = address if address else "не указан"
    text = f"Профиль\n\nАдрес доставки:\n{shown}"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Указать адрес",
                    callback_data=f"pa|{mode_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Корзина",
                    callback_data=f"cv|{mode_id}|0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В меню",
                    callback_data=f"ml|{mode_id}|0",
                )
            ],
        ]
    )
    await bot.send_message(chat_id, text[:4096], reply_markup=kb)


async def _send_cart(
    bot,
    chat_id: int,
    mode_id: int,
    ctx: int,
    *,
    game_bot_id: int,
    telegram_user_id: int,
    edit_message=None,
) -> None:
    items = await cart_repository.list_items(
        bot_id=game_bot_id,
        telegram_user_id=telegram_user_id,
        mode_id=mode_id,
    )
    address = await profile_repository.get_address(bot_id=game_bot_id, telegram_user_id=telegram_user_id)
    payment_code = await cart_repository.get_payment_method(
        bot_id=game_bot_id,
        telegram_user_id=telegram_user_id,
        mode_id=mode_id,
    )
    text = _format_cart_text(items, address=address, payment_code=payment_code)
    kb = _cart_keyboard(mode_id, ctx, items, payment_code)
    if edit_message is not None:
        try:
            await edit_message.edit_text(text, reply_markup=kb)
            return
        except TelegramBadRequest:
            logger.debug("Cart message was not edited; sending a new one.")
    await bot.send_message(chat_id, text, reply_markup=kb)


async def start_menu_mode(
    bot,
    chat_id: int,
    mode_id: int,
    *,
    game_bot_id: int,
    telegram_user_id: int,
) -> None:
    await _send_menu_level(
        bot,
        chat_id,
        mode_id,
        parent_id=None,
        game_bot_id=game_bot_id,
        telegram_user_id=telegram_user_id,
    )


@menu_router.callback_query(F.data.startswith("ml|"))
async def cb_menu_level(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        parent_marker = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot
    parent_id = None if parent_marker == 0 else parent_marker
    await _send_menu_level(
        bot,
        query.message.chat.id,
        mode_id,
        parent_id,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.callback_query(F.data.startswith("mo|"))
async def cb_menu_open_node(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        node_id = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return

    node = await menu_repository.get_node(node_id)
    if not node or node.mode_id != mode_id or not node.is_active:
        await query.answer("Пункт не найден", show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot
    if await menu_repository.has_children(node_id, active_only=True):
        await _send_menu_level(
            bot,
            query.message.chat.id,
            mode_id,
            node_id,
            game_bot_id=game_bot_id,
            telegram_user_id=query.from_user.id,
            header_override=(
                f"{node.title}\n\n{node.body_text.strip()}"
                if node.body_text and node.body_text.strip()
                else node.title
            ),
            category_node=node,
        )
        return

    await _send_leaf(
        bot,
        query.message.chat.id,
        node,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.callback_query(F.data.startswith("mb|"))
async def cb_menu_back(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        current_parent = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    mode = await game_repository.get_mode(mode_id)
    if not mode or mode.bot_id != game_bot_id or mode.mode_type != "menu":
        await query.answer("Раздел недоступен", show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot

    if current_parent == 0:
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

    node = await menu_repository.get_node(current_parent)
    if not node:
        await start_menu_mode(
            bot,
            query.message.chat.id,
            mode_id,
            game_bot_id=game_bot_id,
            telegram_user_id=query.from_user.id,
        )
        return

    up_parent = node.parent_id
    await _send_menu_level(
        bot,
        query.message.chat.id,
        mode_id,
        up_parent,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.callback_query(F.data.startswith("ca|"))
async def cb_cart_add(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 4:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        node_id = int(parts[2])
    except ValueError:
        raise SkipHandler() from None

    if not await _validate_menu_mode(mode_id, game_bot_id):
        raise SkipHandler()

    node = await menu_repository.get_node(node_id)
    if not node or node.mode_id != mode_id or not node.is_active:
        await query.answer("Пункт не найден", show_alert=True)
        return

    if not await menu_repository.is_orderable_leaf(node_id):
        await query.answer("Раздел нельзя добавить в заказ", show_alert=True)
        return

    try:
        total = await cart_repository.add_item(
            bot_id=game_bot_id,
            telegram_user_id=query.from_user.id,
            mode_id=mode_id,
            node_id=node_id,
        )
    except ValueError as exc:
        await query.answer(str(exc), show_alert=True)
        return
    await query.answer(f"Добавлено: {node.title[:30]} (в корзине: {total})")


@menu_router.callback_query(F.data.startswith("cv|"))
async def cb_cart_view(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        ctx = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot
    await _send_cart(
        bot,
        query.message.chat.id,
        mode_id,
        ctx,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.callback_query(F.data.startswith("cc|"))
async def cb_cart_clear(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        ctx = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return

    await cart_repository.clear_cart(
        bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        mode_id=mode_id,
    )
    await query.answer("Корзина очищена")
    bot = query.bot or query.message.bot
    await _send_cart(
        bot,
        query.message.chat.id,
        mode_id,
        ctx,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.callback_query(F.data.startswith("cf|"))
async def cb_cart_checkout(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    parts = (query.data or "").split("|")
    if len(parts) != 3:
        await query.answer("Ошибка данных", show_alert=True)
        return

    try:
        mode_id = int(parts[1])
        ctx = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return

    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return

    address = await profile_repository.get_address(
        bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )
    payment_code = await cart_repository.get_payment_method(
        bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        mode_id=mode_id,
    )
    try:
        result = await order_repository.checkout(
            bot_id=game_bot_id,
            telegram_user_id=query.from_user.id,
            mode_id=mode_id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            delivery_address=address,
            payment_method=payment_code or "",
        )
    except ValueError as exc:
        await query.answer(str(exc), show_alert=True)
        return
    if not result:
        await query.answer("Корзина пуста", show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot
    text = _format_order_text(
        result["order_number"],
        result["items"],
        result["total_amount"],
        address=str(result.get("delivery_address") or address),
        payment_code=result.get("payment_method"),
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ В меню",
                    callback_data=f"ml|{mode_id}|{ctx}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В главное меню",
                    callback_data="home|0",
                )
            ],
        ]
    )
    await bot.send_message(query.message.chat.id, text, reply_markup=kb)


@menu_router.callback_query(F.data == "home|0")
async def cb_menu_home(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return

    await query.answer()
    from bots.game_handlers import _reply_main_menu

    bot = query.bot or query.message.bot
    await _reply_main_menu(
        bot,
        query.message.chat.id,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        username=query.from_user.username,
        first_name=query.from_user.first_name,
    )


def _parse_mode_id(query: CallbackQuery, expected_parts: int) -> int | None:
    parts = (query.data or "").split("|")
    if len(parts) != expected_parts:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


@menu_router.callback_query(F.data.startswith("pf|"))
async def cb_profile(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return
    mode_id = _parse_mode_id(query, 2)
    if mode_id is None:
        await query.answer("Ошибка данных", show_alert=True)
        return
    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return
    await query.answer()
    bot = query.bot or query.message.bot
    await _send_profile(
        bot,
        query.message.chat.id,
        mode_id,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.callback_query(F.data.startswith("pa|"))
async def cb_profile_address(query: CallbackQuery, game_bot_id: int, state: FSMContext) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return
    mode_id = _parse_mode_id(query, 2)
    if mode_id is None:
        await query.answer("Ошибка данных", show_alert=True)
        return
    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return
    await state.set_state(OrderDeskStates.waiting_address)
    await state.update_data(mode_id=mode_id)
    await query.answer()
    bot = query.bot or query.message.bot
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=f"px|{mode_id}",
                )
            ]
        ]
    )
    await bot.send_message(
        query.message.chat.id,
        "Напишите адрес доставки одним сообщением: город, улица, дом, квартира.",
        reply_markup=kb,
    )


@menu_router.callback_query(F.data.startswith("px|"))
async def cb_profile_address_cancel(query: CallbackQuery, game_bot_id: int, state: FSMContext) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return
    mode_id = _parse_mode_id(query, 2)
    await state.clear()
    if mode_id is None or not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Ввод адреса отменён")
        return
    await query.answer("Ввод адреса отменён")
    bot = query.bot or query.message.bot
    await _send_profile(
        bot,
        query.message.chat.id,
        mode_id,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
    )


@menu_router.message(OrderDeskStates.waiting_address, F.text)
async def on_delivery_address(message: Message, state: FSMContext, game_bot_id: int) -> None:
    if not message.from_user:
        return
    text = (message.text or "").strip()
    if text.startswith("/"):
        await state.clear()
        raise SkipHandler()
    if len(text) < 5:
        await message.answer("Адрес слишком короткий. Напишите город, улицу и дом.")
        return
    if len(text) > 500:
        await message.answer("Адрес длиннее 500 символов. Сократите его.")
        return
    data = await state.get_data()
    mode_id = int(data.get("mode_id") or 0)
    await profile_repository.set_address(
        bot_id=game_bot_id,
        telegram_user_id=message.from_user.id,
        address=text,
    )
    await state.clear()
    await message.answer("Адрес сохранён.")
    if mode_id <= 0:
        return
    await _send_profile(
        message.bot,
        message.chat.id,
        mode_id,
        game_bot_id=game_bot_id,
        telegram_user_id=message.from_user.id,
    )


async def _refresh_cart(query: CallbackQuery, game_bot_id: int, mode_id: int, ctx: int) -> None:
    if not query.from_user or not query.message:
        return
    bot = query.bot or query.message.bot
    await _send_cart(
        bot,
        query.message.chat.id,
        mode_id,
        ctx,
        game_bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        edit_message=query.message,
    )


@menu_router.callback_query(F.data.startswith("ci|"))
async def cb_cart_quantity(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return
    parts = (query.data or "").split("|")
    if len(parts) != 5:
        await query.answer("Ошибка данных", show_alert=True)
        return
    try:
        mode_id = int(parts[1])
        node_id = int(parts[2])
        ctx = int(parts[4])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return
    if parts[3] not in {"p", "m"}:
        await query.answer("Ошибка данных", show_alert=True)
        return
    delta = 1 if parts[3] == "p" else -1
    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return
    await cart_repository.change_quantity(
        bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        mode_id=mode_id,
        node_id=node_id,
        delta=delta,
    )
    await query.answer()
    await _refresh_cart(query, game_bot_id, mode_id, ctx)


@menu_router.callback_query(F.data.startswith("cd|"))
async def cb_cart_remove_line(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return
    parts = (query.data or "").split("|")
    if len(parts) != 4:
        await query.answer("Ошибка данных", show_alert=True)
        return
    try:
        mode_id = int(parts[1])
        node_id = int(parts[2])
        ctx = int(parts[3])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return
    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return
    await cart_repository.remove_item(
        bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        mode_id=mode_id,
        node_id=node_id,
    )
    await query.answer("Позиция убрана")
    await _refresh_cart(query, game_bot_id, mode_id, ctx)


@menu_router.callback_query(F.data.startswith("py|"))
async def cb_cart_payment(query: CallbackQuery, game_bot_id: int) -> None:
    if not query.from_user or not query.message:
        await query.answer()
        return
    parts = (query.data or "").split("|")
    if len(parts) != 4:
        await query.answer("Ошибка данных", show_alert=True)
        return
    try:
        mode_id = int(parts[1])
        ctx = int(parts[2])
    except ValueError:
        await query.answer("Ошибка данных", show_alert=True)
        return
    payment_code = parts[3]
    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return
    try:
        await cart_repository.set_payment_method(
            bot_id=game_bot_id,
            telegram_user_id=query.from_user.id,
            mode_id=mode_id,
            payment_method=payment_code,
        )
    except ValueError as exc:
        await query.answer(str(exc), show_alert=True)
        return
    await query.answer(payment_label(payment_code))
    await _refresh_cart(query, game_bot_id, mode_id, ctx)
