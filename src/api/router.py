from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.contacts import router as contacts_router
from src.api.courses import router as courses_router
from src.api.events import router as events_router
from src.api.sync import router as sync_router
from src.api.users import router as users_router
from src.database import get_db

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(503, detail="Database unavailable")


router.include_router(events_router)
router.include_router(courses_router)
router.include_router(contacts_router)
router.include_router(users_router)
router.include_router(sync_router)
