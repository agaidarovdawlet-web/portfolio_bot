import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI, Request
from sqlalchemy import func, select

from src.bot import handlers
from src.config import settings
from src.db.models import User
from src.db.session import async_session_factory, create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(handlers.router)

WEBHOOK_PATH = f"/webhook/{settings.bot_token.get_secret_value()}"
WEBHOOK_URL = f"https://{settings.render_external_hostname}{WEBHOOK_PATH}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables if not exist…")
    await create_tables()
    logger.info("Database ready.")

    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL, 
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )
        logger.info(f"Webhook set to: {WEBHOOK_URL}")
    
    yield

    logger.info("Shutting down: removing webhook…")
    await bot.session.close()
    logger.info("FastAPI shutdown complete.")

fastapi_app = FastAPI(
    title="Portfolio Bot",
    lifespan=lifespan,
)

# Добавил этот роут, чтобы Render видел, что сервис живой (убирает 404 в логах)
@fastapi_app.get("/")
async def root():
    return {"status": "ok", "info": "Portfolio Bot is running"}

@fastapi_app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@fastapi_app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "mode": "webhook"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.api_port))
    logger.info(f"Starting FastAPI server on port {port}")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
