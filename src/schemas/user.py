from datetime import datetime

from pydantic import BaseModel, Field


class MeResponse(BaseModel):
    id: int
    first_name: str | None


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    role: str = Field(default="editor", pattern="^(admin|editor)$")


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    role: str
    added_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
