from __future__ import annotations

import os


def get_database_url() -> str:
    # 例: postgresql+asyncpg://app:app@localhost:5432/appdb
    url = os.getenv("DATABASE_URL")
    if not url:
        # docker-composeの標準値
        url = "postgresql+asyncpg://app:app@localhost:5432/appdb"
    return url


def get_echo_flag() -> bool:
    return os.getenv("SQLALCHEMY_ECHO", "0") in {"1", "true", "True"}
