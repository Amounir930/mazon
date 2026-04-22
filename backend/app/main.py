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

from dotenv import load_dotenv

from app.config import get_settings, get_env_path
# Ensure environment variables are universally loaded into os.environ
load_dotenv(get_env_path(), override=False)

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

# Mount static files for uploaded images (Data/images)
from app.database import APP_DATA_DIR
images_dir = APP_DATA_DIR / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount(f"{settings.API_V1_PREFIX}/images/static", StaticFiles(directory=str(images_dir)), name="images")

# Mount frontend static files (React build) — must come AFTER API routes
# Supports both dev (sibling frontend/dist) and frozen .exe (_MEIPASS/frontend/dist)
import os, sys as _sys
_base = Path(_sys._MEIPASS) if getattr(_sys, 'frozen', False) else Path(__file__).parent.parent.parent
_frontend_dist = _base / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="frontend-assets")
    logger.info(f"Frontend static assets mounted from: {_frontend_dist}")
else:
    logger.warning(f"Frontend dist not found at: {_frontend_dist} — UI may not load")

# Register local documentation routes (DISABLED - missing static dir)
# register_docs_routes(app)


@app.on_event("startup")
async def startup_event():
    """Application startup - initialize database and services"""
    logger.info("Starting Crazy Lister v3.0")

    # Enable file logging in production/frozen mode or if configured
    log_file = APP_DATA_DIR / "crazy_lister.log"
    logger.add(
        log_file,
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )
    logger.info(f"File logging enabled: {log_file}")

    # Create database tables
    logger.info("Initializing database...")
    init_db()

    logger.info("Database initialized successfully")

    
    # 3. Sync Sellers table with .env SP-API credentials (Single Seller source of truth)
    from app.models.seller import Seller
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        sp_seller_id = getattr(settings, "SP_API_SELLER_ID", None)
        if sp_seller_id:
            # Try to find existing seller (either by ID or just the first one)
            existing_seller = db.query(Seller).filter(Seller.amazon_seller_id == sp_seller_id).first()
            if not existing_seller:
                existing_seller = db.query(Seller).first()

            if not existing_seller:
                # Create new
                new_seller = Seller(
                    amazon_seller_id=sp_seller_id,
                    lwa_client_id=getattr(settings, "SP_API_CLIENT_ID", ""),
                    lwa_client_secret=getattr(settings, "SP_API_CLIENT_SECRET", ""),
                    lwa_refresh_token=getattr(settings, "SP_API_REFRESH_TOKEN", ""),
                    display_name=f"Amazon - {sp_seller_id}",
                    marketplace_id=getattr(settings, "SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU"),
                    region=getattr(settings, "AWS_REGION", "eu-west-1"),
                    is_connected=True
                )
                db.add(new_seller)
                logger.info(f"✨ Created Seller from .env: {sp_seller_id}")
            else:
                # Sync existing with .env
                existing_seller.amazon_seller_id = sp_seller_id
                existing_seller.lwa_client_id = getattr(settings, "SP_API_CLIENT_ID", existing_seller.lwa_client_id)
                existing_seller.lwa_client_secret = getattr(settings, "SP_API_CLIENT_SECRET", existing_seller.lwa_client_secret)
                existing_seller.lwa_refresh_token = getattr(settings, "SP_API_REFRESH_TOKEN", existing_seller.lwa_refresh_token)
                existing_seller.is_connected = True
                logger.info(f"🔄 Synced Seller record with .env credentials: {sp_seller_id}")
            
            db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"⚠️ Could not sync seller from .env: {e}")
    finally:
        db.close()


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
    """Serve the React frontend index.html"""
    from fastapi.responses import FileResponse
    import sys as _sys
    _base = Path(_sys._MEIPASS) if getattr(_sys, 'frozen', False) else Path(__file__).parent.parent.parent
    index = _base / "frontend" / "dist" / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return {"message": "Frontend not built. Run 'npm run build' in frontend/.", "docs": "/docs"}


@app.get("/{full_path:path}", tags=["spa"])
async def spa_fallback(full_path: str):
    """SPA catch-all — return index.html for all non-API routes (React Router)"""
    # Skip API, docs, health, static paths
    if full_path.startswith(("api/", "docs", "redoc", "openapi", "health", "debug")):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    from fastapi.responses import FileResponse
    import sys as _sys
    _base = Path(_sys._MEIPASS) if getattr(_sys, 'frozen', False) else Path(__file__).parent.parent.parent
    index = _base / "frontend" / "dist" / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8765,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
