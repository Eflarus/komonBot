from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import settings
from src.database import async_session_factory
from src.models.event import EventStatus
from src.repositories.event import EventRepository
from src.services.audit import AuditService

logger = structlog.get_logger()

tz = ZoneInfo(settings.TIMEZONE)


async def auto_archive_events(content_page_builder=None):
    """Archive published events with past dates. Runs daily at 03:00."""
    async with async_session_factory() as session:
        repo = EventRepository(session)
        audit = AuditService(session)
        today = datetime.now(tz).date()

        past_events = await repo.get_past_published(today)
        if not past_events:
            return

        for event in past_events:
            await repo.update(event, status=EventStatus.ARCHIVED)
            await audit.log(0, "auto_archive", "event", event.id)

        await session.commit()
        logger.info("Auto-archived events", count=len(past_events))

        # Rebuild Ghost page
        if content_page_builder:
            try:
                await content_page_builder.sync_events_page()
            except Exception:
                logger.exception("Ghost sync failed after auto-archive")


async def send_event_reminders(notification_service=None):
    """Notify admins about tomorrow's events. Runs daily at 10:00."""
    if not notification_service:
        return

    async with async_session_factory() as session:
        repo = EventRepository(session)
        tomorrow = datetime.now(tz).date() + timedelta(days=1)

        events = await repo.get_published()
        tomorrow_events = [e for e in events if e.event_date == tomorrow]

        for event in tomorrow_events:
            try:
                await notification_service.send_event_reminder(event)
            except Exception:
                logger.exception("Failed to send reminder", event_id=event.id)


def create_scheduler(
    content_page_builder=None, notification_service=None, bot=None,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        auto_archive_events,
        "cron",
        hour=3,
        minute=0,
        kwargs={"content_page_builder": content_page_builder},
        id="auto_archive_events",
    )
    scheduler.add_job(
        send_event_reminders,
        "cron",
        hour=10,
        minute=0,
        kwargs={"notification_service": notification_service},
        id="send_event_reminders",
    )

    # Daily backup with rotation at 04:00
    from src.services.backup import run_backup

    scheduler.add_job(
        run_backup,
        "cron",
        hour=4,
        minute=0,
        id="daily_backup",
    )

    # Send backup to Telegram every 48 hours at 05:00
    if bot and settings.BACKUP_TELEGRAM_IDS:
        from src.services.backup import send_backup_to_telegram

        scheduler.add_job(
            send_backup_to_telegram,
            "interval",
            hours=48,
            kwargs={"bot": bot},
            id="send_backup_telegram",
        )

    return scheduler
