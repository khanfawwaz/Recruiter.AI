"""
Minimal config – only what we actually need for the DB-free MVP.
Reads from environment variables (or .env file via python-dotenv if installed).
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Gemini (REQUIRED) ──────────────────────────────────────
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ── Demo / fallback mode ───────────────────────────────────
    DEMO_MODE: bool = False  # set to True to skip Gemini entirely
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── App meta ───────────────────────────────────────────────
    APP_TITLE: str = "Recruiter AI"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
