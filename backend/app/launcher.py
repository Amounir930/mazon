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
import traceback
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
# 2. DATA PATHS (Consistent with app/config.py)
# ============================================================

if getattr(sys, 'frozen', False):
    # Production (EXE): Use Standard Windows Roaming AppData with a distinct folder
    APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyListerV3-Release"
else:
    # Development: Use local dev_data folder
    # launcher.py is in backend/app/
    APP_DATA_DIR = Path(__file__).resolve().parent.parent / "dev_data"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = APP_DATA_DIR / "uploads"
EXPORT_DIR = APP_DATA_DIR / "exports"
LOG_FILE = APP_DATA_DIR / "crazy_lister.log"

for d in [UPLOAD_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Set environment variables for the app to use
os.environ["APP_DATA_DIR"] = str(APP_DATA_DIR)


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

    # Logger will show the path from database.py initialization
    logger.info(f"Starting FastAPI backend on {BACKEND_URL}...")


    try:
        # Import app directly to catch any import-time errors in this thread
        from app.main import app
        
        uvicorn.run(
            app,  # Pass the app object directly
            host=BACKEND_HOST,
            port=BACKEND_PORT,
            log_level="warning",
        )
    except Exception as e:
        error_tb = traceback.format_exc()
        logger.error(f"❌ Uvicorn failed to start:\n{error_tb}")
        # Save error to a special file for the main process to see
        with open(APP_DATA_DIR / "last_error.txt", "w", encoding="utf-8") as f:
            f.write(error_tb)
        # Signal failure to the main thread
        _shutdown_event.set()
        raise


def start_backend():
    """Start the backend server in a daemon thread"""
    global _server_thread

    _server_thread = threading.Thread(target=_run_server, daemon=True, name="BackendServer")
    _server_thread.start()
    logger.info("Backend server thread started")


def wait_for_server(timeout: int = 60) -> bool:
    """
    Wait for the backend server to be ready.
    Polls the /health endpoint until it responds.
    """
    logger.info(f"Waiting for backend server (timeout: {timeout}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if the server thread already crashed
        if _shutdown_event.is_set():
            logger.error("❌ Backend server thread signaled failure")
            return False

        try:
            response = urlopen(f"{BACKEND_URL}/health", timeout=1)
            if response.status == 200:
                logger.info("✅ Backend server is ready!")
                return True
        except (URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(1.0)

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
        if not getattr(sys, 'frozen', False) and sys.stdin and sys.stdin.isatty():
            try:
                input("Press Enter to exit...")
            except (RuntimeError, EOFError):
                pass
        sys.exit(1)

    logger.info(f"✅ Frontend: {frontend_path}")
    logger.info(f"✅ Data directory: {APP_DATA_DIR}")

    # Start backend in background thread
    start_backend()

    # Wait for backend to be ready
    if not wait_for_server(timeout=60):
        logger.error("❌ Failed to start backend — exiting")
        
        # Try to show error in a message box if possible
        last_error_file = APP_DATA_DIR / "last_error.txt"
        error_msg = "Backend server failed to start."
        if last_error_file.exists():
            error_msg = last_error_file.read_text(encoding="utf-8")
        
        # We can't use webview yet as start() hasn't been called
        # But we can try a basic tkinter message box if available
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Crazy Lister - Error", f"Failed to start backend:\n\n{error_msg[:500]}...")
            root.destroy()
        except:
            pass
            
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
