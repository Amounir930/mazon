"""
Browser Authentication
Playwright-based login to Amazon Seller Central.

NOTE: Playwright async API has issues with Uvicorn's event loop on Windows.
We use sync API inside a ThreadPoolExecutor to avoid subprocess issues.
"""
import os
import asyncio
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Browser login unavailable.")

# Thread pool for running sync Playwright code
_executor = ThreadPoolExecutor(max_workers=2)


# Amazon Seller Central URLs - Egypt only
SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
}

# Anti-detection browser arguments (from ALister analysis)
ANTI_DETECTION_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-client-side-phishing-detection",
    "--remote-allow-origins=*",
    "--no-first-run",
    "--no-service-autorun",
    "--no-default-browser-check",
    "--homepage=about:blank",
    "--no-pings",
    "--password-store=basic",
    "--disable-infobars",
    "--disable-breakpad",
    "--disable-component-update",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-networking",
    "--disable-dev-shm-usage",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-session-crashed-bubble",
    "--disable-web-security",
    "--disable-features=TranslateUI",
]

# Profile storage
PROFILE_BASE = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyListerProfiles"
PROFILE_BASE.mkdir(parents=True, exist_ok=True)


class BrowserAuth:
    """Amazon Seller Central browser login via Playwright (sync API in thread)"""

    def __init__(self, email: str, password: str, country_code: str = "us"):
        self.email = email
        self.password = password
        self.country_code = country_code.lower()
        self._otp: Optional[str] = None
        self._browser = None
        self._context = None
        self._page = None

        if self.country_code not in SELLER_CENTRAL_BASE:
            raise ValueError(f"Unsupported country code: {country_code}. Use: {list(SELLER_CENTRAL_BASE.keys())}")

        self.base_url = SELLER_CENTRAL_BASE[self.country_code]

    async def login(self, otp: Optional[str] = None) -> dict:
        """
        Execute browser login in a thread pool to avoid async subprocess issues.
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "error": "Playwright not installed"}

        if otp:
            self._otp = otp

        # Run sync Playwright code in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: self._login_sync(otp),
        )
        return result

    def _login_sync(self, otp: Optional[str] = None) -> dict:
        """
        Synchronous browser login using Playwright sync API.
        This runs in a separate thread, avoiding Uvicorn's async loop issues.
        """
        if otp:
            self._otp = otp

        profile_dir = PROFILE_BASE / self.email
        profile_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[SYNC] Launching browser for {self.email} ({self.country_code})")

        playwright = sync_playwright().start()
        try:
            browser = playwright.chromium.launch(
                headless=False,
                args=ANTI_DETECTION_ARGS,
            )

            context = browser.new_context(
                no_viewport=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="ar-EG",
            )

            page = context.new_page()

            # Anti-detection scripts
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['ar-EG', 'en-US', 'en'] });
                Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                window.outerWidth = 1280;
                window.outerHeight = 800;
            """)

            self._browser = browser
            self._context = context
            self._page = page

            # Navigate to seller central
            home_url = f"{self.base_url}/home"
            logger.info(f"[SYNC] Navigating to: {home_url}")
            page.goto(home_url, wait_until="domcontentloaded", timeout=60000)

            # Run state machine
            result = self._state_machine_sync()

            if result.get("needs_otp"):
                return result

            if result.get("success"):
                cookies = context.cookies()
                seller_name = self._get_seller_name_sync(page)

                return {
                    "success": True,
                    "cookies": cookies,
                    "seller_name": seller_name,
                    "country_code": self.country_code,
                }

            return result

        except Exception as e:
            logger.error(f"[SYNC] Browser login failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if self._browser:
                self._browser.close()
                logger.info("[SYNC] Browser closed")

    def _state_machine_sync(self) -> dict:
        """
        Synchronous state machine to track login flow pages.
        """
        max_iterations = 90  # 3 minutes max
        iteration = 0

        while iteration < max_iterations:
            time.sleep(2)
            iteration += 1

            try:
                current_url = self._page.url
                logger.debug(f"[SYNC] State iteration {iteration}: {current_url}")

                # Success: reached home/dashboard
                if "/home" in current_url or "/dashboard" in current_url or ("sellercentral" in current_url and "/ap/" not in current_url):
                    title = self._page.title()
                    if "Sign in" not in title:
                        logger.info(f"[SYNC] Login successful! Page title: {title}")
                        return {"success": True}

                # Sign-in page: fill credentials
                if "/ap/signin" in current_url or "/signin" in current_url:
                    self._fill_credentials_sync()

                # OTP / MFA page
                elif "/ap/mfa" in current_url or "/otp" in current_url or "two-step" in current_url.lower():
                    if not self._otp:
                        logger.info("[SYNC] OTP page detected - waiting for OTP")
                        return {
                            "success": False,
                            "needs_otp": True,
                            "message": "OTP مطلوب - يرجى إدخال رمز التحقق",
                        }
                    self._fill_otp_sync()

                # Account switcher
                elif "/account-switcher" in current_url:
                    self._handle_account_switch_sync()

                else:
                    logger.warning(f"[SYNC] Unknown page: {current_url}")
                    if iteration % 10 == 0:
                        logger.info(f"[SYNC] Still waiting... ({iteration * 2}s)")

            except Exception as e:
                logger.error(f"[SYNC] State machine error: {e}")
                return {"success": False, "error": str(e)}

        return {
            "success": False,
            "error": f"timeout - ما دخلش خلال {max_iterations * 2} ثانية",
        }

    def _fill_credentials_sync(self):
        """Fill email and password"""
        page = self._page

        try:
            # Check for "Switch accounts" page
            switch_heading = page.query_selector('//h1[contains(text(),"Switch accounts")]')
            if switch_heading:
                add_btn = page.query_selector('//*[contains(text(),"Add account")]')
                if add_btn:
                    add_btn.click()
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"[SYNC] Could not check switch accounts: {e}")

        # Email
        try:
            email_input = page.query_selector('input[name="email"]')
            if email_input:
                email_input.fill(self.email)

            continue_btn = page.query_selector('input#continue')
            if continue_btn:
                continue_btn.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"[SYNC] Could not fill email: {e}")

        # Password
        try:
            password_input = page.query_selector('input[name="password"]')
            if password_input:
                password_input.fill(self.password)

            remember = page.query_selector('input[name="rememberMe"]')
            if remember:
                try:
                    remember.check()
                except Exception:
                    pass

            submit = page.query_selector('#signInSubmit')
            if submit:
                submit.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)
        except Exception as e:
            logger.warning(f"[SYNC] Could not fill password: {e}")

        # Check for errors
        try:
            error = page.query_selector('#auth-error-message-box')
            if error:
                error_text = error.inner_text()
                raise Exception(f"Amazon login error: {error_text}")
        except Exception as e:
            if "Amazon login error" in str(e):
                raise

    def _fill_otp_sync(self):
        """Fill OTP"""
        page = self._page

        try:
            otp_input = page.query_selector('input[name="otpCode"]')
            if otp_input:
                otp_input.fill(self._otp)

            remember_device = page.query_selector('input[name="rememberDevice"]')
            if remember_device:
                try:
                    remember_device.check()
                except Exception:
                    pass

            submit_btn = page.query_selector('#auth-signin-button')
            if submit_btn:
                submit_btn.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3)
        except Exception as e:
            logger.warning(f"[SYNC] Could not fill OTP: {e}")

    def _handle_account_switch_sync(self):
        """Handle account switcher page"""
        try:
            add_btn = self._page.query_selector('//*[contains(text(),"Add account")]')
            if add_btn:
                add_btn.click()
                self._page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            logger.warning(f"[SYNC] Could not handle account switch: {e}")

    def _get_seller_name_sync(self, page: Page) -> str:
        """Extract seller name from page"""
        try:
            name_el = page.query_selector('[data-testid="account-name"]')
            if name_el:
                return name_el.inner_text().strip()
        except Exception:
            pass

        return self.email

    async def verify_session(self, cookies: List[Dict[str, Any]]) -> bool:
        """Verify cookies are still valid"""
        import niquests

        session = niquests.AsyncSession()
        for cookie in cookies:
            session.cookies.set(
                cookie.get("name", ""),
                cookie.get("value", ""),
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )

        try:
            url = f"{self.base_url}/home"
            resp = await session.get(url, timeout=30, allow_redirects=True)
            return "/ap/signin" not in str(resp.url)
        except Exception as e:
            logger.warning(f"Session verification failed: {e}")
            return False
        finally:
            await session.close()
