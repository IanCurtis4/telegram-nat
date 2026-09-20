from __future__ import annotations

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from app.database.models import Order, Product, ProductMedia, User
from app.database.repositories.users import UserRepository
from app.database.session import AsyncSessionLocal
from app.services.admin import is_admin

logger = logging.getLogger(__name__)
router = Router()

MEDIA_UPLOADS: dict[int, tuple[int, str]] = {}


def _admin_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧩 Criar produto", callback_data="admin_create_product")
    builder.button(text="📦 Listar produtos", callback_data="admin_list_products")
    builder.button(text="👁️ Pedidos", callback_data="admin_list_orders")
    builder.button(text="🚫 Bloquear usuário", callback_data="admin_block_user")
    builder.button(text="✨ Editar produto", callback_data="admin_edit_product")
    builder.button(text="🔄 Toggle status", callback_data="admin_toggle_product")
    builder.button(text="📸 Adicionar mídia", callback_data="admin_add_media")
    builder.button(text="💸 Reembolsar", callback_data="admin_refund")
    builder.adjust(2)
    return builder


@router.message(Command("admin"))
async def admin_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    await message.answer("<b>Administração</b>", reply_markup=_admin_menu().as_markup())


@router.callback_query(F.data == "admin_list_products")
async def admin_list_products(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        products = (await session.execute(select(Product).order_by(Product.created_at.desc()))).scalars().all()

    if not products:
        await callback.message.edit_text("Nenhum produto cadastrado.")
        return

    lines = ["<b>Produtos</b>"]
    for product in products:
        status = "ATIVO" if product.is_active else "INATIVO"
        lines.append(f"• {product.id} | {product.name} | {product.price_stars} ⭐ | {status}")
    await callback.message.edit_text("\n".join(lines))


@router.callback_query(F.data == "admin_create_product")
async def admin_create_product(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    await callback.message.edit_text(
        "Use o formato:\n\n/create_product\nNome do produto\nDescrição\n100\n"
    )


@router.message(Command("create_product"))
async def create_product_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    args = message.text.splitlines() if message.text else []
    if len(args) < 4:
        await message.answer("Formato inválido. Envie:\n/create_product\nNome\nDescrição\nPreço")
        return

    name = args[1].strip()
    description = args[2].strip()
    try:
        price = int(args[3].strip())
    except ValueError:
        await message.answer("Preço deve ser um número inteiro em Stars.")
        return

    if not name or not description or price <= 0:
        await message.answer("Nome, descrição e preço devem ser válidos.")
        return

    async with AsyncSessionLocal() as session:
        product = Product(name=name, description=description, price_stars=price, is_active=True)
        session.add(product)
        await session.commit()

    await message.answer(f"Produto criado com sucesso: {name} ({price} ⭐)")


@router.callback_query(F.data == "admin_edit_product")
async def admin_edit_product(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    await callback.message.edit_text(
        "Uso:\n/edit_product 3 name Nova descrição\n/edit_product 3 description Nova descrição\n/edit_product 3 price 150"
    )


@router.message(Command("edit_product"))
async def edit_product_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("Uso: /edit_product 3 name Novo nome")
        return

    try:
        product_id = int(parts[1])
    except ValueError:
        await message.answer("O ID do produto deve ser numérico.")
        return

    field = parts[2].lower()
    value = " ".join(parts[3:])

    async with AsyncSessionLocal() as session:
        product = await session.get(Product, product_id)
        if product is None:
            await message.answer("Produto não encontrado.")
            return

        if field == "name":
            product.name = value.strip()
        elif field == "description":
            product.description = value.strip()
        elif field == "price":
            try:
                product.price_stars = int(value)
            except ValueError:
                await message.answer("Preço deve ser numérico.")
                return
        else:
            await message.answer("Campo inválido. Use name, description ou price.")
            return

        product.updated_at = datetime.utcnow()
        await session.commit()

    await message.answer(f"Produto {product_id} atualizado com sucesso.")


@router.callback_query(F.data == "admin_toggle_product")
async def admin_toggle_product(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    await callback.message.edit_text("Uso: /toggle_product 3")


@router.message(Command("toggle_product"))
async def toggle_product_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Uso: /toggle_product 3")
        return

    try:
        product_id = int(parts[1])
    except ValueError:
        await message.answer("O ID do produto deve ser numérico.")
        return

    async with AsyncSessionLocal() as session:
        product = await session.get(Product, product_id)
        if product is None:
            await message.answer("Produto não encontrado.")
            return
        product.is_active = not product.is_active
        product.updated_at = datetime.utcnow()
        await session.commit()

    state = "ativo" if product.is_active else "inativo"
    await message.answer(f"Produto {product_id} está agora {state}.")


@router.callback_query(F.data == "admin_add_media")
async def admin_add_media(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    await callback.message.edit_text("Uso: /add_media 3 photo\nou\n/add_media 3 video\nDepois envie a mídia diretamente para o bot.")


@router.message(Command("add_media"))
async def add_media_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Uso: /add_media 3 photo")
        return

    try:
        product_id = int(parts[1])
    except ValueError:
        await message.answer("O ID do produto deve ser numérico.")
        return

    media_type = parts[2].lower()
    if media_type not in {"photo", "video"}:
        await message.answer("Tipo inválido. Use photo ou video.")
        return

    async with AsyncSessionLocal() as session:
        product = await session.get(Product, product_id)
        if product is None:
            await message.answer("Produto não encontrado.")
            return

    MEDIA_UPLOADS[message.from_user.id] = (product_id, media_type)
    await message.answer("Agora envie a mídia para este produto. Ela será armazenada usando o file_id do Telegram.")


@router.message(F.photo | F.video)
async def capture_media_upload(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    pending = MEDIA_UPLOADS.get(message.from_user.id)
    if pending is None:
        return

    product_id, media_type = pending
    MEDIA_UPLOADS.pop(message.from_user.id, None)

    file_id = None
    if media_type == "photo":
        file_id = message.photo[-1].file_id if message.photo else None
    elif media_type == "video":
        file_id = message.video.file_id if message.video else None

    if not file_id:
        await message.answer("Não foi possível capturar o file_id da mídia.")
        return

    async with AsyncSessionLocal() as session:
        product = await session.get(Product, product_id)
        if product is None:
            await message.answer("Produto não encontrado.")
            return

        existing_count = (await session.execute(select(ProductMedia).where(ProductMedia.product_id == product_id))).scalars().all()
        media = ProductMedia(
            product_id=product_id,
            telegram_file_id=file_id,
            media_type=media_type,
            position=len(existing_count) + 1,
        )
        session.add(media)
        await session.commit()

    await message.answer(f"Mídia adicionada ao produto {product_id} com sucesso.")


@router.callback_query(F.data == "admin_list_orders")
async def admin_list_orders(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        orders = (await session.execute(select(Order).order_by(Order.created_at.desc()))).scalars().all()

    if not orders:
        await callback.message.edit_text("Nenhuma venda registrada.")
        return

    lines = ["<b>Pedidos</b>"]
    for order in orders:
        status = order.status
        lines.append(f"• {order.id} | user_id={order.user_id} | product_id={order.product_id} | status={status} | {order.price_stars} ⭐")
    await callback.message.edit_text("\n".join(lines))


@router.callback_query(F.data == "admin_block_user")
async def admin_block_user(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    await callback.message.edit_text("Envie o ID do Telegram do usuário no formato: /block_user 123456789")


@router.message(Command("block_user"))
async def block_user_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    if len(message.text.split()) < 2:
        await message.answer("Uso: /block_user 123456789")
        return

    telegram_id = int(message.text.split()[1])
    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_telegram_id(telegram_id)
        if user is None:
            await message.answer("Usuário não encontrado.")
            return
        user.is_blocked = True
        user.updated_at = datetime.utcnow()
        await session.commit()

    await message.answer(f"Usuário {telegram_id} bloqueado com sucesso.")


@router.message(Command("unblock_user"))
async def unblock_user_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    if len(message.text.split()) < 2:
        await message.answer("Uso: /unblock_user 123456789")
        return

    telegram_id = int(message.text.split()[1])
    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_telegram_id(telegram_id)
        if user is None:
            await message.answer("Usuário não encontrado.")
            return
        user.is_blocked = False
        user.updated_at = datetime.utcnow()
        await session.commit()

    await message.answer(f"Usuário {telegram_id} desbloqueado com sucesso.")


@router.callback_query(F.data == "admin_refund")
async def admin_refund(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Acesso negado.", show_alert=True)
        return

    await callback.message.edit_text("Uso: /refund_order 3")


@router.message(Command("refund_order"))
async def refund_order_command(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Acesso negado.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Uso: /refund_order 3")
        return

    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("O ID do pedido deve ser numérico.")
        return

    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await message.answer("Pedido não encontrado.")
            return

        if order.status == "refunded":
            await message.answer("Este pedido já foi reembolsado.")
            return

        user = await session.get(User, order.user_id)
        if user is None:
            await message.answer("Usuário associado ao pedido não encontrado.")
            return

        try:
            success = await message.bot.refund_star_payment(
                user_id=user.telegram_id,
                telegram_payment_charge_id=order.telegram_payment_id,
            )
        except TelegramBadRequest:
            await message.answer("Reembolso não suportado pela API para esta transação.")
            logger.exception("Refund failed for order %s", order_id)
            return

        if success:
            order.status = "refunded"
            order.refunded_at = datetime.utcnow()
            await session.commit()
            await message.answer(f"Pedido {order_id} reembolsado com sucesso.")
        else:
            await message.answer("O reembolso não foi concluído pela API do Telegram.")
