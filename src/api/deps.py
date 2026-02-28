from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.exceptions import ForbiddenError
from src.repositories.contact import ContactRepository
from src.repositories.course import CourseRepository
from src.repositories.event import EventRepository
from src.repositories.user import UserRepository
from src.services.audit import AuditService
from src.utils.telegram_auth import TelegramUser, validate_init_data


async def get_current_user(
    x_telegram_init_data: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> TelegramUser:
    """Validate initData and check user is in whitelist."""
    user = validate_init_data(x_telegram_init_data, settings.TELEGRAM_BOT_TOKEN)
    user_repo = UserRepository(db)
    whitelisted = await user_repo.get_by_telegram_id(user.id)
    if not whitelisted:
        raise ForbiddenError("User not in whitelist")
    return user


async def get_admin_user(
    x_telegram_init_data: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> TelegramUser:
    """Validate initData and check user has admin role."""
    user = validate_init_data(x_telegram_init_data, settings.TELEGRAM_BOT_TOKEN)
    user_repo = UserRepository(db)
    whitelisted = await user_repo.get_by_telegram_id(user.id)
    if not whitelisted:
        raise ForbiddenError("User not in whitelist")
    if not whitelisted.is_admin:
        raise ForbiddenError("Admin access required")
    return user


async def get_event_repo(db: AsyncSession = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


async def get_course_repo(db: AsyncSession = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_contact_repo(db: AsyncSession = Depends(get_db)) -> ContactRepository:
    return ContactRepository(db)


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


def get_content_page_builder(request: Request):
    return request.app.state.content_page_builder


def get_notification_service(request: Request):
    return request.app.state.notification_service
