from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://komonbot:password@localhost:5432/komonbot"

    # App — subroute
    ROOT_PATH: str = "/bot"
    PUBLIC_URL: str = "https://komon.tot.pub/bot"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    WEBHOOK_SECRET: str = ""

    # Ghost CMS
    GHOST_URL: str = ""
    GHOST_ADMIN_API_KEY: str = ""
    GHOST_EVENTS_PAGE_ID: str = ""
    GHOST_COURSES_PAGE_ID: str = ""

    # App
    SECRET_KEY: str = "change-me"
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Europe/Moscow"
    ADMIN_TELEGRAM_IDS_STR: str = ""
    ALLOWED_ORIGINS_STR: str = ""

    @computed_field
    @property
    def ADMIN_TELEGRAM_IDS(self) -> list[int]:
        if not self.ADMIN_TELEGRAM_IDS_STR:
            return []
        return [int(x.strip()) for x in self.ADMIN_TELEGRAM_IDS_STR.split(",") if x.strip()]

    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        if not self.ALLOWED_ORIGINS_STR:
            return []
        return [x.strip() for x in self.ALLOWED_ORIGINS_STR.split(",") if x.strip()]

    @computed_field
    @property
    def WEBAPP_URL(self) -> str:
        return f"{self.PUBLIC_URL}/webapp"

    @computed_field
    @property
    def WEBHOOK_URL(self) -> str:
        return f"{self.PUBLIC_URL}/webhook/telegram"

    @property
    def sync_database_url(self) -> str:
        """Synchronous DB URL for Alembic migrations."""
        return self.DATABASE_URL.replace("asyncpg", "psycopg2")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
