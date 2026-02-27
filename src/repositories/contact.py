from datetime import date, datetime, time

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
        sort: str = "desc",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[ContactMessage], int]:
        base = select(ContactMessage)
        count_base = select(func.count()).select_from(ContactMessage)

        if is_processed is not None:
            base = base.where(ContactMessage.is_processed == is_processed)
            count_base = count_base.where(ContactMessage.is_processed == is_processed)

        if date_from is not None:
            dt_from = datetime.combine(date_from, time.min)
            base = base.where(ContactMessage.created_at >= dt_from)
            count_base = count_base.where(ContactMessage.created_at >= dt_from)

        if date_to is not None:
            dt_to = datetime.combine(date_to, time.max)
            base = base.where(ContactMessage.created_at <= dt_to)
            count_base = count_base.where(ContactMessage.created_at <= dt_to)

        total = (await self.session.execute(count_base)).scalar() or 0

        order = ContactMessage.created_at.asc() if sort == "asc" else ContactMessage.created_at.desc()
        query = base.order_by(order).offset(offset).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total
