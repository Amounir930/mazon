"""
Amazon Login via Playwright — Subprocess Mode
Phase 1: Cookie Extraction with Browser Fingerprint Protection

Runs as a DETACHED subprocess to avoid asyncio/ProactorEventLoop issues on Windows.
"""
import os
import sys
import json
import re
import time
import tempfile
import subprocess
from typing import Dict, Any, Optional
from loguru import logger

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "playwright_login_script.py")


async def login_amazon_playwright(country_code: str = "eg", timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Launches a detached subprocess that runs Playwright login.
    Reads result from temp JSON file.
    """
    output_file = os.path.join(tempfile.gettempdir(), f"pw_login_{int(time.time())}.json")

    env = os.environ.copy()
    env["AMZN_COUNTRY"] = country_code
    env["AMZN_OUTPUT"] = output_file
    env["PYTHONIOENCODING"] = "utf-8"

    logger.info(f"Launching Playwright login script (country={country_code})")
    logger.info(f"Output file: {output_file}")

    try:
        python_exe = sys.executable

        # Start the login script
        # On Windows: CREATE_NEW_CONSOLE to show browser window
        # On Linux/Mac: no special flags needed
        startupinfo = None
        creationflags = 0

        if os.name == "nt":
            # Windows: Show the console window and allow browser to appear
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            # CREATE_NEW_CONSOLE instead of DETACHED_PROCESS
            creationflags = subprocess.CREATE_NEW_CONSOLE

        proc = subprocess.Popen(
            [python_exe, "-u", SCRIPT_PATH],
            env=env,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        logger.info(f"Playwright login script launched (PID={proc.pid})")
        logger.info(f"Script path: {SCRIPT_PATH}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Check logs in: {tempfile.gettempdir()}\\pw_login_*.log")
    except Exception as e:
        logger.error(f"Failed to launch Playwright script: {e}", exc_info=True)
        return {"success": False, "error": f"Failed to launch browser: {e}", "cookies": []}

    # Poll for result file
    max_wait = timeout_seconds
    waited = 0

    while waited < max_wait:
        time.sleep(1)
        waited += 1

        if os.path.exists(output_file):
            try:
                time.sleep(0.5)  # Make sure file is fully written
                with open(output_file, "r", encoding="utf-8") as f:
                    result = json.load(f)
                logger.info(f"Playwright login result: success={result.get('success')}, cookies={len(result.get('cookies', []))}")
                return result
            except (json.JSONDecodeError, IOError):
                continue

    logger.warning("Playwright login timed out")
    return {"success": False, "error": "انتهت المهلة - لم يتم تسجيل الدخول", "cookies": []}


def extract_csrf_token(html_content: str) -> Optional[str]:
    """Extract CSRF Token via Regex from HTML content."""
    patterns = [
        r'"anti-csrftoken-a2z"\s*:\s*"([^"]+)"',
        r"'anti-csrftoken-a2z'\s*:\s*'([^']+)'",
        r'anti-csrftoken-a2z["\']\s*:\s*["\']([^"\']+)["\']',
        r'<meta[^>]*anti-csrf-token[^>]*content=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            token = match.group(1).strip()
            # Validate: must be > 40 chars and NOT an A/B test token
            if len(token) > 40 and not re.match(r'^(mons_|.*_treatment|.*_experiment|.*_weblab|^ab)', token, re.IGNORECASE):
                return token
    return None
