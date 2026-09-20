import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.catalog import router as catalog_router
from app.bot.handlers.purchases import router as purchases_router
from app.bot.handlers.start import router as start_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    logger.info("Starting bot initialization")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(purchases_router)
    dp.include_router(admin_router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user interrupt")
    except Exception:
        logger.exception("Unexpected exception during bot startup")
        raise
