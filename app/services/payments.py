from __future__ import annotations

import json
import logging
from typing import Any

from aiogram import Bot
from aiogram.types import InputPaidMediaPhoto, InputPaidMediaVideo, LabeledPrice
from aiogram.exceptions import TelegramBadRequest

from app.database.models import Product, ProductMedia

logger = logging.getLogger(__name__)


def build_payload(product_id: int, user_id: int) -> str:
    return json.dumps({"product_id": product_id, "user_id": user_id}, separators=(",", ":"))


def parse_payload(payload: str) -> dict[str, Any]:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object")
    if "product_id" not in data or "user_id" not in data:
        raise ValueError("Payload missing required fields")
    return data


async def send_product_paid_media(bot: Bot, chat_id: int, product: Product, product_medias: list[ProductMedia]) -> None:
    media: list[InputPaidMediaPhoto | InputPaidMediaVideo] = []
    for product_media in sorted(product_medias, key=lambda item: item.position):
        if product_media.media_type == "photo":
            media.append(InputPaidMediaPhoto(media=product_media.telegram_file_id))
        elif product_media.media_type == "video":
            media.append(InputPaidMediaVideo(media=product_media.telegram_file_id))

    if not media:
        raise ValueError("Product has no media to send")

    try:
        await bot.send_paid_media(
            chat_id=chat_id,
            star_count=product.price_stars,
            media=media,
            payload=build_payload(product.id, chat_id),
            caption=f"<b>{product.name}</b>\n\n{product.description}",
        )
    except TelegramBadRequest:
        logger.exception("Failed to send paid media for product %s", product.id)
        raise


async def send_product_invoice(bot: Bot, chat_id: int, product: Product) -> None:
    await bot.send_invoice(
        chat_id=chat_id,
        title=product.name,
        description=product.description,
        payload=build_payload(product.id, chat_id),
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=product.name, amount=product.price_stars)],
    )
