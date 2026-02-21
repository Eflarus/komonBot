from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.deps import get_contact_repo, get_current_user, get_notification_service
from src.exceptions import NotFoundError
from src.repositories.contact import ContactRepository
from src.schemas.contact import ContactCreate, ContactResponse
from src.utils.telegram_auth import TelegramUser

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

limiter = Limiter(key_func=get_remote_address)


@router.post("", status_code=201)
@limiter.limit("5/minute;20/hour")
async def submit_contact(
    request: Request,
    data: ContactCreate,
    repo: ContactRepository = Depends(get_contact_repo),
    notification_service=Depends(get_notification_service),
):
    # Honeypot check: if website field is filled, silently drop
    if data.website:
        return {"status": "ok"}

    contact = await repo.create(
        name=data.name,
        phone=data.phone,
        email=data.email,
        message=data.message,
        source=data.source,
    )
    await repo.session.commit()

    # Notify admins
    if notification_service:
        try:
            msg = (
                f"Новая заявка!\n"
                f"Имя: {contact.name}\n"
                f"Телефон: {contact.phone}\n"
                f"Сообщение: {contact.message}\n"
                f"Источник: {contact.source or 'не указан'}"
            )
            await notification_service.notify_admins(msg)
        except Exception:
            pass  # don't fail contact submission on notification error

    return {"status": "ok", "id": contact.id}


@router.get("", response_model=dict)
async def list_contacts(
    user: TelegramUser = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    is_processed: bool | None = None,
):
    items, total = await repo.list_filtered(offset, limit, is_processed)
    return {
        "items": [ContactResponse.model_validate(i) for i in items],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.patch("/{contact_id}/process", response_model=ContactResponse)
async def process_contact(
    contact_id: int,
    user: TelegramUser = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    contact = await repo.get(contact_id)
    if not contact:
        raise NotFoundError("Contact", contact_id)

    contact = await repo.update(
        contact,
        is_processed=True,
        processed_by=user.id,
        processed_at=datetime.now(UTC).replace(tzinfo=None),
    )
    await repo.session.commit()
    return contact
