from typing import List, Optional
from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "development"
    debug: bool = False
    log_level: str = "info"

    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_decode_responses: bool = True
    redis_username: str = "default"
    redis_password: str = "*********"
    redis_db: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    secret_key: str = "CHANGE_ME"
    access_token_expire_minutes: int = 30
    jwt_algorithm: str = "HS256"
    auth_header: Optional[str] = None
    value_prefix: Optional[str] = None

    admin_initial_email: EmailStr = "admin@example.com"
    admin_initial_username: str = "admin"
    admin_initial_password: str = "CHANGE_ME"
    password_regex: Optional[str] = None

    sentry_dsn: Optional[str] = None
    timezone: str = "UTC"

    @field_validator("sentry_dsn", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v
