from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import settings

router = Router()


@router.message(Command("backup"))
async def cmd_backup(message: Message):
    """Handle /backup — create and send a fresh backup to the requesting admin."""
    if not message.from_user:
        return

    if message.from_user.id not in settings.BACKUP_TELEGRAM_IDS:
        await message.answer("Нет доступа к бэкапам.")
        return

    await message.answer("Создаю бэкап...")

    from src.services.backup import run_backup

    from aiogram.types import FSInputFile
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(settings.TIMEZONE)
    backup_path = await run_backup()

    caption = f"Бэкап БД — {datetime.now(tz).strftime('%d.%m.%Y %H:%M')}"
    document = FSInputFile(path=str(backup_path), filename=backup_path.name)

    await message.answer_document(document=document, caption=caption)
