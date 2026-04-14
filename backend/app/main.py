"""
Crazy Lister v3.0 - Amazon SP-API Desktop App
Main FastAPI application entry point
"""
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import sys

from app.config import get_settings
from app.api.router import api_router
from app.docs import register_docs_routes
from app.database import engine, Base, init_db

# Get settings
settings = get_settings()

# Setup logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Amazon SP-API Auto-Listing System - Desktop Application v3.0",
    version="3.0.0",
    docs_url="/docs",      # Re-enable default swagger
    redoc_url="/redoc",     # Re-enable default redoc
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files for images (Data/images)
# __file__ = backend/app/main.py → parent.parent.parent = amazon/
images_dir = Path(__file__).parent.parent.parent / "Data" / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount(f"{settings.API_V1_PREFIX}/images/static", StaticFiles(directory=str(images_dir)), name="images")

# Register local documentation routes (DISABLED - missing static dir)
# register_docs_routes(app)


@app.on_event("startup")
async def startup_event():
    """Application startup - initialize database and services"""
    logger.info("Starting Crazy Lister v3.0")

    # Create database tables
    logger.info("Initializing database...")
    init_db()

    # Auto-add missing columns (migration)
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("products")]
    new_cols = [
        ("material", "VARCHAR(200)", "''"),
        ("number_of_items", "INTEGER", "1"),
        ("unit_count", "TEXT", "NULL"),
        ("target_audience", "VARCHAR(100)", "''"),
    ]
    with engine.connect() as conn:
        for name, dtype, default in new_cols:
            if name not in columns:
                try:
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN {name} {dtype} DEFAULT {default}"))
                    conn.commit()
                    logger.info(f"Added column: {name}")
                except Exception as e:
                    logger.warning(f"Column {name} migration skipped: {e}")

    logger.info("Database initialized successfully")

    # Production: No mock data seeding - user must configure real seller credentials
    logger.info("Production mode - no mock data. Configure seller via Settings.")

    # Start task manager
    from app.tasks.task_manager import task_manager
    asyncio.create_task(task_manager.start())
    logger.info("Task manager started")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown - cleanup resources"""
    logger.info("Shutting down Crazy Lister v3.0")

    # Stop task manager
    from app.tasks.task_manager import task_manager
    task_manager.stop()
    logger.info("Task manager stopped")


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "3.0.0",
        "app_name": settings.APP_NAME,
    }

@app.get("/debug/tables")
async def debug_tables():
    from sqlalchemy import inspect
    inspector = inspect(engine)
    return {"tables": inspector.get_table_names()}


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Crazy Lister v3.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8765,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
