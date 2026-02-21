import structlog

from src.exceptions import NotFoundError, ValidationError
from src.models.course import Course, CourseStatus
from src.repositories.course import CourseRepository
from src.schemas.course import CourseCreate, CourseUpdate
from src.services.audit import AuditService

logger = structlog.get_logger()


class CourseService:
    def __init__(
        self,
        repo: CourseRepository,
        audit: AuditService,
        content_page_builder=None,
        notification_service=None,
    ):
        self.repo = repo
        self.audit = audit
        self.content_page_builder = content_page_builder
        self.notification_service = notification_service

    async def get(self, course_id: int) -> Course:
        course = await self.repo.get(course_id)
        if not course:
            raise NotFoundError("Course", course_id)
        return course

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        status: CourseStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Course], int]:
        return await self.repo.list_filtered(offset, limit, status, search)

    async def create(self, data: CourseCreate, user_id: int) -> Course:
        course = await self.repo.create(
            **data.model_dump(),
            created_by=user_id,
        )
        await self.audit.log(user_id, "create", "course", course.id)
        await self.repo.session.commit()
        return course

    async def update(self, course_id: int, data: CourseUpdate, user_id: int) -> Course:
        course = await self.get(course_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return course

        old_values = {k: getattr(course, k) for k in update_data}
        course = await self.repo.update(course, **update_data)

        diff = AuditService.compute_diff(old_values, update_data)
        if diff:
            await self.audit.log(user_id, "update", "course", course.id, changes=diff)

        await self.repo.session.commit()

        if course.status == CourseStatus.PUBLISHED and self.content_page_builder:
            await self._sync_ghost_page()

        return course

    async def delete(self, course_id: int, user_id: int) -> None:
        course = await self.get(course_id)
        if course.status == CourseStatus.PUBLISHED:
            raise ValidationError("Сначала снимите с публикации")

        await self.repo.delete(course)
        await self.audit.log(user_id, "delete", "course", course_id)
        await self.repo.session.commit()

        if self.content_page_builder:
            await self._sync_ghost_page()

    async def publish(self, course_id: int, user_id: int) -> Course:
        course = await self.get(course_id)

        if not course.title:
            raise ValidationError("Title is required")
        if not course.description:
            raise ValidationError("Description is required")
        if not course.schedule:
            raise ValidationError("Schedule is required")
        if not course.cost and course.cost != 0:
            raise ValidationError("Cost is required")

        course = await self.repo.update(course, status=CourseStatus.PUBLISHED)
        await self.audit.log(user_id, "publish", "course", course.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()
        await self._notify_admins(f"Курс опубликован: {course.title}")

        return course

    async def unpublish(self, course_id: int, user_id: int) -> Course:
        course = await self.get(course_id)
        course = await self.repo.update(course, status=CourseStatus.DRAFT)
        await self.audit.log(user_id, "unpublish", "course", course.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()
        await self._notify_admins(f"Курс снят с публикации: {course.title}")

        return course

    async def cancel(self, course_id: int, user_id: int) -> Course:
        course = await self.get(course_id)
        course = await self.repo.update(course, status=CourseStatus.CANCELLED)
        await self.audit.log(user_id, "cancel", "course", course.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()
        await self._notify_admins(f"Курс отменён: {course.title}")

        return course

    async def _sync_ghost_page(self) -> None:
        if self.content_page_builder:
            try:
                await self.content_page_builder.sync_courses_page()
            except Exception:
                logger.exception("Failed to sync courses Ghost page")

    async def _notify_admins(self, message: str) -> None:
        if self.notification_service:
            try:
                await self.notification_service.notify_admins(message)
            except Exception:
                logger.exception("Failed to notify admins")
