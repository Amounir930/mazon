"""
Browser Authentication
Playwright-based login to Amazon Seller Central.

Flow:
1. Launch isolated Chromium profile
2. Navigate to sellercentral.amazon.{country}/home
3. State machine handles: signin → password → OTP (if needed) → home
4. Extract cookies on success
5. Browser closes automatically

Security:
- Each email gets isolated browser profile
- headless=False so user can see & interact if needed
- No credentials stored in browser (cookies only, encrypted in DB)
"""
import asyncio
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Browser login unavailable.")


# Amazon Seller Central URLs by country
SELLER_CENTRAL_BASE = {
    "us": "https://sellercentral.amazon.com",
    "uk": "https://sellercentral.amazon.co.uk",
    "de": "https://sellercentral.amazon.de",
    "fr": "https://sellercentral.amazon.fr",
    "it": "https://sellercentral.amazon.it",
    "es": "https://sellercentral.amazon.es",
    "ae": "https://sellercentral.amazon.ae",
    "sa": "https://sellercentral.amazon.sa",
    "eg": "https://sellercentral.amazon.eg",
    "in": "https://sellercentral.amazon.in",
    "jp": "https://sellercentral.amazon.co.jp",
    "ca": "https://sellercentral.amazon.ca",
    "mx": "https://sellercentral.amazon.com.mx",
    "au": "https://sellercentral.amazon.com.au",
    "sg": "https://sellercentral.amazon.sg",
    "nl": "https://sellercentral.amazon.nl",
    "pl": "https://sellercentral.amazon.pl",
    "se": "https://sellercentral.amazon.se",
    "be": "https://sellercentral.amazon.com.be",
    "tr": "https://sellercentral.amazon.com.tr",
    "br": "https://sellercentral.amazon.com.br",
}

# Profile storage
PROFILE_BASE = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyListerProfiles"
PROFILE_BASE.mkdir(parents=True, exist_ok=True)


class BrowserAuth:
    """Amazon Seller Central browser login via Playwright"""

    def __init__(self, email: str, password: str, country_code: str = "us"):
        self.email = email
        self.password = password
        self.country_code = country_code.lower()
        self._otp: Optional[str] = None
        self._browser = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        if self.country_code not in SELLER_CENTRAL_BASE:
            raise ValueError(f"Unsupported country code: {country_code}. Use one of: {list(SELLER_CENTRAL_BASE.keys())}")

        self.base_url = SELLER_CENTRAL_BASE[self.country_code]

    async def login(self, otp: Optional[str] = None) -> dict:
        """
        Execute full browser login flow.

        Args:
            otp: Optional OTP code if already known

        Returns:
            dict with keys:
                - success (bool)
                - cookies (list[dict]) - only on success
                - seller_name (str) - only on success
                - country_code (str) - only on success
                - needs_otp (bool) - True if OTP page detected
                - error (str) - error message on failure
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "error": "Playwright not installed"}

        if otp:
            self._otp = otp

        profile_dir = PROFILE_BASE / self.email
        profile_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Launching browser for {self.email} ({self.country_code})")

        playwright = await async_playwright().start()
        try:
            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    f"--user-data-dir={profile_dir}",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            context = await browser.new_context(
                no_viewport=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            page = await context.new_page()
            self._browser = browser
            self._context = context
            self._page = page

            # Navigate to seller central
            home_url = f"{self.base_url}/home"
            logger.info(f"Navigating to: {home_url}")
            await page.goto(home_url, wait_until="domcontentloaded", timeout=60000)

            # Run state machine
            result = await self._state_machine()

            if result.get("needs_otp"):
                return result

            if result.get("success"):
                cookies = await context.cookies()
                seller_name = await self._extract_seller_name(page)

                return {
                    "success": True,
                    "cookies": cookies,
                    "seller_name": seller_name,
                    "country_code": self.country_code,
                }

            return result

        except Exception as e:
            logger.error(f"Browser login failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if self._browser:
                await self._browser.close()
                logger.info("Browser closed")

    async def _state_machine(self) -> dict:
        """
        State machine to track login flow pages.
        Monitors URL changes and performs actions accordingly.
        """
        max_iterations = 90  # 3 minutes max (2s per iteration)
        iteration = 0

        while iteration < max_iterations:
            await asyncio.sleep(2)
            iteration += 1

            try:
                current_url = self._page.url
                logger.debug(f"Login state iteration {iteration}: {current_url}")

                # Success: reached home/dashboard
                if "/home" in current_url or "/dashboard" in current_url or "sellercentral" in current_url and "/ap/" not in current_url:
                    # Verify we're actually logged in (not redirected to signin)
                    title = await self._page.title()
                    if "Sign in" not in title:
                        logger.info(f"Login successful! Page title: {title}")
                        return {"success": True}

                # Sign-in page: fill credentials
                if "/ap/signin" in current_url or "/signin" in current_url:
                    await self._fill_credentials()

                # OTP / MFA page
                elif "/ap/mfa" in current_url or "/otp" in current_url or "two-step" in current_url.lower():
                    if not self._otp:
                        logger.info("OTP page detected - waiting for user to provide OTP")
                        return {
                            "success": False,
                            "needs_otp": True,
                            "message": "OTP مطلوب - يرجى إدخال رمز التحقق",
                        }
                    await self._fill_otp()

                # Account switcher
                elif "/account-switcher" in current_url:
                    await self._handle_account_switch()

                # Password page (sometimes separate from email)
                elif "/ap/forgotpassword" in current_url:
                    return {"success": False, "error": "Password reset page - check credentials"}

                # CAPTCHA or other verification
                elif "/ap/cvf" in current_url or "captcha" in current_url.lower():
                    return {
                        "success": False,
                        "needs_otp": True,
                        "message": "Amazon يطلب التحقق - أكّده يدوياً في المتصفح",
                    }

                # Unknown page - log but continue
                else:
                    logger.debug(f"Unknown page during login: {current_url}")

            except Exception as e:
                logger.warning(f"State machine error at iteration {iteration}: {e}")
                # Page might be loading, continue
                continue

        return {"success": False, "error": "timeout - فشل تسجيل الدخول خلال 3 دقائق"}

    async def _fill_credentials(self):
        """Fill email and password on the sign-in page"""
        page = self._page

        # Check if we need to click "Add account" first
        try:
            switch_heading = await page.query_selector('h1:has-text("Switch accounts")')
            if switch_heading:
                add_btn = await page.query_selector('text="Add account"')
                if add_btn:
                    await add_btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(1)
        except Exception:
            pass

        # Fill email
        email_input = await page.query_selector('input[name="email"]')
        if email_input:
            await email_input.fill(self.email)

        # Click Continue
        continue_btn = await page.query_selector('input#continue')
        if continue_btn:
            await continue_btn.click()
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1.5)

        # Fill password (may be on same page or after continue)
        password_input = await page.query_selector('input[name="password"]')
        if password_input:
            await password_input.fill(self.password)

        # Check "Keep me signed in"
        remember = await page.query_selector('input[name="rememberMe"]')
        if remember:
            try:
                await remember.check()
            except Exception:
                pass

        # Click Sign In
        submit = await page.query_selector('#signInSubmit')
        if submit:
            await submit.click()
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

        # Check for error messages
        try:
            error_box = await page.query_selector('#auth-error-message-box')
            if error_box:
                error_text = await error_box.inner_text()
                logger.error(f"Amazon login error: {error_text}")
                raise Exception(f"Amazon login error: {error_text}")
        except Exception:
            pass

    async def _fill_otp(self):
        """Fill OTP code on the MFA page"""
        page = self._page

        otp_input = await page.query_selector('input[name="otpCode"]')
        if otp_input:
            await otp_input.fill(self._otp)

        # Check "Don't ask for code on this device again"
        remember = await page.query_selector('input[name="rememberDevice"]')
        if remember:
            try:
                await remember.check()
            except Exception:
                pass

        # Click Sign In
        submit = await page.query_selector('#auth-signin-button')
        if not submit:
            submit = await page.query_selector('input[type="submit"]')

        if submit:
            await submit.click()
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)

    async def _handle_account_switch(self):
        """Handle the account switcher page"""
        page = self._page

        # Try to click "Add account"
        add_btn = await page.query_selector('text="Add account"')
        if add_btn:
            await add_btn.click()
            await page.wait_for_load_state("domcontentloaded")

    async def _extract_seller_name(self, page: Page) -> str:
        """Extract seller name from the home page"""
        try:
            # Try common selectors
            selectors = [
                '[data-testid="account-name"]',
                '[data-testid="merchant-name"]',
                '.sc-account-switcher-name',
                'h1',
            ]

            for selector in selectors:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if text and len(text) < 100:
                        return text.strip()
        except Exception:
            pass

        return self.email

    async def submit_otp(self, otp: str) -> dict:
        """
        Resume login by providing OTP code.
        Re-opens browser with saved profile and continues from OTP page.
        """
        self._otp = otp
        return await self.login(otp=otp)


# ============================================================
# Session Verification
# ============================================================

async def verify_browser_session(cookies: List[Dict[str, Any]], country_code: str = "us") -> bool:
    """
    Verify that a set of cookies still provides valid access to Seller Central.
    Uses a lightweight HTTP request (no browser needed).
    """
    try:
        import niquests

        base_url = SELLER_CENTRAL_BASE.get(country_code, SELLER_CENTRAL_BASE["us"])

        session = niquests.AsyncSession()
        for cookie in cookies:
            session.cookies.set(
                cookie.get("name", ""),
                cookie.get("value", ""),
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )

        resp = await session.get(f"{base_url}/home", timeout=30, allow_redirects=True)

        # If redirected to sign-in page, session is invalid
        is_valid = "/ap/signin" not in str(resp.url)

        await session.close()
        return is_valid

    except Exception as e:
        logger.warning(f"Session verification failed: {e}")
        return False
