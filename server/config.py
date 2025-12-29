from typing import List, Optional
from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env: str = "development"
    debug: bool = False
    log_level: str = "info"

    app_name: str = "FastAPI Module"
    app_description: str = "Template modular para FastAPI server"
    app_version: str = "0.1.0"

    api_prefix: str = "/api"
    api_version: str = "v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    cors_allowed_origins: List[str] = ["*"]
    cors_allowed_headers: List[str] = ["*"]
    cors_allowed_methods: List[str] = ["*"]

    database_url: str = "sqlite:///./data/app.db"
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10

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

    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    pagination_default_limit: int = 50
    pagination_max_limit: int = 200

    @field_validator("cors_allowed_origins", "cors_allowed_headers", "cors_allowed_methods", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("sentry_dsn", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v
