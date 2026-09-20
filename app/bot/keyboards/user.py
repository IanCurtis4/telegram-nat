from __future__ import annotations

from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Catálogo", callback_data="catalog")
    builder.button(text="📦 Minhas compras", callback_data="my_purchases")
    builder.button(text="📃 Termos", callback_data="terms")
    builder.button(text="🔒 Privacidade", callback_data="privacy")
    builder.button(text="🆘 Suporte", callback_data="support")
    builder.adjust(2)
    return builder


def catalog_keyboard(product_ids: list[int]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for product_id in product_ids:
        builder.button(text=f"Comprar — {product_id} ⭐", callback_data=f"buy_product:{product_id}")
    builder.button(text="🔙 Voltar ao menu", callback_data="main_menu")
    builder.adjust(1)
    return builder


def catalog_product_keyboard(product_id: int, price_stars: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Comprar — {price_stars} ⭐", callback_data=f"buy_product:{product_id}")
    builder.button(text="⬅️ Voltar ao catálogo", callback_data="catalog")
    builder.adjust(1)
    return builder


def product_preview_keyboard(product_id: int, price_stars: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Pagar {price_stars} ⭐", callback_data=f"buy_product:{product_id}")
    builder.button(text="⬅️ Voltar ao catálogo", callback_data="catalog")
    builder.adjust(1)
    return builder
