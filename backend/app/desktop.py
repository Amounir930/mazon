"""
Desktop App Launcher (Alternative Entry Point)
Starts FastAPI backend + PyWebView frontend window

This is an alternative to launcher.py — both work the same way.
Use this if you want a simpler, more straightforward launcher.
"""
import os
import sys
import threading
import time
from pathlib import Path
import uvicorn
import webview
from loguru import logger

# ============================================================
# Path Resolution for PyInstaller
# ============================================================
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    BASE_DIR = Path(sys._MEIPASS)
    APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
else:
    # Development mode
    BASE_DIR = Path(__file__).parent.parent
    APP_DATA_DIR = BASE_DIR / "app_data"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Logging Setup
# ============================================================
log_file = APP_DATA_DIR / "crazy_lister.log"
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <6}</level> | <level>{message}</level>"
)
logger.add(
    str(log_file),
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <6} | {message}"
)

# ============================================================
# Backend Server
# ============================================================
def start_backend():
    """Start FastAPI in background thread"""
    logger.info("Starting FastAPI backend on port 8765...")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="warning",
    )

# ============================================================
# Frontend Path
# ============================================================
def get_frontend_path() -> str:
    """Get the path to the built frontend"""
    if getattr(sys, 'frozen', False):
        return str(BASE_DIR / "frontend" / "dist" / "index.html")
    else:
        return str(BASE_DIR.parent / "frontend" / "dist" / "index.html")

# ============================================================
# App Launcher
# ============================================================
def create_app():
    """Create and run the desktop application"""
    logger.info("=" * 50)
    logger.info("  Crazy Lister v3.0 — Desktop App")
    logger.info("=" * 50)

    # Verify frontend exists
    frontend_path = get_frontend_path()
    if not os.path.exists(frontend_path):
        logger.error(f"❌ Frontend not found: {frontend_path}")
        logger.error("Run 'npm run build' in frontend/ first!")
        input("Press Enter to exit...")
        sys.exit(1)

    logger.info(f"✅ Frontend: {frontend_path}")
    logger.info(f"✅ Data: {APP_DATA_DIR}")

    # Start backend
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for backend
    time.sleep(2)

    # Create PyWebView window
    window = webview.create_window(
        title="Crazy Lister v3.0",
        url=f"file:///{os.path.abspath(frontend_path).replace(chr(92), '/')}",
        width=1280,
        height=850,
        min_size=(900, 600),
        resizable=True,
        background_color="#0a0a0f",
    )

    logger.info("🚀 Desktop window created. Starting UI...")
    webview.start()

if __name__ == "__main__":
    create_app()
