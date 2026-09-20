from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import User
from app.database.repositories.orders import OrderRepository
from app.database.session import AsyncSessionLocal
from app.services.catalog import get_active_product
from app.services.payments import parse_payload

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("my_purchases"))
async def my_purchases_command(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user_by_telegram_id(session, message.from_user.id, message.from_user.username)
        repository = OrderRepository(session)
        orders = await repository.list_for_user(user)

    if not orders:
        await message.answer("Você ainda não realizou nenhuma compra.")
        return

    lines = ["<b>Minhas compras</b>"]
    for order in orders:
        lines.append(f"• Produto ID {order.product_id} — {order.price_stars} ⭐ — {order.status}")
    await message.answer("\n".join(lines))


@router.callback_query(F.data == "my_purchases")
async def my_purchases_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user_by_telegram_id(session, callback.from_user.id, callback.from_user.username)
        repository = OrderRepository(session)
        orders = await repository.list_for_user(user)

    if not orders:
        await callback.message.edit_text("Você ainda não realizou nenhuma compra.")
        return

    lines = ["<b>Minhas compras</b>"]
    for order in orders:
        lines.append(f"• Produto ID {order.product_id} — {order.price_stars} ⭐ — {order.status}")
    await callback.message.edit_text("\n".join(lines))


async def get_or_create_user_by_telegram_id(session, telegram_id: int, username: str | None) -> User:
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
        await session.commit()
    elif user.username != username:
        user.username = username
        await session.commit()
    return user


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if payment is None:
        logger.warning("Successful payment event without payment payload")
        return

    from_user = message.from_user
    if from_user is None:
        logger.warning("Successful payment message without from_user context")
        return

    try:
        payload_data = parse_payload(payment.invoice_payload)
        product_id = int(payload_data["product_id"])
        user_id = int(payload_data["user_id"])
    except (ValueError, TypeError, KeyError):
        logger.warning("Invalid payload received for successful payment from user %s: %r", from_user.id, payment.invoice_payload)
        await message.answer("Pagamento recebido, mas a referência da compra está inválida.")
        return

    async with AsyncSessionLocal() as session:
        try:
            user = await get_or_create_user_by_telegram_id(session, from_user.id, from_user.username)
            product = await get_active_product(session, product_id)
            if product is None:
                logger.warning("Payment attempted for inactive product %s by user %s", product_id, from_user.id)
                await message.answer("Este produto não está mais disponível.")
                return

            repository = OrderRepository(session)
            existing = await repository.get_by_telegram_payment_id(payment.telegram_payment_charge_id)
            if existing is not None:
                logger.info("Duplicate order prevented for payment %s", payment.telegram_payment_charge_id)
                await message.answer("Compra já registrada.")
                return

            order = await repository.create(
                user_id=user.id,
                product_id=product.id,
                telegram_payment_id=payment.telegram_payment_charge_id,
                price_stars=product.price_stars,
            )
            await session.commit()
        except Exception:
            logger.exception("Error while recording successful payment for user %s", from_user.id)
            await message.answer("Houve um problema ao registrar a sua compra. Tente novamente em alguns instantes.")
            return

    await message.answer(
        f"<b>Compra confirmada.</b>\n\nProduto: {product.name}\nValor: {product.price_stars} ⭐\nPedido: {order.id}",
    )
    logger.info("Purchase confirmed for product %s by user %s", product.id, user_id)
