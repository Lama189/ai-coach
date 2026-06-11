from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    bot_token: str = ""
    api_base_url: str = ""
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()