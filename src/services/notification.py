import structlog
from aiogram import Bot

from src.database import async_session_factory
from src.repositories.user import UserRepository

logger = structlog.get_logger()


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_admins(self, message: str) -> None:
        """Send message to all whitelisted admin users."""
        async with async_session_factory() as session:
            repo = UserRepository(session)
            admin_ids = await repo.get_all_telegram_ids()

        for tg_id in admin_ids:
            try:
                await self.bot.send_message(tg_id, message)
            except Exception:
                logger.warning("Failed to notify admin", telegram_id=tg_id)

    async def notify_user(self, telegram_id: int, message: str) -> None:
        """Send message to specific user."""
        try:
            await self.bot.send_message(telegram_id, message)
        except Exception:
            logger.warning("Failed to notify user", telegram_id=telegram_id)

    async def send_event_reminder(self, event) -> None:
        """Send reminder about tomorrow's event to admins."""
        msg = (
            "Напоминание: "
            f"завтра мероприятие!\n"
            f"{event.title}\n"
            f"{event.location}\n"
            f"{event.event_time}"
        )
        await self.notify_admins(msg)
