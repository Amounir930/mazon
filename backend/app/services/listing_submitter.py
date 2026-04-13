"""
Amazon Listing Submitter (Playwright-based)

Uses Playwright to:
1. Open the listing creation page in Amazon Seller Central
2. Fill in all required form fields
3. Submit the listing via Amazon's own UI
4. Capture the response (success/error)

This is the ONLY reliable way to create listings — bypasses the 403 protection
on the ABIS AJAX API by using Amazon's own frontend JavaScript.

Pattern: Clone & Inject via browser automation (same as ALister)
"""
import json
import random
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data

# Amazon Seller Central URLs
SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}


class ListingSubmitter:
    """
    Submit listings to Amazon via Playwright browser automation.
    Uses the same flow as a human filling the form — which Amazon accepts.
    """

    def __init__(self, country_code: str = "eg", debug: bool = False):
        self.country_code = country_code.lower()
        self.base_url = SELLER_CENTRAL_BASE.get(self.country_code, SELLER_CENTRAL_BASE["eg"])
        self.debug = debug
        self.browser = None
        self.context = None
        self.page = None
        self.api_responses = []

    async def submit_listing(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a listing to Amazon using Playwright.

        Args:
            product_data: Dict with sku, name, price, quantity, brand, ean, etc.

        Returns:
            {
                "success": bool,
                "status": str,
                "asin": str,
                "listing_id": str,
                "error": str or None,
            }
        """
        sku = product_data.get("sku", "UNKNOWN")
        logger.info(f"📦 Starting Playwright listing submission for SKU: {sku}")

        try:
            from playwright.async_api import async_playwright

            # Launch browser
            logger.info("Launching Playwright browser...")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            # Create context with realistic settings
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="Africa/Cairo",
            )

            # Load cookies from DB
            cookies = await self._load_cookies()
            if not cookies:
                return {
                    "success": False,
                    "error": "No active session — please login first",
                    "session_expired": True,
                }

            await context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} cookies")

            # Intercept API responses
            self.api_responses = []

            async def handle_response(response):
                url = response.url
                if "/abis/ajax/create-listing" in url:
                    try:
                        body = await response.text()
                        status = response.status
                        logger.info(f"📡 Intercepted API: {status} {url}")
                        self.api_responses.append({
                            "url": url,
                            "status": status,
                            "body": body,
                        })
                    except:
                        pass

            page = await context.new_page()
            page.on("response", handle_response)

            # Step 1: Navigate to listing creation page
            create_url = f"{self.base_url}/abis/listing/create/product_identity?productType=HOME_ORGANIZERS_AND_STORAGE"
            logger.info(f"Navigating to: {create_url}")
            
            response = await page.goto(create_url, wait_until="domcontentloaded", timeout=30000)
            
            # Check if redirected to login
            if "/ap/signin" in page.url or "/gp/signin" in page.url:
                logger.error("Redirected to login — session expired")
                await browser.close()
                return {
                    "success": False,
                    "error": "Session expired — redirected to login",
                    "session_expired": True,
                }

            logger.info(f"Page loaded: {page.url}")
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Random delay to appear human
            delay = random.uniform(2, 4)
            logger.info(f"Waiting {delay:.1f}s (human simulation)...")
            await page.wait_for_timeout(delay * 1000)

            # Step 2: Fill in the form using JavaScript injection
            logger.info("Filling form fields...")
            
            fill_result = await page.evaluate(self._get_fill_script(product_data))
            logger.info(f"Fill result: {fill_result}")

            if not fill_result.get("success"):
                logger.error(f"Form filling failed: {fill_result.get('error')}")
                # Take screenshot for debugging
                if self.debug:
                    await page.screenshot(path=f"listing_error_{sku}.png")
                await browser.close()
                return {
                    "success": False,
                    "error": f"Failed to fill form: {fill_result.get('error')}",
                }

            # Random delay before submission
            delay = random.uniform(1, 3)
            logger.info(f"Waiting {delay:.1f}s before submit...")
            await page.wait_for_timeout(delay * 1000)

            # Step 3: Click submit/save button
            logger.info("Submitting listing...")
            
            submit_result = await page.evaluate(self._get_submit_script())
            logger.info(f"Submit result: {submit_result}")

            # Wait for API response
            logger.info("Waiting for API response...")
            await page.wait_for_timeout(10000)

            # Check intercepted responses
            result = self._process_api_responses()
            
            if result:
                logger.info(f"API result: {result}")
                await browser.close()
                return result

            # Fallback: check page for success/error indicators
            page_text = await page.inner_text("body")
            
            if "successfully" in page_text.lower() or "created" in page_text.lower():
                logger.info("✅ Listing created successfully (page indicator)")
                await browser.close()
                return {
                    "success": True,
                    "status": "SUCCESS",
                    "asin": "",
                    "listing_id": sku,
                }
            
            if "error" in page_text.lower() or "failed" in page_text.lower():
                # Extract error message
                error_start = max(0, page_text.lower().find("error") - 50)
                error_msg = page_text[error_start:error_start + 300]
                logger.warning(f"Error detected on page: {error_msg}")
                await browser.close()
                return {
                    "success": False,
                    "error": f"Amazon returned error: {error_msg}",
                }

            # Screenshot for debugging
            if self.debug:
                await page.screenshot(path=f"listing_result_{sku}.png")

            await browser.close()
            return {
                "success": False,
                "error": "Could not determine result — check screenshot",
                "page_url": str(page.url),
            }

        except Exception as e:
            logger.error(f"Listing submission failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    async def _load_cookies(self) -> List[Dict[str, Any]]:
        """Load cookies from database and format for Playwright"""
        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.is_active == True,
                AuthSession.is_valid == True,
            ).first()

            if not session or not session.cookies_json:
                return []

            raw_cookies = json.loads(decrypt_data(session.cookies_json))
            
            # Convert to Playwright format
            pw_cookies = []
            for c in raw_cookies:
                pw_c = {
                    "name": c.get("name", ""),
                    "value": c.get("value", ""),
                    "domain": c.get("domain", ".amazon.eg"),
                    "path": c.get("path", "/"),
                    "httpOnly": c.get("httpOnly", False),
                    "secure": c.get("secure", False),
                }
                if c.get("expires"):
                    pw_c["expires"] = c["expires"]
                if c.get("sameSite"):
                    ss = c["sameSite"].lower()
                    if ss in ("lax", "strict", "none"):
                        pw_c["sameSite"] = ss.upper()
                pw_cookies.append(pw_c)

            return pw_cookies
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return []
        finally:
            db.close()

    def _get_fill_script(self, product_data: Dict[str, Any]) -> str:
        """Generate JS to fill all form fields"""
        data = json.dumps({
            "sku": product_data.get("sku", ""),
            "name": product_data.get("name", ""),
            "description": product_data.get("description", ""),
            "price": str(product_data.get("price", 0)),
            "quantity": str(product_data.get("quantity", 0)),
            "brand": product_data.get("brand", "Generic"),
            "ean": product_data.get("ean", ""),
            "model_number": product_data.get("model_number", ""),
            "country_of_origin": product_data.get("country_of_origin", ""),
            "bullet_points": product_data.get("bullet_points", []),
        })
        
        return f"""
        () => {{
            try {{
                const data = {data};
                const results = {{ filled: 0, errors: [] }};

                // Helper: find and set input value
                function fillField(selectors, value) {{
                    if (!value) return false;
                    for (const sel of selectors) {{
                        const el = document.querySelector(sel) || document.querySelector(`[name="${{sel}}"]`);
                        if (el && el.tagName === 'INPUT') {{
                            const input = el;
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            nativeInputValueSetter.call(input, value);
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        if (el && el.tagName === 'TEXTAREA') {{
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                            nativeInputValueSetter.call(el, value);
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                    return false;
                }}

                // Try to fill common fields
                if (fillField(['input[name="sku"]', 'input[data-testid="sku"]', '#sku'], data.sku)) results.filled++;
                if (fillField(['input[name="item_name"]', 'input[data-testid="item_name"]', '#item_name'], data.name)) results.filled++;
                if (fillField(['textarea[name="product_description"]', 'textarea[data-testid="product_description"]'], data.description)) results.filled++;
                if (fillField(['input[name="price"]', 'input[data-testid="price"]', 'input[name="your-price"]'], data.price)) results.filled++;
                if (fillField(['input[name="quantity"]', 'input[data-testid="quantity"]', 'input[name="qty"]'], data.quantity)) results.filled++;
                if (fillField(['input[name="brand"]', 'input[data-testid="brand"]'], data.brand)) results.filled++;
                if (fillField(['input[name="ean"]', 'input[data-testid="ean"]', 'input[name="upc"]'], data.ean)) results.filled++;

                // Check if we're on the right page (form should be visible)
                const hasForm = document.querySelector('form') || document.querySelector('[data-testid="listing-form"]') || document.querySelector('.listing-form');
                if (!hasForm) {{
                    results.errors.push('No form found on page');
                }}

                results.success = results.filled > 0;
                return results;
            }} catch(e) {{
                return {{ success: false, error: e.message }};
            }}
        }}
        """

    def _get_submit_script(self) -> str:
        """Generate JS to click the submit/save button"""
        return """
        () => {
            try {
                // Try common submit button selectors
                const selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button[data-testid="submit"]',
                    'button[data-testid="save"]',
                    'button:contains("Save")',
                    'button:contains("Submit")',
                    'button:contains("Save and finish")',
                    'button:contains("Save and close")',
                    '[data-action="save"]',
                    '[data-action="submit"]',
                ];
                
                for (const sel of selectors) {
                    const btn = document.querySelector(sel);
                    if (btn && btn.offsetParent !== null) { // visible
                        btn.click();
                        return { clicked: true, selector: sel };
                    }
                }
                
                // Fallback: find any button with "save" or "submit" text
                const buttons = document.querySelectorAll('button, [role="button"]');
                for (const btn of buttons) {
                    const text = (btn.textContent || '').toLowerCase();
                    if ((text.includes('save') || text.includes('submit') || text.includes('finish')) && btn.offsetParent !== null) {
                        btn.click();
                        return { clicked: true, text: text.trim() };
                    }
                }
                
                return { clicked: false, error: 'No submit button found' };
            } catch(e) {
                return { clicked: false, error: e.message };
            }
        }
        """

    def _process_api_responses(self) -> Optional[Dict[str, Any]]:
        """Process intercepted API responses"""
        for resp in self.api_responses:
            if resp["status"] == 200:
                try:
                    data = json.loads(resp["body"])
                    if data.get("status") == "SUCCESS":
                        return {
                            "success": True,
                            "status": "SUCCESS",
                            "asin": data.get("asin", ""),
                            "listing_id": data.get("listingId", ""),
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("message", data.get("error", "Unknown error")),
                            "response": data,
                        }
                except:
                    pass
            elif resp["status"] >= 400:
                return {
                    "success": False,
                    "error": f"API returned {resp['status']}: {resp['body'][:300]}",
                }
        return None

    async def close(self):
        """Clean up browser"""
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
