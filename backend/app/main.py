"""
Crazy Lister v3.0 - Amazon SP-API Desktop App
Main FastAPI application entry point
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import get_settings
from app.api.router import api_router
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
    docs_url=None,      # Disable default swagger (CDN blocked)
    redoc_url=None,     # Disable default redoc (CDN blocked)
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


@app.on_event("startup")
async def startup_event():
    """Application startup - initialize database and services"""
    logger.info("Starting Crazy Lister v3.0")

    # Create database tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

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
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
