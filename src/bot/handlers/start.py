from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from src.config import settings
from src.database import async_session_factory
from src.repositories.user import UserRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start — show WebApp button if user is whitelisted."""
    if not message.from_user:
        return

    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "Доступ запрещён. "
            "Обратитесь к администратору."
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть панель управления",
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                )
            ]
        ]
    )
    await message.answer(
        "Добро пожаловать! "
        "Нажмите кнопку для управления.",
        reply_markup=keyboard,
    )
