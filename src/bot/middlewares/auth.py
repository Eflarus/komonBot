from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.database import async_session_factory
from src.repositories.user import UserRepository


class WhitelistMiddleware(BaseMiddleware):
    """Check if user is in whitelist before processing."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return

        async with async_session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(event.from_user.id)

        if not user:
            await event.answer("Доступ запрещён.")
            return

        return await handler(event, data)
