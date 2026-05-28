from typing import List, Optional
from zoneinfo import ZoneInfo

from pydantic import EmailStr, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "development"
    debug: bool = False
    log_level: str = "info"
    log_file_: Optional[Path] = Field(default=Path("data/server.log"), validation_alias="LOG_FILE")

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
    timezone_: str = "UTC"

    @property
    def log_file(self) -> Optional[Path]:
        return Path(__file__).parent.joinpath(self.log_file_)

    def get_redis_url(self, db: int = 0) -> str:
        if self.redis_password == "*********":
            return f"redis://{self.redis_host}:{self.redis_port}/{db}"
        return f"redis://{self.redis_username}:{self.redis_password}@{self.redis_host}:{self.redis_port}/{db}"

    @property
    def timezone(self):
        return ZoneInfo(self.timezone_)

    @field_validator("sentry_dsn", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @property
    def get_redis_broker_url(self):
        if self.redis_password == "":
            return f"redis://{self.redis_host}:{self.redis_port}/0"
        else:
            return f"redis://{self.redis_username}:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

settings = CoreSettings()