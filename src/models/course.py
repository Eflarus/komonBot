import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, Text, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    detailed_description: Mapped[str | None] = mapped_column(Text)
    schedule: Mapped[str] = mapped_column(Text, default="")
    image_desktop: Mapped[str | None] = mapped_column(String(500))
    image_mobile: Mapped[str | None] = mapped_column(String(500))
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[CourseStatus] = mapped_column(
        SQLEnum(CourseStatus, native_enum=False, length=20), default=CourseStatus.DRAFT
    )
    order: Mapped[int] = mapped_column(default=0)
    created_by: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.now
    )
