from datetime import UTC, datetime
from io import BytesIO

import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from openpyxl import Workbook
from openpyxl.styles import Font

from src.config import settings
from src.database import async_session_factory
from src.repositories.contact import ContactRepository

logger = structlog.get_logger()

EXPORT_MAX_ROWS = 10_000

router = Router()


@router.message(Command("export"))
async def cmd_export(message: Message):
    """Handle /export — generate and send contacts as Excel file."""
    if not message.from_user:
        return

    if message.from_user.id not in settings.ADMIN_TELEGRAM_IDS:
        await message.answer("Нет доступа.")
        return

    logger.info("export_requested", user_id=message.from_user.id)
    await message.answer("Формирую файл...")

    try:
        async with async_session_factory() as session:
            repo = ContactRepository(session)
            items, total = await repo.list_filtered(offset=0, limit=EXPORT_MAX_ROWS)

        if total == 0:
            await message.answer("Нет заявок для экспорта.")
            return

        wb = Workbook()
        buf = BytesIO()
        try:
            ws = wb.active
            ws.title = "Заявки"

            headers = ["ID", "Имя", "Телефон", "Email", "Сообщение", "Источник",
                       "Статус", "Дата создания", "Дата обработки"]
            ws.append(headers)
            for cell in ws[1]:
                cell.font = Font(bold=True)

            for c in items:
                ws.append([
                    c.id,
                    c.name,
                    c.phone,
                    c.email or "",
                    c.message,
                    c.source or "",
                    "Обработана" if c.is_processed else "Новая",
                    c.created_at.strftime("%d.%m.%Y %H:%M") if c.created_at else "",
                    c.processed_at.strftime("%d.%m.%Y %H:%M") if c.processed_at else "",
                ])

            rows_exported = len(items)
            del items

            wb.save(buf)
            filename = f"contacts_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.xlsx"
            document = BufferedInputFile(buf.getvalue(), filename=filename)

            caption = f"Заявки ({total} шт.)"
            if total > EXPORT_MAX_ROWS:
                caption += f" — выгружено {EXPORT_MAX_ROWS}"

            await message.answer_document(document=document, caption=caption)
            logger.info("export_completed", user_id=message.from_user.id, total=total, rows=rows_exported)
        finally:
            wb.close()
            buf.close()

    except Exception:
        logger.exception("export_failed", user_id=message.from_user.id)
        await message.answer("Ошибка при формировании файла. Попробуйте позже.")
