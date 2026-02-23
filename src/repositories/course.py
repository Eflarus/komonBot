from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.course import Course, CourseStatus
from src.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(Course, session)

    async def list_filtered(
        self,
        offset: int = 0,
        limit: int = 20,
        status: CourseStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Course], int]:
        base = select(Course)
        count_base = select(func.count()).select_from(Course)

        if status:
            base = base.where(Course.status == status)
            count_base = count_base.where(Course.status == status)

        if search:
            pattern = f"%{search}%"
            base = base.where(Course.title.like(pattern))
            count_base = count_base.where(Course.title.like(pattern))

        total = (await self.session.execute(count_base)).scalar() or 0

        query = base.order_by(Course.order.asc(), Course.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_published(self) -> list[Course]:
        query = (
            select(Course)
            .where(Course.status == CourseStatus.PUBLISHED)
            .order_by(Course.order.asc(), Course.id.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
