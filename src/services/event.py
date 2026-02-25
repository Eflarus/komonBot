import structlog

from src.exceptions import NotFoundError, ValidationError
from src.models.event import Event, EventStatus
from src.repositories.event import EventRepository
from src.schemas.event import EventCreate, EventUpdate
from src.services.audit import AuditService

logger = structlog.get_logger()


class EventService:
    def __init__(
        self,
        repo: EventRepository,
        audit: AuditService,
        content_page_builder=None,
        notification_service=None,
    ):
        self.repo = repo
        self.audit = audit
        self.content_page_builder = content_page_builder
        self.notification_service = notification_service

    async def get(self, event_id: int) -> Event:
        event = await self.repo.get(event_id)
        if not event:
            raise NotFoundError("Event", event_id)
        return event

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        status: EventStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Event], int]:
        return await self.repo.list_filtered(offset, limit, status, search)

    async def create(self, data: EventCreate, user_id: int) -> Event:
        event = await self.repo.create(
            **data.model_dump(),
            created_by=user_id,
        )
        await self.audit.log(user_id, "create", "event", event.id)
        await self.repo.session.commit()
        return event

    async def update(self, event_id: int, data: EventUpdate, user_id: int) -> Event:
        event = await self.get(event_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return event

        old_values = {k: getattr(event, k) for k in update_data}
        event = await self.repo.update(event, **update_data)

        diff = AuditService.compute_diff(old_values, update_data)
        if diff:
            await self.audit.log(user_id, "update", "event", event.id, changes=diff)

        await self.repo.session.commit()

        if event.status == EventStatus.PUBLISHED and self.content_page_builder:
            await self._sync_ghost_page()

        return event

    async def delete(self, event_id: int, user_id: int) -> None:
        event = await self.get(event_id)
        if event.status == EventStatus.PUBLISHED:
            raise ValidationError("Сначала снимите с публикации")

        was_published = event.status in (EventStatus.CANCELLED, EventStatus.ARCHIVED)
        await self.repo.delete(event)
        await self.audit.log(user_id, "delete", "event", event_id)
        await self.repo.session.commit()

        if was_published and self.content_page_builder:
            await self._sync_ghost_page()

    async def publish(self, event_id: int, user_id: int) -> Event:
        event = await self.get(event_id)

        # Validate required fields
        if not event.title:
            raise ValidationError("Title is required")
        if not event.location:
            raise ValidationError("Location is required")
        if not event.event_date:
            raise ValidationError("Event date is required")
        if not event.event_time:
            raise ValidationError("Event time is required")

        event = await self.repo.update(event, status=EventStatus.PUBLISHED)
        await self.audit.log(user_id, "publish", "event", event.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()
        await self._notify_admins(f"Событие опубликовано: {event.title}")

        return event

    async def unpublish(self, event_id: int, user_id: int) -> Event:
        event = await self.get(event_id)
        event = await self.repo.update(event, status=EventStatus.DRAFT)
        await self.audit.log(user_id, "unpublish", "event", event.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()
        await self._notify_admins(f"Событие снято с публикации: {event.title}")

        return event

    async def cancel(self, event_id: int, user_id: int) -> Event:
        event = await self.get(event_id)
        event = await self.repo.update(event, status=EventStatus.CANCELLED)
        await self.audit.log(user_id, "cancel", "event", event.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()
        await self._notify_admins(f"Событие отменено: {event.title}")

        return event

    async def archive(self, event_id: int, user_id: int) -> Event:
        event = await self.get(event_id)
        if event.status == EventStatus.DRAFT:
            raise ValidationError("Нельзя архивировать черновик")

        event = await self.repo.update(event, status=EventStatus.ARCHIVED)
        await self.audit.log(user_id, "archive", "event", event.id)
        await self.repo.session.commit()

        await self._sync_ghost_page()

        return event

    async def reactivate(self, event_id: int, user_id: int) -> Event:
        event = await self.get(event_id)
        if event.status not in (EventStatus.CANCELLED, EventStatus.ARCHIVED):
            raise ValidationError("Можно вернуть только отменённое или архивное")

        event = await self.repo.update(event, status=EventStatus.DRAFT)
        await self.audit.log(user_id, "reactivate", "event", event.id)
        await self.repo.session.commit()

        return event

    async def _sync_ghost_page(self) -> None:
        if self.content_page_builder:
            try:
                await self.content_page_builder.sync_events_page()
            except Exception:
                logger.exception("Failed to sync events Ghost page")

    async def _notify_admins(self, message: str) -> None:
        if self.notification_service:
            try:
                await self.notification_service.notify_admins(message)
            except Exception:
                logger.exception("Failed to notify admins")
