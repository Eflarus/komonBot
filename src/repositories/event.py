from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import Event, EventStatus
from src.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    def __init__(self, session: AsyncSession):
        super().__init__(Event, session)

    async def list_filtered(
        self,
        offset: int = 0,
        limit: int = 20,
        status: EventStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Event], int]:
        base = select(Event)
        count_base = select(func.count()).select_from(Event)

        if status:
            base = base.where(Event.status == status)
            count_base = count_base.where(Event.status == status)

        if search:
            pattern = f"%{search}%"
            base = base.where(Event.title.like(pattern))
            count_base = count_base.where(Event.title.like(pattern))

        total = (await self.session.execute(count_base)).scalar() or 0

        query = base.order_by(Event.order.asc(), Event.event_date.asc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_published(self) -> list[Event]:
        query = (
            select(Event)
            .where(Event.status == EventStatus.PUBLISHED)
            .order_by(Event.order.asc(), Event.event_date.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_past_published(self, today: date) -> list[Event]:
        query = (
            select(Event)
            .where(Event.status == EventStatus.PUBLISHED)
            .where(Event.event_date < today)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
