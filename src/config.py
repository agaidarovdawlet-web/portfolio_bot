"""
Application configuration via Pydantic v2 Settings.

All values are loaded from environment variables or a .env file.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the bot and FastAPI application.

    Attributes:
        bot_token: Telegram bot token obtained from @BotFather.
        database_url: Async SQLAlchemy DSN for SQLite.
        api_host: Host on which FastAPI will listen.
        api_port: Port on which FastAPI will listen.
        owner_telegram: Your personal Telegram handle (shown in /contacts).
        owner_github: Your GitHub profile URL.
        owner_linkedin: Your LinkedIn profile URL.
    """
    gemini_api_key: SecretStr
    owner_vk: str = "https://vk.com/tipahuman"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )    # Это спасет от ошибок, если в .env есть лишние переменные

    # ── Telegram ──────────────────────────────────────────────────────────────
    bot_token: SecretStr

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./portfolio.db"

    # ── FastAPI ───────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ── Personal info (edit these!) ───────────────────────────────────────────
    owner_name: str = "Иван Иванов"
    owner_telegram: str = "https://t.me/your_handle"
    owner_github: str = "https://github.com/your_handle"
    owner_linkedin: str = "https://linkedin.com/in/your_handle"


# Создаем экземпляр настроек
settings = Settings()