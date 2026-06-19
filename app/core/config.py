from pydantic_settings import BaseSettings, SettingsConfigDict

from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = ""
    redis_url: str = ""
    secret_key: str = ""
    llm_api_key: str = "" 
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = ""
    llama_cloud_api_key: str = ""

    debug: bool = False
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()