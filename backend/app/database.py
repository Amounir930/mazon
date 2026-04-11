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

# Windows AppData path
APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{APP_DATA_DIR.as_posix()}/crazy_lister.db"
logger.info(f"Database URL configured as: {DATABASE_URL}")

# SQLite-specific engine config
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
    Initialize database - create all tables and seed initial data.
    Call this on application startup.
    """
    # Import all models here to ensure they're registered with Base
    from app.models.seller import Seller
    from app.models.product import Product
    from app.models.listing import Listing
    from app.models.session import Session  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at: {APP_DATA_DIR}/crazy_lister.db")

    # Seed initial mock seller if database is empty
    from app.config import get_settings
    settings = get_settings()
    if getattr(settings, 'USE_AMAZON_MOCK', False):
        db = SessionLocal()
        try:
            existing_seller = db.query(Seller).first()
            if not existing_seller:
                mock_seller = Seller(
                    lwa_client_id="test123",
                    lwa_client_secret="test123",
                    lwa_refresh_token="Atzr|test123",
                    amazon_seller_id="test123",
                    display_name="Mock Seller",
                    marketplace_id="ARBP9OOSHTCHU",
                    region="EU",
                    is_connected=True,
                )
                db.add(mock_seller)
                db.commit()
                logger.info("Seeded mock seller for development")
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not seed mock seller: {e}")
        finally:
            db.close()


# Enable WAL mode for better performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=memory")
    cursor.close()
