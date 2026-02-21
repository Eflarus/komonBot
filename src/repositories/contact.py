from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact import ContactMessage
from src.repositories.base import BaseRepository


class ContactRepository(BaseRepository[ContactMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(ContactMessage, session)

    async def list_filtered(
        self,
        offset: int = 0,
        limit: int = 20,
        is_processed: bool | None = None,
    ) -> tuple[list[ContactMessage], int]:
        base = select(ContactMessage)
        count_base = select(func.count()).select_from(ContactMessage)

        if is_processed is not None:
            base = base.where(ContactMessage.is_processed == is_processed)
            count_base = count_base.where(ContactMessage.is_processed == is_processed)

        total = (await self.session.execute(count_base)).scalar() or 0

        query = base.order_by(ContactMessage.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total
