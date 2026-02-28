from fastapi import APIRouter, Depends, Query, UploadFile

from src.api.deps import (
    get_audit_service,
    get_content_page_builder,
    get_course_repo,
    get_current_user,
    get_notification_service,
)
from src.models.course import CourseStatus
from src.repositories.course import CourseRepository
from src.schemas.common import ImageUploadResponse
from src.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from src.services.audit import AuditService
from src.services.course import CourseService
from src.utils.image_validation import validate_image
from src.utils.telegram_auth import TelegramUser

router = APIRouter(prefix="/api/courses", tags=["courses"])


def _get_course_service(
    repo: CourseRepository = Depends(get_course_repo),
    audit: AuditService = Depends(get_audit_service),
    content_page_builder=Depends(get_content_page_builder),
    notification_service=Depends(get_notification_service),
) -> CourseService:
    return CourseService(repo, audit, content_page_builder, notification_service)


@router.get("", response_model=dict)
async def list_courses(
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: CourseStatus | None = None,
    search: str | None = Query(default=None, max_length=100),
):
    items, total = await service.list(offset, limit, status, search)
    return {
        "items": [CourseResponse.model_validate(i) for i in items],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.get(course_id)


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    data: CourseCreate,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.create(data, user.id)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.update(course_id, data, user.id)


@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    await service.delete(course_id, user.id)


@router.post("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.publish(course_id, user.id)


@router.post("/{course_id}/unpublish", response_model=CourseResponse)
async def unpublish_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.unpublish(course_id, user.id)


@router.post("/{course_id}/cancel", response_model=CourseResponse)
async def cancel_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.cancel(course_id, user.id)


@router.post("/{course_id}/archive", response_model=CourseResponse)
async def archive_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.archive(course_id, user.id)


@router.post("/{course_id}/reactivate", response_model=CourseResponse)
async def reactivate_course(
    course_id: int,
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
):
    return await service.reactivate(course_id, user.id)


@router.post("/{course_id}/upload-image", response_model=ImageUploadResponse)
async def upload_course_image(
    course_id: int,
    file: UploadFile,
    type: str = Query(default="desktop", pattern="^(desktop|mobile)$"),
    user: TelegramUser = Depends(get_current_user),
    service: CourseService = Depends(_get_course_service),
    content_page_builder=Depends(get_content_page_builder),
):
    course = await service.get(course_id)
    content, safe_name = await validate_image(file)

    if content_page_builder and content_page_builder.ghost_client:
        url = await content_page_builder.ghost_client.upload_image(
            content, safe_name
        )
    else:
        url = f"/uploads/{safe_name}"

    field = "image_desktop" if type == "desktop" else "image_mobile"
    course = await service.repo.update(course, **{field: url})
    await service.repo.session.commit()

    if course.status == CourseStatus.PUBLISHED:
        await service._sync_ghost_page()

    return ImageUploadResponse(url=url)
