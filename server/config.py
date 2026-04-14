from pathlib import Path
from typing import List, Optional

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from server.core.config import CoreSettings


class Settings(CoreSettings):
    app_name: str = "FastAPI Module"
    app_description: str = "Template modular para FastAPI server"
    app_version: str = "0.1.0"

    template_dir: str = "templates"
    static_dir: str = "static"
    media_dir: str = "media"

    api_prefix: str = "/api"
    api_version: str = "v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    scalar_url: str = "/scalar"
    openapi_url: str = "/openapi.json"

    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_domain: str = "http://localhost:8000"

    cors_allowed_origins: List[str] = ["*"]
    cors_allowed_headers: List[str] = ["*"]
    cors_allowed_methods: List[str] = ["*"]
    cors_allow_credentials: bool = True

    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    pagination_default_limit: int = 50
    pagination_max_limit: int = 200

    @property
    def get_redis_broker_url(self):
        if self.redis_password == "":
            return f"redis://{self.redis_host}:{self.redis_port}/0"
        else:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    @property
    def template_dir_full(self):
        return Path(__file__).parent / self.template_dir

    @property
    def static_dir_full(self):
        return Path(__file__).parent / self.static_dir

    @property
    def media_dir_full(self):
        return Path(__file__).parent / self.media_dir

    @field_validator(
        "cors_allowed_origins",
        "cors_allowed_headers",
        "cors_allowed_methods",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

settings = Settings()