import hashlib
import hmac
import json
import time
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config import settings
from src.database import Base, get_db
from src.main import app

test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="session")
async def _create_tables():
    """Drop and recreate all tables to match current models."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True, scope="function")
async def _truncate_tables(_create_tables):
    """Truncate all tables before each test for isolation."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))

    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


def make_init_data(
    user_id: int = 123456789,
    first_name: str = "Test",
    bot_token: str = "",
) -> str:
    """Generate valid Telegram initData string for testing."""
    token = bot_token or settings.TELEGRAM_BOT_TOKEN or "test:token"

    user_data = json.dumps({"id": user_id, "first_name": first_name})
    auth_date = str(int(time.time()))

    data_parts = {"auth_date": auth_date, "user": user_data}

    check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data_parts.items())
    )
    secret_key = hmac.new(
        b"WebAppData", token.encode(), hashlib.sha256
    ).digest()
    hash_value = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()

    parts = [f"{k}={v}" for k, v in data_parts.items()]
    parts.append(f"hash={hash_value}")
    return "&".join(parts)


@pytest.fixture
def auth_headers():
    return {"X-Telegram-Init-Data": make_init_data()}


@pytest_asyncio.fixture
async def editor_headers(client):
    """Auth headers for a non-admin (editor) user."""
    from src.models.user import WhitelistUser

    editor_tg_id = 111222333
    async with test_session_factory() as session:
        session.add(
            WhitelistUser(telegram_id=editor_tg_id, username="editor", role="editor")
        )
        await session.commit()
    return {"X-Telegram-Init-Data": make_init_data(user_id=editor_tg_id)}


@pytest.fixture
def mock_ghost():
    ghost = MagicMock()
    ghost.upload_image = AsyncMock(
        return_value="https://ghost.example.com/image.jpg"
    )
    ghost.get_page = AsyncMock(
        return_value={"updated_at": "2024-01-01T00:00:00Z"}
    )
    ghost.update_page_html = AsyncMock()
    ghost.close = AsyncMock()
    return ghost


@pytest.fixture
def mock_notification():
    notification = MagicMock()
    notification.notify_admins = AsyncMock()
    notification.notify_user = AsyncMock()
    notification.send_event_reminder = AsyncMock()
    return notification


@pytest.fixture
def mock_content_builder(mock_ghost):
    builder = MagicMock()
    builder.ghost_client = mock_ghost
    builder.sync_events_page = AsyncMock()
    builder.sync_courses_page = AsyncMock()
    return builder


@pytest_asyncio.fixture
async def client(
    _truncate_tables, mock_content_builder, mock_notification,
) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client with overridden deps."""
    from src.models.user import WhitelistUser

    # Seed test admin
    async with test_session_factory() as session:
        session.add(
            WhitelistUser(telegram_id=123456789, username="testadmin", role="admin")
        )
        await session.commit()

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    from src.api.contacts import limiter
    limiter.enabled = False

    app.dependency_overrides[get_db] = override_get_db
    app.state.content_page_builder = mock_content_builder
    app.state.notification_service = mock_notification

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    app.state.content_page_builder = None
    app.state.notification_service = None
    limiter.enabled = True
