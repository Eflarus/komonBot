from src.schemas.common import ErrorResponse, ImageUploadResponse, PaginationParams
from src.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from src.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from src.schemas.event import EventCreate, EventResponse, EventUpdate
from src.schemas.user import UserCreate, UserResponse

__all__ = [
    "ContactCreate",
    "ContactResponse",
    "ContactUpdate",
    "CourseCreate",
    "CourseResponse",
    "CourseUpdate",
    "ErrorResponse",
    "EventCreate",
    "EventResponse",
    "EventUpdate",
    "ImageUploadResponse",
    "PaginationParams",
    "UserCreate",
    "UserResponse",
]
