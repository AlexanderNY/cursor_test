"""Состав стола заказов и правила корзины (без I/O)."""

from __future__ import annotations

from dataclasses import dataclass

ORDER_DESK_CODE = "order_desk"
ORDER_DESK_TITLE = "Стол заказов"

PAYMENT_METHODS: tuple[tuple[str, str], ...] = (
    ("cash", "Наличные"),
    ("card", "Карта"),
    ("transfer", "Перевод"),
)


@dataclass(frozen=True, slots=True)
class DeskProduct:
    title: str
    description: str
    price_rub: int


@dataclass(frozen=True, slots=True)
class DeskCategory:
    title: str
    description: str
    products: tuple[DeskProduct, ...]


def payment_label(code: str | None) -> str:
    if not code:
        return "не выбрана"
    for method_code, label in PAYMENT_METHODS:
        if method_code == code:
            return label
    return code


def is_payment_method(code: str | None) -> bool:
    return any(method_code == code for method_code, _label in PAYMENT_METHODS)


def next_quantity(current: int, delta: int) -> int:
    """Новое количество позиции. Ноль значит строку нужно убрать из корзины."""
    base = current if current > 0 else 0
    updated = base + delta
    if updated < 0:
        return 0
    return updated


def _products(rows: list[tuple[str, str, int]]) -> tuple[DeskProduct, ...]:
    return tuple(DeskProduct(title=title, description=body, price_rub=price) for title, body, price in rows)


def order_desk_categories() -> tuple[DeskCategory, ...]:
    """Три категории, в каждой десять товаров."""
    return (
        DeskCategory(
            title="Категория 1",
            description="Горячие напитки",
            products=_products(
                [
                    ("Эспрессо", "Двойной эспрессо, 60 мл", 120),
                    ("Американо", "Эспрессо и горячая вода, 200 мл", 140),
                    ("Капучино", "Эспрессо и молочная пенка, 250 мл", 180),
                    ("Латте", "Эспрессо и молоко, 300 мл", 190),
                    ("Раф", "Сливки и ваниль, 300 мл", 210),
                    ("Какао", "Какао на молоке, 300 мл", 160),
                    ("Чай чёрный", "Ассам, 400 мл", 100),
                    ("Чай зелёный", "Сенча, 400 мл", 100),
                    ("Матча", "Японский чай на молоке, 300 мл", 220),
                    ("Горячий шоколад", "Тёмный шоколад, 250 мл", 200),
                ]
            ),
        ),
        DeskCategory(
            title="Категория 2",
            description="Основные блюда",
            products=_products(
                [
                    ("Борщ", "Со сметаной, 350 г", 280),
                    ("Куриный суп", "Лапша и курица, 350 г", 240),
                    ("Цезарь", "Курица, салат, соус, 250 г", 320),
                    ("Греческий салат", "Овощи и сыр, 250 г", 290),
                    ("Паста карбонара", "Бекон и сливочный соус, 300 г", 360),
                    ("Паста с курицей", "Сливочный соус, 300 г", 340),
                    ("Стейк", "Говядина, прожарка medium, 200 г", 690),
                    ("Курица гриль", "С овощами, 250 г", 390),
                    ("Бургер", "Говядина, сыр, булочка", 350),
                    ("Рис с овощами", "Овощи на пару, 300 г", 260),
                ]
            ),
        ),
        DeskCategory(
            title="Категория 3",
            description="Десерты",
            products=_products(
                [
                    ("Чизкейк", "Нью-Йорк, 120 г", 250),
                    ("Тирамису", "Классический, 120 г", 270),
                    ("Наполеон", "Слоёный, 130 г", 220),
                    ("Медовик", "Со сметанным кремом, 130 г", 220),
                    ("Брауни", "Шоколадный, 100 г", 190),
                    ("Маффин", "Черничный, 90 г", 160),
                    ("Эклер", "Заварной, 80 г", 150),
                    ("Мороженое", "Ваниль, 100 г", 140),
                    ("Панкейки", "Три штуки, с сиропом", 240),
                    ("Фруктовый салат", "Сезонные фрукты, 200 г", 210),
                ]
            ),
        ),
    )
