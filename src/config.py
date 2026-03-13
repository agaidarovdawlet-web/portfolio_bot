from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: SecretStr
    bot_token: SecretStr
    
    database_url: str = "sqlite+aiosqlite:///./portfolio.db"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    render_external_hostname: str = "localhost"

    owner_name: str = "Даулет Агайдаров"
    owner_telegram: str = "https://t.me/agaidarovdawlet"
    owner_github: str = "https://github.com/agaidarovdawlet-web"
    owner_linkedin: str = "https://linkedin.com/in/agaidarovdawlet"
    owner_vk: str = "https://vk.com/tipahuman"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()
