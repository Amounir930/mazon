import sys
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


def get_env_path() -> Path:
    """Unified helper to get the path to the .env file (supports Local and EXE)"""
    if getattr(sys, 'frozen', False):
        # Compiled EXE mode: .env is in the same folder as the .exe
        return Path(sys.executable).parent / ".env"
    
    # Development mode: resolve to backend/.env
    # Current file is backend/app/config.py, we need parent/parent/.env
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent
    return backend_dir / ".env"


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
        env_file=get_env_path(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        protected_namespaces=(),  # Fixes Pydantic UserWarning about 'model_'
    )

    # Application
    APP_NAME: str = "Crazy Lister v3.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # SQLite Database
    DATABASE_URL: str = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"

    # Amazon SP-API (Real Production Only)
    # AWS Credentials
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "eu-west-1"
    AWS_SELLER_ROLE_ARN: Optional[str] = None

    # LWA Credentials (Used for SP-API OAuth)
    SP_API_CLIENT_ID: str = ""
    SP_API_CLIENT_SECRET: str = ""
    SP_API_REFRESH_TOKEN: str = ""
    SP_API_SELLER_ID: str = ""
    SP_API_MARKETPLACE_ID: str = "ARBP9OOSHTCHU"
    SP_API_COUNTRY: str = "eg"
    SP_API_ENABLED: bool = True

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

    # Amazon Mock Mode (set to True to use local mock API instead of real SP-API)
    USE_AMAZON_MOCK: bool = False


def get_settings() -> Settings:
    """Get fresh settings instance (no cache to allow live .env updates)"""
    return Settings()
