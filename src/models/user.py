from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"


class WhitelistUser(Base):
    __tablename__ = "whitelist_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), server_default=text("'editor'"))
    added_by: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP")
    )

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN
