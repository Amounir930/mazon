"""
Database Configuration
SQLite for local desktop app
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool
from typing import Generator
from loguru import logger

from app.config import get_settings

# Get settings
settings = get_settings()
APP_DATA_DIR = Path(settings.UPLOAD_DIR).parent
DATABASE_URL = settings.DATABASE_URL

logger.info(f"Database initialized with path: {DATABASE_URL}")

# Create engine with better SQLite settings for desktop usage
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides database sessions.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables and run migrations.
    Call this on application startup.
    """
    # Import all models here to ensure they're registered with Base
    from app.models.seller import Seller
    from app.models.product import Product
    from app.models.listing import Listing
    from app.models.session import Session  # noqa: F401
    from app.models.activity_log import ActivityLog  # noqa: F401
    from app.models.setting import Setting  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at: {APP_DATA_DIR}/crazy_lister.db")

    # Run migrations for schema evolution
    from app.migrations import run_migrations
    run_migrations(engine)


# Enable WAL mode for better performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=memory")
    # Enable foreign keys for CASCADE deletes
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
