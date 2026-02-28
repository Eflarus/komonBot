from fastapi import APIRouter, Depends, Query, UploadFile

from src.api.deps import (
    get_admin_user,
    get_audit_service,
    get_content_page_builder,
    get_current_user,
    get_event_repo,
    get_notification_service,
)
from src.models.event import EventStatus
from src.repositories.event import EventRepository
from src.schemas.common import ImageUploadResponse
from src.schemas.event import EventCreate, EventResponse, EventUpdate
from src.services.audit import AuditService
from src.services.event import EventService
from src.utils.image_validation import validate_image
from src.utils.telegram_auth import TelegramUser

router = APIRouter(prefix="/api/events", tags=["events"])


def _get_event_service(
    repo: EventRepository = Depends(get_event_repo),
    audit: AuditService = Depends(get_audit_service),
    content_page_builder=Depends(get_content_page_builder),
    notification_service=Depends(get_notification_service),
) -> EventService:
    return EventService(repo, audit, content_page_builder, notification_service)


@router.get("", response_model=dict)
async def list_events(
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: EventStatus | None = None,
    search: str | None = Query(default=None, max_length=100),
):
    items, total = await service.list(offset, limit, status, search)
    return {
        "items": [EventResponse.model_validate(i) for i in items],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.get(event_id)


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.create(data, user.id)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.update(event_id, data, user.id)


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    user: TelegramUser = Depends(get_admin_user),
    service: EventService = Depends(_get_event_service),
):
    await service.delete(event_id, user.id)


@router.post("/{event_id}/publish", response_model=EventResponse)
async def publish_event(
    event_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.publish(event_id, user.id)


@router.post("/{event_id}/unpublish", response_model=EventResponse)
async def unpublish_event(
    event_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.unpublish(event_id, user.id)


@router.post("/{event_id}/cancel", response_model=EventResponse)
async def cancel_event(
    event_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.cancel(event_id, user.id)


@router.post("/{event_id}/archive", response_model=EventResponse)
async def archive_event(
    event_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.archive(event_id, user.id)


@router.post("/{event_id}/reactivate", response_model=EventResponse)
async def reactivate_event(
    event_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
):
    return await service.reactivate(event_id, user.id)


@router.post("/{event_id}/upload-image", response_model=ImageUploadResponse)
async def upload_event_image(
    event_id: int,
    file: UploadFile,
    user: TelegramUser = Depends(get_current_user),
    service: EventService = Depends(_get_event_service),
    content_page_builder=Depends(get_content_page_builder),
):
    event = await service.get(event_id)
    content, safe_name = await validate_image(file)

    if content_page_builder and content_page_builder.ghost_client:
        url = await content_page_builder.ghost_client.upload_image(
            content, safe_name
        )
    else:
        url = f"/uploads/{safe_name}"

    event = await service.repo.update(event, cover_image=url)
    await service.repo.session.commit()

    if event.status == EventStatus.PUBLISHED:
        await service._sync_ghost_page()

    return ImageUploadResponse(url=url)
