from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    database_url: str
    db_echo: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()
        admin_raw = os.getenv("ADMIN_ID", "0").strip()
        database_url = os.getenv("DATABASE_URL", "").strip()
        db_echo = os.getenv("DB_ECHO", "false").strip().lower() in {"1", "true", "yes", "on"}

        if not token:
            raise RuntimeError("BOT_TOKEN is not configured.")

        try:
            admin_id = int(admin_raw)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("ADMIN_ID must be a valid Telegram user ID.") from exc

        if admin_id <= 0:
            raise RuntimeError("ADMIN_ID must be a valid Telegram user ID.")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured.")

        return cls(
            bot_token=token,
            admin_id=admin_id,
            database_url=database_url,
            db_echo=db_echo,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
