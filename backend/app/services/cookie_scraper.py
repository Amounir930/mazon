"""
Cookie-based Sync Worker (Playwright + DOM Extraction) - PRODUCTION READY

Uses Playwright to:
1. Open authenticated pages using stored cookies (including HttpOnly)
2. Validate session before each sync
3. Extract data from rendered DOM via JavaScript
4. Retry on failures with exponential backoff
5. Save raw HTML on failure for debugging

Features:
- Retry logic with tenacity for rate limits
- Session validation before each sync
- Random delays (3-7s) to avoid CAPTCHA/WAF detection
- Raw response saving on failure for debugging
- Flexible selectors for Amazon's dynamic DOM
"""
import json
import os
import random
import asyncio
import tempfile
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data

# Amazon Seller Central URLs
SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
    "uk": "https://sellercentral.amazon.co.uk",
    "us": "https://sellercentral.amazon.com",
}

# Debug directory for failed responses
DEBUG_DIR = Path(tempfile.gettempdir()) / "crazy_lister" / "sync_debug"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


class CookieScraper:
    """
    Production-ready sync engine using Playwright for authenticated data extraction.
    
    Features:
    - Retry with exponential backoff
    - Session validation
    - CAPTCHA avoidance via random delays
    - Debug mode with raw HTML saving
    """

    def __init__(self, debug: bool = False):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.debug = debug
        self._session_valid = False
    
    async def _init_browser(self):
        """Initialize Playwright browser with anti-detection flags"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-gpu",
                ]
            )
        except Exception as e:
            logger.error(f"Failed to init Playwright: {e}")
            raise RuntimeError(f"Playwright initialization failed: {e}")

    async def _setup_context(self, cookies: List[Dict], country_code: str):
        """Create browser context with proper cookie injection"""
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ar-EG",
            timezone_id="Africa/Cairo",
        )

        # Fix cookie domains - map .amazon.com to country-specific domain
        domain_map = {
            "eg": ".amazon.eg",
            "sa": ".amazon.sa",
            "ae": ".amazon.ae",
            "uk": ".amazon.co.uk",
            "us": ".amazon.com",
        }
        target_domain = domain_map.get(country_code, ".amazon.eg")

        injected_count = 0
        for cookie in cookies:
            try:
                # Override domain from .amazon.com to country-specific domain
                cookie_domain = cookie.get("domain", ".amazon.com")
                
                # If cookie is on .amazon.com but we need .amazon.eg, rewrite it
                if cookie_domain == ".amazon.com" and country_code != "us":
                    cookie_domain = target_domain
                
                if not cookie_domain.startswith("."):
                    cookie_domain = f".{cookie_domain}"
                
                await self.context.add_cookies([{
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie_domain,
                    "path": cookie.get("path", "/"),
                    "httpOnly": cookie.get("httpOnly", False),
                    "secure": cookie.get("secure", True),
                    "sameSite": cookie.get("sameSite", "Lax"),
                }])
                injected_count += 1
            except Exception as e:
                logger.debug(f"Cookie injection error {cookie.get('name')}: {e}")
        
        logger.info(f"Injected {injected_count}/{len(cookies)} cookies (domain: {target_domain})")
        self.page = await self.context.new_page()
        
        # Hide automation detection
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ar-EG', 'ar', 'en-US', 'en']});
        """)

    async def _get_session(self, email: str):
        """Get cookies and country from database"""
        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.email == email,
                AuthSession.is_active == True,
                AuthSession.is_valid == True,
            ).first()

            if not session:
                logger.warning(f"No active session for {email}")
                return None, None

            cookies = json.loads(decrypt_data(session.cookies_json))
            country = session.country_code or "eg"
            logger.info(f"Retrieved session for {email} ({country.upper()}, {len(cookies)} cookies)")
            return cookies, country
        except Exception as e:
            logger.error(f"Session retrieval failed: {e}")
            return None, None
        finally:
            db.close()

    async def _validate_session(self, base_url: str) -> bool:
        """
        Validate session by checking if we can access the home page.
        Returns False if redirected to login.
        """
        try:
            await self.page.goto(f"{base_url}/home", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            
            url = self.page.url
            if "/ap/signin" in url or "/gp/signin" in url:
                logger.warning("Session invalid - redirected to login page")
                return False
            
            # Also check for login form in the page
            has_login_form = await self.page.evaluate("""
                () => !!document.querySelector('#ap_email, form[action*="signin"]')
            """)
            
            if has_login_form:
                logger.warning("Session invalid - login form detected")
                return False
            
            logger.info("Session validation passed")
            self._session_valid = True
            return True
            
        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            return False

    async def _random_delay(self):
        """Add random delay to avoid CAPTCHA detection (3-7 seconds)"""
        delay = random.uniform(3, 7)
        logger.debug(f"Waiting {delay:.1f}s to avoid detection")
        await asyncio.sleep(delay)

    async def _save_debug_html(self, html: str, page_name: str):
        """Save raw HTML for debugging"""
        if not self.debug:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{page_name}_{timestamp}.html"
        filepath = DEBUG_DIR / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"Debug HTML saved: {filepath}")
        except Exception as e:
            logger.debug(f"Failed to save debug HTML: {e}")

    async def _check_for_captcha(self) -> bool:
        """Check if CAPTCHA is blocking the page"""
        try:
            has_captcha = await self.page.evaluate("""
                () => {
                    const captchaElements = [
                        '#captcha',
                        '#captchacharacters',
                        'form[action*="validateCaptcha"]',
                        '.captcha-container',
                    ];
                    return captchaElements.some(sel => !!document.querySelector(sel));
                }
            """)
            return has_captcha
        except:
            return False

    async def close(self):
        """Cleanup resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")

    # ========================================================
    # Public API - With retry logic
    # ========================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((TimeoutError, Exception)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=False,
    )
    async def sync_products(self, email: str) -> Dict[str, Any]:
        """
        Sync products from Amazon Seller Central.
        
        Flow:
        1. Get session from database
        2. Validate session
        3. Navigate to inventory page
        4. Extract products via JavaScript
        5. Return structured data
        """
        try:
            # Get session
            cookies, country = await self._get_session(email)
            if not cookies:
                return {
                    "success": False,
                    "error": "No active session - please login again",
                    "products": [],
                    "total": 0,
                }

            # Init browser
            await self._init_browser()
            await self._setup_context(cookies, country)

            base = SELLER_CENTRAL_BASE.get(country, SELLER_CENTRAL_BASE["eg"])

            # Validate session
            if not await self._validate_session(base):
                await self.close()
                return {
                    "success": False,
                    "error": "Session expired - please login again",
                    "products": [],
                    "total": 0,
                }

            # Random delay to avoid detection
            await self._random_delay()

            # Navigate to inventory page
            logger.info(f"Navigating to {base}/inventory")
            await self.page.goto(
                f"{base}/inventory",
                wait_until="networkidle",
                timeout=30000
            )
            
            # Wait for content to render
            await asyncio.sleep(3)

            # Check for CAPTCHA
            if await self._check_for_captcha():
                logger.warning("CAPTCHA detected - waiting and retrying")
                await asyncio.sleep(10)
                raise Exception("CAPTCHA detected")

            # Save debug HTML
            if self.debug:
                html = await self.page.content()
                await self._save_debug_html(html, "products")

            # Extract products via JS
            products = await self.page.evaluate(self._PRODUCTS_JS)

            await self.close()

            logger.info(f"Successfully extracted {len(products or [])} products")
            return {
                "success": True,
                "products": products or [],
                "total": len(products or []),
            }

        except Exception as e:
            logger.error(f"Products sync failed: {e}", exc_info=True)
            await self.close()
            return {
                "success": False,
                "error": str(e),
                "products": [],
                "total": 0,
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((TimeoutError, Exception)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=False,
    )
    async def sync_orders(self, email: str, days: int = 30) -> Dict[str, Any]:
        """
        Sync orders from Amazon Seller Central.
        
        Args:
            email: Amazon account email
            days: Number of days to look back (default 30)
        """
        try:
            cookies, country = await self._get_session(email)
            if not cookies:
                return {
                    "success": False,
                    "error": "No active session - please login again",
                    "orders": [],
                    "total": 0,
                }

            await self._init_browser()
            await self._setup_context(cookies, country)

            base = SELLER_CENTRAL_BASE.get(country, SELLER_CENTRAL_BASE["eg"])

            if not await self._validate_session(base):
                await self.close()
                return {
                    "success": False,
                    "error": "Session expired - please login again",
                    "orders": [],
                    "total": 0,
                }

            await self._random_delay()

            # Build orders URL with date filter
            from datetime import timedelta
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Try orders page
            logger.info(f"Navigating to {base}/orders")
            await self.page.goto(
                f"{base}/orders",
                wait_until="networkidle",
                timeout=30000
            )
            await asyncio.sleep(3)

            if await self._check_for_captcha():
                logger.warning("CAPTCHA detected - waiting and retrying")
                await asyncio.sleep(10)
                raise Exception("CAPTCHA detected")

            if self.debug:
                html = await self.page.content()
                await self._save_debug_html(html, "orders")

            orders = await self.page.evaluate(self._ORDERS_JS)

            # Normalize order data
            normalized = []
            for o in (orders or []):
                normalized.append({
                    "amazon_order_id": o.get("order_id", ""),
                    "created_at": o.get("date", ""),
                    "status": o.get("status", "Unknown"),
                    "total": float(o.get("total", 0)),
                    "buyer_name": o.get("buyer", ""),
                    "items": [],
                })

            await self.close()

            logger.info(f"Successfully extracted {len(normalized)} orders")
            return {
                "success": True,
                "orders": normalized,
                "total": len(normalized),
            }

        except Exception as e:
            logger.error(f"Orders sync failed: {e}", exc_info=True)
            await self.close()
            return {
                "success": False,
                "error": str(e),
                "orders": [],
                "total": 0,
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((TimeoutError, Exception)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=False,
    )
    async def sync_inventory(self, email: str) -> Dict[str, Any]:
        """Sync inventory from Amazon Seller Central."""
        try:
            cookies, country = await self._get_session(email)
            if not cookies:
                return {
                    "success": False,
                    "error": "No active session - please login again",
                    "inventory": [],
                    "total": 0,
                }

            await self._init_browser()
            await self._setup_context(cookies, country)

            base = SELLER_CENTRAL_BASE.get(country, SELLER_CENTRAL_BASE["eg"])

            if not await self._validate_session(base):
                await self.close()
                return {
                    "success": False,
                    "error": "Session expired - please login again",
                    "inventory": [],
                    "total": 0,
                }

            await self._random_delay()

            logger.info(f"Navigating to {base}/manage/inventory")
            await self.page.goto(
                f"{base}/manage/inventory",
                wait_until="networkidle",
                timeout=30000
            )
            await asyncio.sleep(3)

            if await self._check_for_captcha():
                logger.warning("CAPTCHA detected - waiting and retrying")
                await asyncio.sleep(10)
                raise Exception("CAPTCHA detected")

            if self.debug:
                html = await self.page.content()
                await self._save_debug_html(html, "inventory")

            inventory = await self.page.evaluate(self._INVENTORY_JS)

            # Normalize inventory data
            normalized = []
            for item in (inventory or []):
                f = item.get("fulfillment", "MFN").upper()
                normalized.append({
                    "sku": item.get("sku", ""),
                    "asin": item.get("asin", ""),
                    "name": item.get("name", ""),
                    "available": int(item.get("available", 0)),
                    "reserved": int(item.get("reserved", 0)),
                    "inbound": int(item.get("inbound", 0)),
                    "fulfillment": f,
                    "fba": f in ["FBA", "AFN"],
                    "fbm": f in ["MFN", "FBM"],
                })

            await self.close()

            logger.info(f"Successfully extracted {len(normalized)} inventory items")
            return {
                "success": True,
                "inventory": normalized,
                "total": len(normalized),
            }

        except Exception as e:
            logger.error(f"Inventory sync failed: {e}", exc_info=True)
            await self.close()
            return {
                "success": False,
                "error": str(e),
                "inventory": [],
                "total": 0,
            }

    # ========================================================
    # JavaScript Extraction Scripts (Flexible Selectors)
    # ========================================================

    _PRODUCTS_JS = """
    () => {
        const products = [];
        
        // Try multiple selector strategies
        const selectors = [
            'table tbody tr',
            '[role="row"]',
            '.inventory-row',
            '.data-grid-row',
            '[data-testid*="product"]',
            '.manage-inventory-table tbody tr',
        ];
        
        let rows = [];
        for (const sel of selectors) {
            rows = document.querySelectorAll(sel);
            if (rows.length > 0) break;
        }
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th, [role="gridcell"]');
            if (cells.length < 3) return;
            
            const p = {};
            
            cells.forEach(cell => {
                const text = cell.textContent.trim();
                if (!text) return;
                
                // SKU: ABC-12345 or similar
                if (!p.sku && /^[A-Z0-9]+-[A-Z0-9\\d]+/i.test(text)) {
                    p.sku = text;
                }
                // ASIN: B0XXXXXXXX
                else if (!p.asin && /^B[0-9A-Z]{9}$/.test(text)) {
                    p.asin = text;
                }
                // Price: EGP 150.00 or 150.00
                else if (!p.price && /[\\d,]+\\.?\\d*/.test(text)) {
                    const num = text.replace(/[^\\d.]/g, '');
                    if (num && !isNaN(parseFloat(num))) {
                        p.price = parseFloat(num);
                    }
                }
                // Quantity: pure number
                else if (!p.quantity && /^\\d+$/.test(text) && parseInt(text) < 100000) {
                    p.quantity = parseInt(text);
                }
                // Status
                else if (!p.status && /^(Active|Inactive|Draft|Published|Closed)$/i.test(text)) {
                    p.status = text;
                }
                // Name (fallback: long text)
                else if (!p.name && text.length > 10 && text.length < 300) {
                    p.name = text;
                }
            });
            
            // Only add if we got something meaningful
            if (p.sku || (p.name && p.asin)) {
                products.push(p);
            }
        });
        
        return products;
    }
    """

    _ORDERS_JS = """
    () => {
        const orders = [];
        
        // Try multiple selector strategies
        const selectors = [
            'table tbody tr',
            '[role="row"]',
            '.order-row',
            '.data-grid-row',
            '[data-testid*="order"]',
            '.manage-orders-table tbody tr',
        ];
        
        let rows = [];
        for (const sel of selectors) {
            rows = document.querySelectorAll(sel);
            if (rows.length > 0) break;
        }
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th, [role="gridcell"]');
            if (cells.length < 3) return;
            
            const o = {};
            
            cells.forEach(cell => {
                const text = cell.textContent.trim();
                if (!text) return;
                
                // Order ID: 123-4567890-1234567
                if (!o.order_id && /^\\d{3}-\\d{7}-\\d{7}$/.test(text)) {
                    o.order_id = text;
                }
                // Date: MM/DD/YYYY or DD/MM/YYYY
                else if (!o.date && /\\d{1,2}\\/\\d{1,2}\\/\\d{4}/.test(text)) {
                    o.date = text;
                }
                // Total: price amount
                else if (!o.total && /[\\d,]+\\.?\\d*/.test(text)) {
                    const num = text.replace(/[^\\d.]/g, '');
                    if (num && !isNaN(parseFloat(num)) && parseFloat(num) > 0) {
                        o.total = parseFloat(num);
                    }
                }
                // Status
                else if (!o.status && /^(Pending|Unshipped|Shipped|Delivered|Canceled|Cancelled|Processing)$/i.test(text)) {
                    o.status = text;
                }
                // Buyer name
                else if (!o.buyer && text.length > 3 && text.length < 60 && /^[A-Za-z\\s\\.'-]+$/.test(text)) {
                    o.buyer = text;
                }
            });
            
            if (o.order_id) {
                orders.push(o);
            }
        });
        
        return orders;
    }
    """

    _INVENTORY_JS = """
    () => {
        const inventory = [];
        
        // Try multiple selector strategies
        const selectors = [
            'table tbody tr',
            '[role="row"]',
            '.inventory-row',
            '.data-grid-row',
            '[data-testid*="inventory"]',
            '.manage-inventory-table tbody tr',
        ];
        
        let rows = [];
        for (const sel of selectors) {
            rows = document.querySelectorAll(sel);
            if (rows.length > 0) break;
        }
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th, [role="gridcell"]');
            if (cells.length < 3) return;
            
            const item = {};
            let numCount = 0;
            
            cells.forEach(cell => {
                const text = cell.textContent.trim();
                if (!text) return;
                
                // SKU
                if (!item.sku && /^[A-Z0-9]+-[A-Z0-9\\d]+/i.test(text)) {
                    item.sku = text;
                }
                // ASIN
                else if (!item.asin && /^B[0-9A-Z]{9}$/.test(text)) {
                    item.asin = text;
                }
                // Numbers (quantities)
                else if (/^\\d+$/.test(text) && parseInt(text) < 100000) {
                    numCount++;
                    if (numCount === 1) item.available = parseInt(text);
                    else if (numCount === 2) item.reserved = parseInt(text);
                    else if (numCount === 3) item.inbound = parseInt(text);
                }
                // Fulfillment type
                else if (/^(FBA|AFN|MFN|FBM)$/i.test(text)) {
                    item.fulfillment = text.toUpperCase();
                }
                // Name
                else if (!item.name && text.length > 10 && text.length < 300) {
                    item.name = text;
                }
            });
            
            if (item.sku) {
                // Set defaults
                if (!item.available) item.available = 0;
                if (!item.reserved) item.reserved = 0;
                if (!item.inbound) item.inbound = 0;
                if (!item.fulfillment) item.fulfillment = 'MFN';
                
                inventory.push(item);
            }
        });
        
        return inventory;
    }
    """
