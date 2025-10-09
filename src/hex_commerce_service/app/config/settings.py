from __future__ import annotations

import functools
import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvName = Literal["dev", "staging", "prod"]


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="hex-commerce")
    env: EnvName = Field(default="dev")
    version: str = Field(default=os.getenv("APP_VERSION", "0.0.0"))

    # Logging
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    log_json: bool = Field(default=os.getenv("LOG_JSON", "1") in {"1", "true", "True"})
    log_timezone: Literal["utc", "local"] = Field(default=os.getenv("LOG_TZ", "utc"))

    # HTTP / API
    request_id_header: str = Field(default=os.getenv("REQUEST_ID_HEADER", "x-request-id"))
    correlation_id_header: str = Field(
        default=os.getenv("CORRELATION_ID_HEADER", "x-correlation-id")
    )

    # DB (asyncpg URL, Day 8)
    database_url: str = Field(
        default=os.getenv("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/appdb")
    )

    # JWT (Day 12)
    jwt_secret: str = Field(default=os.getenv("JWT_SECRET", "dev-secret-change-me"))
    jwt_alg: str = Field(default=os.getenv("JWT_ALG", "HS256"))
    jwt_ttl_seconds: int = Field(default=int(os.getenv("JWT_TTL_SECONDS", "3600")))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
