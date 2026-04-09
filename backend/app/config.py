"""
Crazy Lister v3.0 - Configuration
Environment variables and application settings
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


# Windows AppData paths
APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = APP_DATA_DIR / "uploads"
EXPORT_DIR = APP_DATA_DIR / "exports"
LOG_FILE = APP_DATA_DIR / "crazy_lister.log"

for d in [UPLOAD_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Crazy Lister v3.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # SQLite Database
    DATABASE_URL: str = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"

    # Amazon SP-API (empty by default — user will configure)
    USE_AMAZON_MOCK: bool = False

    # CORS (localhost only for desktop app)
    CORS_ORIGINS: list[str] = ["*"]

    # File paths
    UPLOAD_DIR: str = str(UPLOAD_DIR)
    EXPORT_DIR: str = str(EXPORT_DIR)
    LOG_FILE: str = str(LOG_FILE)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "30 days"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
