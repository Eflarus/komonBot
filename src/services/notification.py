import time

import structlog
from aiogram import Bot

from src.database import async_session_factory
from src.repositories.user import UserRepository

logger = structlog.get_logger()

CONTACT_NOTIFY_INTERVAL = 30  # seconds between contact notifications


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._last_contact_notify: float = 0
        self._suppressed_count: int = 0

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

    async def notify_contact_submission(self, message: str) -> None:
        """Throttled notification for new contact submissions."""
        now = time.monotonic()
        elapsed = now - self._last_contact_notify

        if elapsed < CONTACT_NOTIFY_INTERVAL:
            self._suppressed_count += 1
            logger.info(
                "contact_notification_throttled",
                suppressed=self._suppressed_count,
            )
            return

        if self._suppressed_count > 0:
            message += f"\n\n(+{self._suppressed_count} за последние {CONTACT_NOTIFY_INTERVAL}с)"

        self._last_contact_notify = now
        self._suppressed_count = 0
        await self.notify_admins(message)

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
