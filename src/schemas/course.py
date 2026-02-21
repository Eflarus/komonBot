from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.models.course import CourseStatus


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    detailed_description: str | None = Field(default=None, max_length=10000)
    schedule: str = Field(default="", max_length=1000)
    cost: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="RUB", max_length=3)
    order: int = Field(default=0, ge=0)


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    detailed_description: str | None = Field(default=None, max_length=10000)
    schedule: str | None = Field(default=None, max_length=1000)
    cost: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=3)
    order: int | None = Field(default=None, ge=0)


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    detailed_description: str | None
    schedule: str
    image_desktop: str | None
    image_mobile: str | None
    cost: Decimal
    currency: str
    status: CourseStatus
    order: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
