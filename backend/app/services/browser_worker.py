"""
Browser Worker - Process-based Playwright on Windows
Process منفصل تماماً - من غير ProactorEventLoop issues
"""
import os
import time
import multiprocessing
from typing import Dict, Any
from pathlib import Path
from loguru import logger

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed.")

PROFILE_BASE = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "CrazyListerProfiles"
PROFILE_BASE.mkdir(parents=True, exist_ok=True)
SELLER_CENTRAL_BASE = {"eg": "https://sellercentral.amazon.eg"}
ANTI_DETECTION_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-client-side-phishing-detection",
    "--no-first-run",
    "--no-service-autorun",
    "--no-default-browser-check",
    "--no-pings",
    "--password-store=basic",
    "--disable-infobars",
    "--disable-component-update",
    "--disable-background-networking",
    "--disable-dev-shm-usage",
]


def _browser_process(email, password, country_code, otp, result_dict):
    """بيشتغل في process منفصل تماماً"""
    try:
        profile_dir = PROFILE_BASE / email
        profile_dir.mkdir(parents=True, exist_ok=True)

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=False, args=ANTI_DETECTION_ARGS)
        ctx = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ar-EG",
        )
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        base = SELLER_CENTRAL_BASE.get(country_code)
        if not base:
            result_dict["error"] = f"Unsupported country: {country_code}"
            result_dict["done"] = True
            return

        page.goto(f"{base}/home", wait_until="domcontentloaded", timeout=60000)

        for i in range(90):
            time.sleep(2)
            url = page.url

            if "/home" in url or ("/sellercentral" in url and "/ap/" not in url):
                title = page.title()
                if "Sign in" not in title:
                    cookies = ctx.cookies()
                    seller = "Unknown"
                    try:
                        el = page.query_selector('[data-testid="account-name"]')
                        if el:
                            seller = el.inner_text().strip()
                    except Exception:
                        pass
                    result_dict.update({"success": True, "cookies": cookies, "seller_name": seller, "country_code": country_code, "done": True})
                    browser.close()
                    pw.stop()
                    return

            if "/ap/signin" in url or "/signin" in url:
                try:
                    email_el = page.query_selector('input[name="email"]')
                    if email_el:
                        email_el.fill(email)
                        btn = page.query_selector('input#continue')
                        if btn:
                            btn.click()
                            page.wait_for_load_state("domcontentloaded")
                            time.sleep(1)
                except Exception:
                    pass
                try:
                    pw_el = page.query_selector('input[name="password"]')
                    if pw_el:
                        pw_el.fill(password)
                        submit = page.query_selector('#signInSubmit')
                        if submit:
                            submit.click()
                            page.wait_for_load_state("domcontentloaded")
                            time.sleep(2)
                except Exception:
                    pass

            elif ("/ap/mfa" in url or "two-step" in url.lower()) and otp:
                try:
                    otp_el = page.query_selector('input[name="otpCode"]')
                    if otp_el:
                        otp_el.fill(otp)
                        btn = page.query_selector('#auth-signin-button')
                        if btn:
                            btn.click()
                            page.wait_for_load_state("domcontentloaded")
                            time.sleep(3)
                except Exception:
                    pass

        result_dict["error"] = "timeout"
        result_dict["done"] = True
        browser.close()
        pw.stop()

    except Exception as e:
        logger.error(f"[BrowserProcess] Failed: {e}")
        result_dict.update({"success": False, "error": str(e), "done": True})


class BrowserWorker:
    def __init__(self):
        self._started = False

    def start(self):
        self._started = True
        logger.info("BrowserWorker ready")

    def stop(self):
        logger.info("BrowserWorker stopped")


_browser_worker = BrowserWorker()


def get_browser_worker() -> BrowserWorker:
    return _browser_worker


async def browser_login(email: str, password: str, country_code: str, otp: str = None) -> Dict[str, Any]:
    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "error": "Playwright not installed"}

    manager = multiprocessing.Manager()
    result = manager.dict({"done": False})

    process = multiprocessing.Process(
        target=_browser_process,
        args=(email, password, country_code, otp, result),
        daemon=True,
    )
    process.start()

    # استنى النتيجة
    waited = 0
    while not result.get("done") and waited < 180:
        time.sleep(1)
        waited += 1

    if not result.get("done"):
        process.terminate()
        process.join(timeout=5)
        return {"success": False, "error": "timeout"}

    return dict(result)


async def browser_submit_otp(session_id: str, otp: str) -> Dict[str, Any]:
    return {"success": False, "error": "OTP not supported"}
