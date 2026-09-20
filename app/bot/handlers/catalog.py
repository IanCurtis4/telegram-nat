from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.user import catalog_keyboard, catalog_product_keyboard, main_menu_keyboard
from app.database.session import AsyncSessionLocal
from app.services.catalog import get_active_product, get_active_products
from app.services.payments import send_product_invoice, send_product_paid_media

logger = logging.getLogger(__name__)
router = Router()


async def _render_catalog(message_or_callback: Message | CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        products = await get_active_products(session)

    if not products:
        text = "<b>Catálogo</b>\n\nNo momento não há produtos ativos disponíveis."
        markup = main_menu_keyboard().as_markup()
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text, reply_markup=markup)
        else:
            await message_or_callback.message.edit_text(text, reply_markup=markup)
        return

    text_parts = ["<b>Catálogo</b>", "", "Produtos disponíveis:"]
    buttons = []
    for product in products:
        text_parts.append(f"• <b>{product.name}</b> — {product.price_stars} ⭐")
        text_parts.append(f"  {product.description[:120]}{'...' if len(product.description) > 120 else ''}")
        buttons.append(product.id)

    markup = catalog_keyboard(buttons).as_markup()
    text = "\n".join(text_parts)

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=markup)
    else:
        await message_or_callback.message.edit_text(text, reply_markup=markup)


@router.message(Command("catalog"))
async def catalog_command(message: Message) -> None:
    logger.info("Catalog requested by user %s", message.from_user.id)
    await _render_catalog(message)


@router.callback_query(lambda c: c.data == "catalog")
async def catalog_callback(callback: CallbackQuery) -> None:
    await _render_catalog(callback)


@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery) -> None:
    markup = main_menu_keyboard().as_markup()
    await callback.message.edit_text(
        "<b>Menu principal</b>\n\nEscolha uma opção abaixo.",
        reply_markup=markup,
    )


@router.callback_query(lambda c: c.data and c.data.startswith("buy_product:"))
async def buy_product_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        logger.warning("Buy product callback without from_user context")
        return

    try:
        product_id = int(callback.data.split(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("Produto inválido.", show_alert=True)
        logger.warning("Malformed buy_product callback from user %s: %s", callback.from_user.id, callback.data)
        return

    async with AsyncSessionLocal() as session:
        product = await get_active_product(session, product_id)

    if product is None:
        await callback.answer("Produto indisponível no momento.", show_alert=True)
        return

    if product.media:
        try:
            await send_product_paid_media(callback.bot, callback.from_user.id, product, product.media)
            logger.info("Paid media purchase initiated for product %s by user %s", product.id, callback.from_user.id)
            await callback.answer("Iniciando pagamento do conteúdo selecionado...", show_alert=False)
            return
        except Exception:
            logger.exception("Falling back to invoice for product %s due to paid media failure", product.id)

    try:
        await send_product_invoice(callback.bot, callback.from_user.id, product)
        logger.info("Invoice purchase initiated for product %s by user %s", product.id, callback.from_user.id)
        await callback.answer("Iniciando pagamento via Telegram Stars...", show_alert=False)
    except Exception:
        logger.exception("Invoice checkout failed for product %s", product.id)
        await callback.answer("Não foi possível iniciar a compra neste momento.", show_alert=True)


@router.callback_query(lambda c: c.data and c.data.startswith("preview_product:"))
async def preview_product_callback(callback: CallbackQuery) -> None:
    try:
        product_id = int(callback.data.split(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("Produto inválido.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        product = await get_active_product(session, product_id)

    if product is None:
        await callback.answer("Produto indisponível no momento.", show_alert=True)
        return

    markup = catalog_product_keyboard(product.id, product.price_stars).as_markup()
    await callback.message.edit_text(
        f"<b>{product.name}</b>\n\n{product.description}\n\nPreço: {product.price_stars} ⭐",
        reply_markup=markup,
    )
    logger.info("Product preview requested for product %s by user %s", product_id, callback.from_user.id)
