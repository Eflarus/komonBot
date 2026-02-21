import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(pattern=r"^\+?[\d\s\-\(\)]{7,20}$")
    email: EmailStr | None = None
    message: str = Field(min_length=1, max_length=2000)
    source: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None)  # honeypot: if filled, silently drop

    @field_validator("name", "message")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        v = v.strip()
        v = re.sub(r"<[^>]+>", "", v)  # strip HTML tags
        v = re.sub(r"\s+", " ", v)  # collapse whitespace
        return v


class ContactUpdate(BaseModel):
    is_processed: bool = True


class ContactResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: str | None
    message: str
    source: str | None
    is_processed: bool
    processed_by: int | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}
