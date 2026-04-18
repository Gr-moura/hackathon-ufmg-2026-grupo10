from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model_reasoning: str = "gpt-4o-mini"
    openai_model_embedding: str = "text-embedding-3-small"

    postgres_password: str = "enteros_dev"
    database_url: str = "postgresql+psycopg://enteros:enteros_dev@db:5432/enteros"

    jwt_secret: str = "change-me-only-for-demo"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    log_level: str = "INFO"
    data_dir: str = "/data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
