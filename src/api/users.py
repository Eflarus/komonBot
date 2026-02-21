from fastapi import APIRouter, Depends

from src.api.deps import get_current_user, get_user_repo
from src.exceptions import NotFoundError, ValidationError
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate, UserResponse
from src.utils.telegram_auth import TelegramUser

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    user: TelegramUser = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repo),
):
    items, _ = await repo.list(offset=0, limit=100)
    return items


@router.post("", response_model=UserResponse, status_code=201)
async def add_user(
    data: UserCreate,
    user: TelegramUser = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repo),
):
    existing = await repo.get_by_telegram_id(data.telegram_id)
    if existing:
        raise ValidationError("User already in whitelist")

    new_user = await repo.create(
        telegram_id=data.telegram_id,
        username=data.username,
        first_name=data.first_name,
        last_name=data.last_name,
        added_by=user.id,
    )
    await repo.session.commit()
    return new_user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    user: TelegramUser = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repo),
):
    target = await repo.get(user_id)
    if not target:
        raise NotFoundError("User", user_id)

    if target.telegram_id == user.id:
        raise ValidationError("Cannot remove yourself from whitelist")

    await repo.delete(target)
    await repo.session.commit()
