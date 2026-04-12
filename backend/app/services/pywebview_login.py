"""
Amazon Login (via PyWebView subprocess)
بيشغل script منفصل لعزل PyWebView عن FastAPI
"""
import os
import sys
import json
import time
import tempfile
from typing import Dict, Any
from loguru import logger

# Use PyWebView script (working with Amazon Egypt)
STANDALONE_SCRIPT = os.path.join(os.path.dirname(__file__), "amazon_login_standalone.py")


async def start_amazon_login(country_code: str = "eg") -> Dict[str, Any]:
    """
    بيشغل standalone script اللي بيفتح PyWebView ويقرأ الـ cookies.
    """
    output_file = os.path.join(tempfile.gettempdir(), f"amzn_login_{int(time.time())}.json")
    
    env = os.environ.copy()
    env["AMZN_COUNTRY"] = country_code
    env["AMZN_OUTPUT"] = output_file
    env["PYTHONIOENCODING"] = "utf-8"
    
    logger.info(f"Launching Amazon login script (country={country_code})")
    logger.info(f"Output file: {output_file}")
    
    # Launch in background - don't wait for it
    import subprocess
    try:
        # Use pythonw.exe (no console) if available, otherwise python.exe
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(python_exe):
            python_exe = sys.executable
        
        # Start the login script - DETACHED_PROCESS so it runs independently
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
        
        proc = subprocess.Popen(
            [python_exe, "-u", STANDALONE_SCRIPT],
            env=env,
            startupinfo=startupinfo,
            creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
        )
        logger.info(f"Login script launched (PID={proc.pid})")
    except Exception as e:
        logger.error(f"Failed to launch login script: {e}", exc_info=True)
        return {"success": False, "error": f"فشل فتح نافذة تسجيل الدخول: {e}", "cookies": []}
    
    # Poll for result file
    max_wait = 300  # 5 minutes
    waited = 0
    
    while waited < max_wait:
        time.sleep(1)
        waited += 1
        
        if os.path.exists(output_file):
            try:
                # Make sure file is fully written
                time.sleep(0.5)
                with open(output_file, "r", encoding="utf-8") as f:
                    result = json.load(f)
                logger.info(f"Login result: success={result.get('success')}, cookies={len(result.get('cookies', []))}")
                return result
            except (json.JSONDecodeError, IOError):
                # File might still be being written
                continue
    
    # Timeout
    logger.warning("Login timed out")
    return {"success": False, "error": "انتهت المهلة - لم يتم تسجيل الدخول", "cookies": []}


async def get_login_status(session_id: str) -> Dict[str, Any]:
    """Not supported in standalone mode"""
    return {"status": "not_supported"}
