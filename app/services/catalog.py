from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Product
from app.database.repositories.products import ProductRepository


async def get_active_products(session: AsyncSession) -> list[Product]:
    repository = ProductRepository(session)
    return await repository.list_active()


async def get_active_product(session: AsyncSession, product_id: int) -> Product | None:
    repository = ProductRepository(session)
    return await repository.get_active_by_id(product_id)
