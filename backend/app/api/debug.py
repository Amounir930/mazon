"""
Debug & Diagnostics API
"""
from fastapi import APIRouter, HTTPException
from app.database import APP_DATA_DIR
from loguru import logger
import os

router = APIRouter()

@router.get("/logs")
async def get_logs(lines: int = 100):
    """
    Get the last N lines of the application log file.
    """
    log_file = APP_DATA_DIR / "crazy_lister.log"
    
    if not log_file.exists():
        return {"logs": [], "message": "Log file not found yet."}
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Read all lines and take the last N
            content = f.readlines()
            last_lines = content[-lines:] if len(content) > lines else content
            return {
                "logs": [line.strip() for line in last_lines],
                "file_path": str(log_file),
                "total_lines": len(content)
            }
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")

@router.get("/status")
async def get_system_status():
    """
    Get basic system diagnostics.
    """
    import platform
    import sys
    from app.config import get_settings, IS_FROZEN
    settings = get_settings()
    
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version,
        "app_data_dir": str(APP_DATA_DIR),
        "db_url": settings.DATABASE_URL,
        "is_frozen": IS_FROZEN,
        "db_exists": (APP_DATA_DIR / "crazy_lister.db").exists(),
        "log_exists": (APP_DATA_DIR / "crazy_lister.log").exists(),
    }

