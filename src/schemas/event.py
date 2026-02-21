from datetime import date, datetime, time

from pydantic import BaseModel, Field

from src.models.event import EventStatus


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    location: str = Field(default="", max_length=255)
    event_date: date | None = None
    event_time: time | None = None
    ticket_link: str | None = Field(default=None, max_length=500)
    order: int = Field(default=0, ge=0)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=255)
    event_date: date | None = None
    event_time: time | None = None
    ticket_link: str | None = Field(default=None, max_length=500)
    order: int | None = Field(default=None, ge=0)


class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    event_date: date | None
    event_time: time | None
    cover_image: str | None
    ticket_link: str | None
    status: EventStatus
    order: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
