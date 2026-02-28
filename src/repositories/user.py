from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import ROLE_ADMIN, WhitelistUser
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[WhitelistUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(WhitelistUser, session)

    async def get_by_telegram_id(self, telegram_id: int) -> WhitelistUser | None:
        query = select(WhitelistUser).where(WhitelistUser.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_telegram_ids(self) -> list[int]:
        query = select(WhitelistUser.telegram_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_admin_telegram_ids(self) -> list[int]:
        query = select(WhitelistUser.telegram_id).where(
            WhitelistUser.role == ROLE_ADMIN
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
