from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import main_menu_keyboard
from app.database.models import User
from app.database.session import AsyncSessionLocal
from app.services.admin import can_access_bot

logger = logging.getLogger(__name__)
router = Router()


async def _get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
        logger.info("New user registered: %s", telegram_id)
    else:
        if user.username != username:
            user.username = username
            await session.flush()
    await session.commit()
    return user


def _confirm_age_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Tenho 18+ e aceito os termos", callback_data="confirm_age")
    return builder


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    if message.from_user is None:
        logger.warning("Start command received without from_user context")
        return

    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(session, message.from_user.id, message.from_user.username)

    if not can_access_bot(user):
        await message.answer("Seu acesso foi bloqueado por administração.")
        logger.warning("Blocked user %s attempted to start the bot", user.telegram_id)
        return

    text = (
        "<b>Conteúdo adulto</b>\n\n"
        "Este bot contém conteúdo destinado exclusivamente a maiores de 18 anos. "
        "Ao continuar, você declara que tem 18 anos ou mais e concorda com os termos de uso."
    )
    keyboard = _confirm_age_keyboard()
    await message.answer(text, reply_markup=keyboard.as_markup())
    logger.info("User %s started bot and saw age confirmation", user.telegram_id)


@router.callback_query(lambda c: c.data == "confirm_age")
async def confirm_age_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        logger.warning("Age confirmation callback without from_user context")
        return

    telegram_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user = await _get_or_create_user(session, telegram_id, callback.from_user.username)
        if not can_access_bot(user):
            await callback.answer("Seu acesso foi bloqueado por administração.", show_alert=True)
            logger.warning("Blocked user %s tried to confirm age", telegram_id)
            return
        user.age_confirmed_at = datetime.now(timezone.utc)
        user.terms_version = "1.0"
        await session.commit()

    menu_markup = main_menu_keyboard().as_markup()
    await callback.message.edit_text(
        "<b>Confirmação registrada.</b>\n\n"
        "Você já pode acessar o catálogo e comprar conteúdo disponível.",
        reply_markup=menu_markup,
    )
    logger.info("User %s confirmed age and accepted terms", telegram_id)
