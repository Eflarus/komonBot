import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.contacts import limiter
from src.config import settings
from src.exceptions import AppError
from src.logging_config import setup_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting KomonBot", root_path=settings.ROOT_PATH)

    # Seed initial admins
    from sqlalchemy import select

    from src.database import async_session_factory
    from src.models.user import WhitelistUser

    async with async_session_factory() as session:
        for tg_id in settings.ADMIN_TELEGRAM_IDS:
            result = await session.execute(
                select(WhitelistUser).where(WhitelistUser.telegram_id == tg_id)
            )
            if not result.scalar_one_or_none():
                session.add(WhitelistUser(telegram_id=tg_id, added_by=None))
        await session.commit()

    # Ghost client + content page builder
    ghost_client = None
    content_page_builder = None
    notification_service = None
    scheduler = None

    if settings.GHOST_ADMIN_API_KEY and settings.GHOST_URL:
        from src.services.ghost import GhostClient

        ghost_client = GhostClient(settings.GHOST_URL, settings.GHOST_ADMIN_API_KEY)

    # Bot + notification service
    from src.bot.setup import bot

    if bot and settings.TELEGRAM_BOT_TOKEN:
        from src.services.notification import NotificationService

        notification_service = NotificationService(bot)

    if ghost_client:
        from src.services.content_page import ContentPageBuilder

        content_page_builder = ContentPageBuilder(ghost_client, notification_service)

    # Store on app state for dependency injection
    app.state.content_page_builder = content_page_builder
    app.state.notification_service = notification_service

    # Setup bot webhook
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from src.bot.setup import setup_bot

            await setup_bot()
        except Exception:
            logger.exception("Failed to setup bot webhook")

    # Start scheduler
    from src.services.scheduler import create_scheduler

    scheduler = create_scheduler(content_page_builder, notification_service, bot)
    scheduler.start()

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown(wait=True)

    if bot and settings.TELEGRAM_BOT_TOKEN:
        await bot.session.close()

    if ghost_client:
        await ghost_client.close()

    from src.database import engine

    await engine.dispose()
    logger.info("KomonBot shutdown complete")


docs_url = "/docs" if settings.LOG_LEVEL == "DEBUG" else None
redoc_url = "/redoc" if settings.LOG_LEVEL == "DEBUG" else None

app = FastAPI(
    title="KomonBot",
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
    
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # No wildcard — only same-origin requests allowed when not configured
    logger.warning("ALLOWED_ORIGINS not set, CORS disabled (same-origin only)")


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )


# Routers
from src.api.router import router  # noqa: E402
from src.api.webhook import router as webhook_router  # noqa: E402

app.include_router(router)
app.include_router(webhook_router)

# Redirect /webapp → /webapp/ with correct root_path prefix
# (Starlette's StaticFiles redirect doesn't include root_path in Location header)
@app.get("/webapp")
async def webapp_trailing_slash():
    return RedirectResponse(
        url=f"{settings.ROOT_PATH}/webapp/", status_code=307,
    )


# Static files (webapp)
app.mount("/webapp", StaticFiles(directory="webapp/dist", html=True), name="webapp")
