from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[Product]:
        stmt = (
            select(Product)
            .options(selectinload(Product.media))
            .where(Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_by_id(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(selectinload(Product.media))
            .where(Product.id == product_id)
            .where(Product.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
