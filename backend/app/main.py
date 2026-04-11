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

# Register local documentation routes (DISABLED - missing static dir)
# register_docs_routes(app)


@app.on_event("startup")
async def startup_event():
    """Application startup - initialize database and services"""
    logger.info("Starting Crazy Lister v3.0")

    # Start BrowserWorker (dedicated event loop thread for Playwright on Windows)
    from app.services.browser_worker import get_browser_worker
    worker = get_browser_worker()
    worker.start()
    logger.info("BrowserWorker initialized")

    # Create database tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    # Seed Mock Seller Data ONLY on first run (if table is empty)
    from app.models.seller import Seller
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        existing_seller = db.query(Seller).first()
        
        if not existing_seller:
            # Only seed if the database is empty. 
            # If user changed settings, we do NOT overwrite them here.
            logger.info("Seeding Initial Mock Seller Data...")
            mock_seller = Seller(
                lwa_client_id="test123",
                lwa_client_secret="test123",
                lwa_refresh_token="Atzr|test123",
                amazon_seller_id="MOCK-SELLER-01",
                display_name="My AWS Account",
                marketplace_id="ARBP9OOSHTCHU",
                region="EU",
                is_connected=True  # Auto-connect for mock mode
            )
            db.add(mock_seller)
            db.commit()
            logger.info("Mock Seller Data Seeded.")
    except Exception as e:
        logger.error(f"Error seeding mock data: {e}")
        db.rollback()
    finally:
        db.close()

    # Start task manager
    from app.tasks.task_manager import task_manager
    asyncio.create_task(task_manager.start())
    logger.info("Task manager started")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown - cleanup resources"""
    logger.info("Shutting down Crazy Lister v3.0")

    # Stop BrowserWorker
    from app.services.browser_worker import get_browser_worker
    worker = get_browser_worker()
    worker.stop()
    logger.info("BrowserWorker stopped")

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
