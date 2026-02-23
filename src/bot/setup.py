import structlog
from aiogram import Bot, Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo

from src.config import settings

logger = structlog.get_logger()

dp = Dispatcher()

# Lazy bot creation — only if token is valid
bot: Bot | None = None
if settings.TELEGRAM_BOT_TOKEN and ":" in settings.TELEGRAM_BOT_TOKEN:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


async def setup_bot() -> None:
    """Set menu button and webhook."""
    if not bot:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping bot setup")
        return

    from src.bot.handlers.backup import router as backup_router
    from src.bot.handlers.start import router as start_router

    dp.include_router(backup_router)
    dp.include_router(start_router)

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Управление",
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    )
    await bot.set_webhook(
        settings.WEBHOOK_URL,
        secret_token=settings.WEBHOOK_SECRET,
    )
    logger.info("Bot webhook set", url=settings.WEBHOOK_URL)
