from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Order, User


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_payment_id(self, telegram_payment_id: str) -> Order | None:
        stmt = select(Order).where(Order.telegram_payment_id == telegram_payment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, *, user_id: int, product_id: int, telegram_payment_id: str, price_stars: int) -> Order:
        order = Order(
            user_id=user_id,
            product_id=product_id,
            telegram_payment_id=telegram_payment_id,
            price_stars=price_stars,
            status="paid",
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def list_for_user(self, user: User) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
