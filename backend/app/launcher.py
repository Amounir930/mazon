"""
Crazy Lister v3.0 — Desktop Launcher
Entry point for the standalone Windows desktop application.

This module:
1. Starts FastAPI backend on a background thread
2. Waits for the server to be ready
3. Opens PyWebView window with the React frontend
4. Handles graceful shutdown when the window is closed
"""
import os
import sys
import time
import signal
import threading
import asyncio
import socket
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

import uvicorn
import webview
from loguru import logger

# ============================================================
# 1. PATH RESOLUTION (PyInstaller compatible)
# ============================================================

if getattr(sys, 'frozen', False):
    # Running as compiled .exe — files are in _MEIPASS
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Development mode
    BASE_DIR = Path(__file__).parent.parent

# ============================================================
# 2. APPDATA PATHS (No Admin permissions needed)
# ============================================================

APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = APP_DATA_DIR / "uploads"
EXPORT_DIR = APP_DATA_DIR / "exports"
LOG_FILE = APP_DATA_DIR / "crazy_lister.log"

for d in [UPLOAD_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Set environment variables for the app to use
os.environ["APP_DATA_DIR"] = str(APP_DATA_DIR)
os.environ["UPLOAD_DIR"] = str(UPLOAD_DIR)
os.environ["EXPORT_DIR"] = str(EXPORT_DIR)

# ============================================================
# 3. LOGGING SETUP
# ============================================================

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <6}</level> | <level>{message}</level>"
)
logger.add(
    str(LOG_FILE),
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <6} | {message}"
)

# ============================================================
# 4. BACKEND SERVER MANAGEMENT
# ============================================================

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8765
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

_server_thread = None
_server_started = False
_shutdown_event = threading.Event()


def _run_server():
    """Run FastAPI server in background thread"""
    global _server_started

    # Set up database before starting server
    import app.database as db_module
    db_module.APP_DATA_DIR = APP_DATA_DIR
    db_module.DATABASE_URL = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"

    logger.info(f"Starting FastAPI backend on {BACKEND_URL}...")

    try:
        uvicorn.run(
            "app.main:app",
            host=BACKEND_HOST,
            port=BACKEND_PORT,
            log_level="warning",
        )
    except Exception as e:
        logger.error(f"❌ Uvicorn failed: {e}")
        raise


def start_backend():
    """Start the backend server in a daemon thread"""
    global _server_thread

    _server_thread = threading.Thread(target=_run_server, daemon=True, name="BackendServer")
    _server_thread.start()
    logger.info("Backend server thread started")


def wait_for_server(timeout: int = 30) -> bool:
    """
    Wait for the backend server to be ready.
    Polls the /health endpoint until it responds.
    """
    logger.info(f"Waiting for backend server (timeout: {timeout}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = urlopen(f"{BACKEND_URL}/health", timeout=1)
            if response.status == 200:
                logger.info("✅ Backend server is ready!")
                return True
        except (URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(0.5)

    logger.error("❌ Backend server failed to start within timeout")
    return False


def stop_backend():
    """Signal the backend server to stop"""
    logger.info("Stopping backend server...")
    _shutdown_event.set()


# ============================================================
# 5. FRONTEND PATH RESOLUTION
# ============================================================

def get_frontend_path() -> str:
    """Get the path to the built frontend"""
    if getattr(sys, 'frozen', False):
        # Running as .exe — frontend is bundled in _MEIPASS
        frontend_path = BASE_DIR / "frontend" / "dist" / "index.html"
    else:
        # Development mode — frontend is in sibling directory
        frontend_path = BASE_DIR.parent / "frontend" / "dist" / "index.html"

    return str(frontend_path)


def get_icon_path() -> str:
    """Get the path to the application icon"""
    if getattr(sys, 'frozen', False):
        # Running as .exe — icon is bundled in _MEIPASS
        icon_path = BASE_DIR / "assets" / "icon.ico"
    else:
        # Development mode — icon is in project root
        icon_path = BASE_DIR.parent / "assets" / "icon.ico"

    return str(icon_path)


# ============================================================
# 7. MAIN ENTRY POINT
# ============================================================

def main():
    """Main entry point — double-click to run"""
    logger.info("=" * 60)
    logger.info("  Crazy Lister v3.0 — Desktop App")
    logger.info("=" * 60)

    # Verify frontend exists
    frontend_path = get_frontend_path()
    if not os.path.exists(frontend_path):
        logger.error(f"❌ Frontend not found: {frontend_path}")
        logger.error("Run 'npm run build' in frontend/ first!")
        try:
            input("Press Enter to exit...")
        except (RuntimeError, EOFError):
            pass  # stdin not available in frozen .exe
        sys.exit(1)

    logger.info(f"✅ Frontend: {frontend_path}")
    logger.info(f"✅ Data directory: {APP_DATA_DIR}")

    # Start backend in background thread
    start_backend()

    # Wait for backend to be ready
    if not wait_for_server(timeout=15):
        logger.error("❌ Failed to start backend — exiting")
        input("Press Enter to exit...")
        sys.exit(1)

    # Create PyWebView window
    logger.info("Creating desktop window...")

    # Normalize path for Windows (convert backslashes to forward slashes)
    file_url = f"file:///{os.path.abspath(frontend_path).replace(chr(92), '/')}"

    # Prepare window parameters
    # Load from backend HTTP server (NOT file://) to avoid CORS and fetch() issues
    window_params = {
        "title": "Crazy Lister v3.0",
        "url": BACKEND_URL,  # http://127.0.0.1:8765 — backend serves the frontend
        "width": 1280,
        "height": 850,
        "min_size": (900, 600),
        "resizable": True,
        "background_color": "#0a0a0f",
    }

    window = webview.create_window(**window_params)

    # Set up closing event handler
    def on_closing():
        """Called when the user closes the PyWebView window"""
        logger.info("Window closing — shutting down gracefully...")

        # Stop backend
        stop_backend()

        # Stop task manager
        try:
            from app.tasks.task_manager import task_manager
            task_manager.stop()
            logger.info("Task manager stopped")
        except Exception as e:
            logger.warning(f"Error stopping task manager: {e}")

        logger.info("Crazy Lister shutdown complete")
        return True  # Allow the window to close

    # Bind closing event (pywebview 4.x compatible)
    window.events.closing += on_closing

    logger.info("🚀 Starting PyWebView UI...")
    webview.start()


if __name__ == "__main__":
    main()
