"""
Application entry point.

Starts two concurrent async tasks:
    1. FastAPI (via Uvicorn) — serves health-check and metrics endpoints.
    2. Aiogram bot — runs in Long Polling mode.

Both tasks share the same asyncio event loop, so they can safely share
resources such as the SQLAlchemy async engine.

Usage::

    python -m src.main
    # or
    uvicorn src.main:fastapi_app --reload   # FastAPI only (dev)
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI
from sqlalchemy import func, select

from src.bot import handlers
from src.config import settings
from src.db.models import User
from src.db.session import async_session_factory, create_tables

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Aiogram setup ─────────────────────────────────────────────────────────────

bot = Bot(
    token=settings.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(handlers.router)


# ── FastAPI lifespan ──────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: create DB tables on startup."""
    logger.info("Creating database tables if not exist…")
    await create_tables()
    logger.info("Database ready.")
    yield
    logger.info("FastAPI shutdown.")


fastapi_app = FastAPI(
    title="Portfolio Bot — Admin API",
    description="Health-check and basic analytics for the Telegram portfolio bot.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── FastAPI routes ────────────────────────────────────────────────────────────


@fastapi_app.get("/health", tags=["ops"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return 200 OK with service status.

    Suitable for use as a Docker/Kubernetes liveness probe.
    """
    return {"status": "ok"}


@fastapi_app.get("/metrics/users", tags=["metrics"], summary="Visitor count")
async def user_metrics() -> dict[str, int]:
    """Return the total number of unique bot visitors.

    Use this to show HR managers how many people have opened the bot.
    """
    async with async_session_factory() as session:
        result = await session.execute(select(func.count()).select_from(User))
        total: int = result.scalar_one()
    return {"total_users": total}


# ── Polling task ──────────────────────────────────────────────────────────────


async def run_bot() -> None:
    """Start the aiogram Long Polling loop.

    Drops any updates that accumulated while the bot was offline so that
    stale messages are not processed on restart.
    """
    logger.info("Starting Telegram Long Polling…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# ── Main coroutine ────────────────────────────────────────────────────────────


async def main() -> None:
    """Run FastAPI (uvicorn) and the aiogram bot concurrently."""
    # Create tables before anything else starts.
    await create_tables()

    uvicorn_config = uvicorn.Config(
        app=fastapi_app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
        # Disable uvicorn's own lifespan so we control startup order.
        lifespan="off",
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)

    logger.info(
        "FastAPI will listen on http://%s:%s",
        settings.api_host,
        settings.api_port,
    )

    await asyncio.gather(
        uvicorn_server.serve(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
