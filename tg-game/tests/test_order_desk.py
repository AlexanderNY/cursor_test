"""Каталог стола заказов и подписи оплаты."""

from services.order_desk import (
    is_payment_method,
    next_quantity,
    order_desk_categories,
    payment_label,
)


def test_order_desk_has_three_categories_of_ten_products() -> None:
    categories = order_desk_categories()
    assert [category.title for category in categories] == [
        "Категория 1",
        "Категория 2",
        "Категория 3",
    ]
    for category in categories:
        assert len(category.products) == 10
        titles = [product.title for product in category.products]
        assert len(set(titles)) == 10
        assert all(product.price_rub > 0 for product in category.products)


def test_payment_labels() -> None:
    assert payment_label(None) == "не выбрана"
    assert payment_label("cash") == "Наличные"
    assert payment_label("card") == "Карта"
    assert payment_label("transfer") == "Перевод"
    assert payment_label("wire") == "wire"
    assert is_payment_method("card")
    assert not is_payment_method("wire")
    assert not is_payment_method(None)


def test_next_quantity_clamps_at_zero() -> None:
    assert next_quantity(1, 1) == 2
    assert next_quantity(1, -1) == 0
    assert next_quantity(2, -5) == 0
    assert next_quantity(0, -1) == 0
    assert next_quantity(-3, 1) == 1
