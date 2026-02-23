import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import structlog
from aiogram import Bot
from aiogram.types import FSInputFile

from src.config import settings

logger = structlog.get_logger()

tz = ZoneInfo(settings.TIMEZONE)


def _db_path() -> Path:
    """Extract filesystem path from SQLite DATABASE_URL."""
    # "sqlite+aiosqlite:///data/komonbot.db" → "data/komonbot.db"
    url = settings.DATABASE_URL
    prefix = "sqlite+aiosqlite:///"
    if url.startswith(prefix):
        return Path(url[len(prefix):])
    # fallback: strip scheme
    return Path(url.split("///", 1)[-1])


def create_backup() -> Path:
    """Create a consistent SQLite backup using the backup API. Returns path to backup file."""
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz).strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"komonbot-{timestamp}.db"

    src_path = _db_path()
    src_conn = sqlite3.connect(str(src_path))
    dst_conn = sqlite3.connect(str(backup_path))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    logger.info("Backup created", path=str(backup_path), size=backup_path.stat().st_size)
    return backup_path


def rotate_backups() -> int:
    """Remove oldest backups, keeping BACKUP_KEEP most recent. Returns number removed."""
    backup_dir = Path(settings.BACKUP_DIR)
    if not backup_dir.exists():
        return 0

    backups = sorted(backup_dir.glob("komonbot-*.db"), key=lambda p: p.name)
    to_remove = backups[: max(0, len(backups) - settings.BACKUP_KEEP)]
    for path in to_remove:
        path.unlink()
        logger.info("Removed old backup", path=str(path))
    return len(to_remove)


async def run_backup() -> Path:
    """Create backup and rotate old ones."""
    backup_path = create_backup()
    rotate_backups()
    return backup_path


async def send_backup_to_telegram(bot: Bot) -> None:
    """Create a backup and send it to configured Telegram admins."""
    if not settings.BACKUP_TELEGRAM_IDS:
        logger.warning("BACKUP_TELEGRAM_IDS not set, skipping backup send")
        return

    backup_path = await run_backup()

    caption = f"Бэкап БД — {datetime.now(tz).strftime('%d.%m.%Y %H:%M')}"
    document = FSInputFile(path=str(backup_path), filename=backup_path.name)

    for tg_id in settings.BACKUP_TELEGRAM_IDS:
        try:
            await bot.send_document(chat_id=tg_id, document=document, caption=caption)
            logger.info("Backup sent to Telegram", telegram_id=tg_id)
        except Exception:
            logger.exception("Failed to send backup", telegram_id=tg_id)
