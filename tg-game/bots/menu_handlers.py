"""Хендлеры иерархического меню (режим mode_type=menu)."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.cart_repository import CartItemRow, cart_repository
from services.game_repository import GameModeRow, game_repository
from services.media_storage import extract_media_filename, fetch_media_bytes
from services.menu_repository import GameMenuNodeRow, GameMenuNodeView, menu_repository
from services.order_repository import order_repository

logger = logging.getLogger(__name__)

menu_router = Router(name="game_menu")


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


def _format_cart_text(items: list[CartItemRow]) -> str:
    if not items:
        return "🛒 Корзина пуста."
    lines = ["🛒 Корзина", "─" * 20, ""]
    total_qty = 0
    total_amount = Decimal("0")
    for idx, item in enumerate(items, start=1):
        line_total = item.line_total
        total_qty += item.quantity
        total_amount += line_total
        lines.append(
            f"{idx}. {item.title}\n"
            f"   {item.quantity} × {_format_price(item.unit_price)} = {_format_price(line_total)}"
        )
    lines.extend(["", "─" * 20, f"Позиций: {total_qty}", f"Итого: {_format_price(total_amount)}"])
    return "\n".join(lines)[:4096]


def _format_order_text(order_number: str, items: list[dict], total_amount: float) -> str:
    lines = [f"✅ Заказ {order_number}", "─" * 20, ""]
    for idx, item in enumerate(items, start=1):
        unit_price = item.get("unit_price", 0)
        line_total = item.get("line_total", unit_price * item["quantity"])
        lines.append(
            f"{idx}. {item['title']}\n"
            f"   {item['quantity']} × {_format_price(unit_price)} = {_format_price(line_total)}"
        )
    lines.extend(["", "─" * 20, f"Итого: {_format_price(total_amount)}"])
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
) -> list[list[InlineKeyboardButton]]:
    ctx = _ctx_marker(parent_id)
    back_parent = ctx
    return [
        [
            InlineKeyboardButton(
                text=_cart_button_label(cart_total)[:64],
                callback_data=f"cv|{mode_id}|{ctx}",
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"mb|{mode_id}|{back_parent}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="home|0",
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
    rows.extend(_nav_footer_rows(mode_id, parent_id, cart_total))
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


def _cart_keyboard(mode_id: int, ctx: int, has_items: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_items:
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
        header = mode.title
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
        empty_kb = InlineKeyboardMarkup(
            inline_keyboard=_nav_footer_rows(mode_id, parent_id, cart_total)
        )
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


async def _send_cart(
    bot,
    chat_id: int,
    mode_id: int,
    ctx: int,
    *,
    game_bot_id: int,
    telegram_user_id: int,
) -> None:
    items = await cart_repository.list_items(
        bot_id=game_bot_id,
        telegram_user_id=telegram_user_id,
        mode_id=mode_id,
    )
    text = _format_cart_text(items)
    kb = _cart_keyboard(mode_id, ctx, has_items=len(items) > 0)
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
            header_override=node.body_text or node.title,
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
        await query.answer("Ошибка данных", show_alert=True)
        return

    if not await _validate_menu_mode(mode_id, game_bot_id):
        await query.answer("Раздел недоступен", show_alert=True)
        return

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

    result = await order_repository.checkout(
        bot_id=game_bot_id,
        telegram_user_id=query.from_user.id,
        mode_id=mode_id,
        username=query.from_user.username,
        first_name=query.from_user.first_name,
    )
    if not result:
        await query.answer("Корзина пуста", show_alert=True)
        return

    await query.answer()
    bot = query.bot or query.message.bot
    text = _format_order_text(
        result["order_number"],
        result["items"],
        result["total_amount"],
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
