import structlog
from fastapi import APIRouter, Depends

from src.api.deps import get_content_page_builder, get_current_user
from src.exceptions import ValidationError
from src.utils.telegram_auth import TelegramUser

logger = structlog.get_logger()

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("")
async def sync_all(
    user: TelegramUser = Depends(get_current_user),
    content_page_builder=Depends(get_content_page_builder),
):
    if not content_page_builder:
        raise ValidationError("Ghost CMS not configured")

    errors: list[str] = []

    try:
        await content_page_builder.sync_events_page()
    except Exception:
        logger.exception("Manual sync failed for events")
        errors.append("events")

    try:
        await content_page_builder.sync_courses_page()
    except Exception:
        logger.exception("Manual sync failed for courses")
        errors.append("courses")

    if errors:
        raise ValidationError(f"Sync failed for: {', '.join(errors)}")

    return {"status": "ok"}
