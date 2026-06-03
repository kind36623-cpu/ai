from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "SeedAGI"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "change-me"

    # Database
    database_url: str = "sqlite+aiosqlite:///./seed_agi.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # AI Models
    gemini_api_key: str = ""
    groq_api_key: str = ""
    primary_model: str = "gemini-2.0-flash"
    reasoning_model: str = "gemini-2.5-pro"
    fast_model: str = "llama-3.1-8b-instant"

    # Memory
    pinecone_api_key: str = ""
    pinecone_index_name: str = "seed-agi-memory"

    # Crawler
    crawler_enabled: bool = False
    crawler_schedule_hours: int = 6

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
