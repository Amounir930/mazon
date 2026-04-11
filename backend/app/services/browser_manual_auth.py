"""
Browser Manual Authentication
Opens a browser for the user to manually enter credentials.
Monitors until login succeeds or timeout.
"""
import asyncio
import os
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page, BrowserContext
from loguru import logger


class BrowserManualAuth:
    """
    يفتح متصفح ➜ المستخدم يدخل بإيده ➜ يرجع بالكوكيز
    Amazon Seller Central Egypt فقط
    """

    BASE_URL = "https://sellercentral.amazon.eg"
    PROFILE_BASE = os.path.join(os.path.expanduser("~"), "CrazyListerProfiles")

    def __init__(self, timeout_seconds: int = 180):
        self.timeout_seconds = timeout_seconds
        self._browser = None
        self._context = None
        self._page = None

    async def login(self) -> dict:
        """
        فتح المتصفح والانتظار حتى يسجل المستخدم الدخول.
        """
        profile_dir = os.path.join(self.PROFILE_BASE, "manual_eg")
        os.makedirs(profile_dir, exist_ok=True)

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        self._browser = browser
        self._context = context
        self._page = page

        try:
            url = f"{self.BASE_URL}/home"
            logger.info(f"Opening browser for manual login: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Monitor for successful login
            result = await self._wait_for_login()

            if result.get("success"):
                cookies = await context.cookies()
                seller_name = await self._get_seller_name(page)

                return {
                    "success": True,
                    "cookies": cookies,
                    "seller_name": seller_name,
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Browser manual auth failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await browser.close()
            await playwright.stop()

    async def _wait_for_login(self) -> dict:
        """
        مراقبة URL حتى يصل /home أو timeout.
        """
        max_checks = self.timeout_seconds // 2  # كل ثانيتين
        iteration = 0

        while iteration < max_checks:
            await asyncio.sleep(2)
            iteration += 1

            try:
                current_url = self._page.url
            except Exception:
                return {"success": False, "error": "المتصفح أُغلق"}

            logger.debug(f"Manual login check [{iteration}/{max_checks}]: {current_url}")

            # نجاح - وصل الصفحة الرئيسية
            if "/home" in current_url:
                logger.info("Manual login successful - reached /home")
                return {"success": True}

            # لو راح لصفحة تسجيل الدخول - المستخدم لسه ما دخلش
            if "/ap/signin" in current_url or "/gp/signin" in current_url:
                continue  # انتظر أكثر

            # صفحة غير معروفة - انتظر
            if iteration % 10 == 0:
                logger.info(f"Still waiting for login... ({iteration * 2}s elapsed)")

        return {
            "success": False,
            "error": f"timeout - ما دخلش خلال {self.timeout_seconds} ثانية",
        }

    async def _get_seller_name(self, page: Page) -> str:
        """استخراج اسم البائع من الصفحة"""
        try:
            name_el = await page.query_selector('[data-testid="account-name"]')
            if name_el:
                return (await name_el.inner_text()).strip()
        except Exception:
            pass

        return "Manual User (EG)"
