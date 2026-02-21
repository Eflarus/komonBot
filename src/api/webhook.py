import hmac

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from src.bot.setup import bot, dp
from src.config import settings

router = APIRouter(tags=["webhook"])


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(...),
):
    if not hmac.compare_digest(x_telegram_bot_api_secret_token, settings.WEBHOOK_SECRET):
        raise HTTPException(403, "Invalid webhook secret")

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
