"""
Amazon Listing Submitter — ALister Protocol v2 (Simplified Native POST)

Uses Playwright to:
1. Open the listing creation page (product_identity) in Amazon Seller Central
2. Wait for page to fully load (establishes session)
3. Build payload from known Amazon template structure
4. POST the payload from INSIDE the browser via page.evaluate()

WHY THIS WORKS:
- Request comes from real browser (no WAF detection)
- Uses live session cookies + CSRF from the page
- No DOM selectors needed (no brittle code)
- No unreliable interception needed

This replaces the old approach that used page.route() interception which
was causing NotImplementedError.
"""
import json
import asyncio
import sys
import re
from typing import Dict, Any, Optional, List
from loguru import logger

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}


class ListingSubmitter:
    """
    Submit listings to Amazon via Native POST from inside Playwright browser.

    Flow:
    1. Open product_identity page with Playwright
    2. Wait for page load + extract CSRF
    3. Build payload from known Amazon template structure
    4. POST via page.evaluate() — fetch() from INSIDE browser (bypasses WAF)
    """

    def __init__(self, country_code: str = "eg", debug: bool = False):
        self.country_code = country_code.lower()
        self.base_url = SELLER_CENTRAL_BASE.get(self.country_code, SELLER_CENTRAL_BASE["eg"])
        self.debug = debug
        self.browser = None
        self.context = None
        self.page = None
        self._csrf_token: Optional[str] = None

    async def submit_listing(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a listing to Amazon using ALister Protocol v2.

        On Windows, runs sync Playwright in a thread to avoid ProactorEventLoop issues.
        On Linux/Mac, uses async Playwright directly.
        """
        sku = product_data.get("sku", "UNKNOWN")
        logger.info(f"[ALister] Starting listing submission for SKU: {sku}")

        # FIX: Windows ProactorEventLoop doesn't support subprocess_exec
        # Run sync Playwright in a thread on Windows
        if sys.platform == "win32":
            logger.info("[ALister] Windows detected — using sync Playwright in thread")
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,  # default ThreadPool
                self._submit_listing_sync,
                product_data,
            )
        else:
            return await self._submit_listing_async(product_data)

    def _submit_listing_sync(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync version of submit_listing for Windows thread execution"""
        import sys as _sys
        try:
            from playwright.sync_api import sync_playwright

            sku = product_data.get("sku", "UNKNOWN")
            logger.info(f"[ALister-Sync] Starting listing submission for SKU: {sku}")

            playwright = sync_playwright().start()
            try:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )

                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="Africa/Cairo",
                )

                # Load cookies
                logger.info("[ALister-Sync] Loading cookies from DB...")
                cookies = self._load_cookies_sync()
                if not cookies:
                    logger.error("[ALister-Sync] No active session")
                    return {
                        "success": False,
                        "error": "No active session — please login first",
                        "session_expired": True,
                    }

                context.add_cookies(cookies)
                logger.info(f"[ALister-Sync] Loaded {len(cookies)} cookies")

                page = context.new_page()

                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = {runtime: {}};
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ar']});
                """)

                # Navigate
                create_url = f"{self.base_url}/abis/listing/create/product_identity?productType=HOME_ORGANIZERS_AND_STORAGE"
                logger.info(f"[ALister-Sync] Navigating to {create_url}")

                page.goto(create_url, wait_until="domcontentloaded", timeout=30000)

                if "/ap/signin" in page.url or "/gp/signin" in page.url:
                    logger.error("[ALister-Sync] Redirected to login — session expired")
                    browser.close()
                    playwright.stop()
                    return {
                        "success": False,
                        "error": "Session expired — redirected to login",
                        "session_expired": True,
                    }

                logger.info(f"[ALister-Sync] Page loaded: {page.url}")

                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                    logger.info("[ALister-Sync] Network idle reached")
                except Exception as e:
                    logger.warning(f"[ALister-Sync] Network idle timeout (non-fatal): {e}")

                import time
                time.sleep(3)

                # Extract CSRF
                csrf_token = self._extract_csrf_sync(page)
                if not csrf_token:
                    logger.error("[ALister-Sync] Failed to extract CSRF token")
                    browser.close()
                    playwright.stop()
                    return {
                        "success": False,
                        "error": "Failed to extract CSRF token from page",
                    }

                logger.info(f"[ALister-Sync] CSRF token: {csrf_token[:20]}... ({len(csrf_token)} chars)")

                # Build payload
                payload = self._build_payload(product_data)
                payload_json = json.dumps(payload, ensure_ascii=False)
                logger.info(f"[ALister-Sync] Payload size: {len(payload_json)} chars")

                # POST
                result = self._native_post_sync(page, payload_json, csrf_token)

                browser.close()
                playwright.stop()
                return result

            except Exception as e:
                logger.error(f"[ALister-Sync] Submission failed: {e}", exc_info=True)
                try:
                    browser.close()
                    playwright.stop()
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": str(e),
                }

        except ImportError:
            logger.error("[ALister-Sync] playwright not installed. Run: playwright install chromium")
            return {
                "success": False,
                "error": "Playwright not installed. Run: playwright install chromium",
            }

    def _load_cookies_sync(self) -> List[Dict[str, Any]]:
        """Load cookies sync version"""
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

                raw_ss = c.get("sameSite", "")
                if raw_ss:
                    ss_lower = str(raw_ss).lower()
                    if ss_lower == "strict":
                        pw_c["sameSite"] = "Strict"
                    elif ss_lower == "none":
                        pw_c["sameSite"] = "None"
                    else:
                        pw_c["sameSite"] = "Lax"

                pw_cookies.append(pw_c)

            return pw_cookies
        except Exception as e:
            logger.error(f"[ALister-Sync] Failed to load cookies: {e}")
            return []
        finally:
            db.close()

    def _extract_csrf_sync(self, page) -> Optional[str]:
        """Extract CSRF sync version"""
        try:
            token = page.evaluate("""
                () => {
                    const windowToken = window['anti-csrftoken-a2z'] || window.a2zToken;
                    if (windowToken && windowToken.length > 20) return windowToken;
                    const metaToken = document.querySelector('[name="anti-csrftoken-a2z"]')?.content;
                    if (metaToken && metaToken.length > 20) return metaToken;
                    const inputToken = document.querySelector('input[name="anti-csrftoken-a2z"]')?.value;
                    if (inputToken && inputToken.length > 20) return inputToken;
                    return "";
                }
            """)

            if token and len(token) > 20:
                return token

            content = page.content()
            for pattern in [r'"anti-csrftoken-a2z"\s*:\s*"([^"]+)"', r'anti-csrftoken-a2z["\']\s*:\s*["\']([^"\']+)["\']']:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    t = match.group(1)
                    if len(t) > 20 and not t.startswith('mons_'):
                        return t

            return None
        except Exception as e:
            logger.error(f"[ALister-Sync] CSRF extraction failed: {e}")
            return None

    def _native_post_sync(self, page, payload_json: str, csrf: str) -> Dict[str, Any]:
        """Native POST sync version"""
        result = page.evaluate("""
            async (params) => {
                const { payload, csrf } = params;
                const formData = new URLSearchParams();
                formData.append('data', payload);
                formData.append('anti-csrftoken-a2z', csrf);

                try {
                    const res = await fetch('/abis/ajax/create-listing', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
                            'X-Requested-With': 'XMLHttpRequest',
                            'anti-csrftoken-a2z': csrf,
                            'x-csrf-token': csrf,
                        },
                        body: formData.toString(),
                    });

                    const text = await res.text();
                    let json;
                    try {
                        json = JSON.parse(text);
                    } catch (e) {
                        return {
                            success: false,
                            status: 'PARSE_ERROR',
                            error: 'Response not JSON: ' + text.substring(0, 300),
                            raw: text.substring(0, 500),
                        };
                    }

                    return {
                        success: json.status === 'SUCCESS',
                        status: json.status || 'ERROR',
                        asin: json.asin || '',
                        listing_id: json.listingId || '',
                        message: json.message || json.error || '',
                        raw: json,
                    };
                } catch (e) {
                    return {
                        success: false,
                        status: 'FETCH_ERROR',
                        error: e.message,
                    };
                }
            }
        """, {"payload": payload_json, "csrf": csrf})

        logger.info(f"[ALister-Sync] POST result: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")

        if result.get("success"):
            logger.info(f"[ALister-Sync] SUCCESS! ASIN={result.get('asin')}, Listing ID={result.get('listing_id')}")
            return {
                "success": True,
                "status": "SUCCESS",
                "asin": result.get("asin", ""),
                "listing_id": result.get("listing_id", ""),
            }
        else:
            error = result.get("error", result.get("message", "Unknown"))
            logger.error(f"[ALister-Sync] FAILED: {error}")
            return {
                "success": False,
                "status": result.get("status", "ERROR"),
                "error": error,
                "response": result.get("raw"),
            }

    async def _submit_listing_async(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of submit_listing for Linux/Mac"""
        sku = product_data.get("sku", "UNKNOWN")
        logger.info(f"[ALister] Starting listing submission for SKU: {sku}")

        try:
            from playwright.async_api import async_playwright

            # Step 1: Launch browser
            logger.info("[ALister] Step 1: Launching Playwright...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="Africa/Cairo",
            )

            # Step 2: Load cookies
            logger.info("[ALister] Step 2: Loading cookies from DB...")
            cookies = await self._load_cookies()
            if not cookies:
                logger.error("[ALister] No active session")
                return {
                    "success": False,
                    "error": "No active session — please login first",
                    "session_expired": True,
                }

            await self.context.add_cookies(cookies)
            logger.info(f"[ALister] Loaded {len(cookies)} cookies")

            # Step 3: Create page + anti-detection
            logger.info("[ALister] Step 3: Creating page...")
            self.page = await self.context.new_page()

            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ar']});
            """)

            # Step 4: Navigate to product_identity page
            create_url = f"{self.base_url}/abis/listing/create/product_identity?productType=HOME_ORGANIZERS_AND_STORAGE"
            logger.info(f"[ALister] Step 4: Navigating to {create_url}")

            response = await self.page.goto(create_url, wait_until="domcontentloaded", timeout=30000)

            # Check if redirected to login
            if "/ap/signin" in self.page.url or "/gp/signin" in self.page.url:
                logger.error("[ALister] Redirected to login — session expired")
                await self._cleanup()
                return {
                    "success": False,
                    "error": "Session expired — redirected to login",
                    "session_expired": True,
                }

            logger.info(f"[ALister] Page loaded: {self.page.url}")

            # Wait for network to settle
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                logger.info("[ALister] Network idle reached")
            except Exception as e:
                logger.warning(f"[ALister] Network idle timeout (non-fatal): {e}")

            # Wait a bit for Amazon's JS to initialize
            await asyncio.sleep(3)

            # Step 5: Extract CSRF token
            logger.info("[ALister] Step 5: Extracting CSRF token...")
            self._csrf_token = await self._extract_csrf_from_page()
            if not self._csrf_token:
                logger.error("[ALister] Failed to extract CSRF token")
                await self._cleanup()
                return {
                    "success": False,
                    "error": "Failed to extract CSRF token from page",
                }

            logger.info(f"[ALister] CSRF token: {self._csrf_token[:20]}... ({len(self._csrf_token)} chars)")

            # Step 6: Build payload
            logger.info("[ALister] Step 6: Building payload...")
            payload = self._build_payload(product_data)
            payload_json = json.dumps(payload, ensure_ascii=False)
            logger.info(f"[ALister] Payload size: {len(payload_json)} chars")

            # Step 7: POST from INSIDE browser
            logger.info("[ALister] Step 7: Executing native POST from inside browser...")
            result = await self._native_post(payload_json)

            await self._cleanup()
            return result

        except Exception as e:
            logger.error(f"[ALister] Listing submission failed: {e}", exc_info=True)
            await self._cleanup()
            return {
                "success": False,
                "error": str(e),
            }

    def _build_payload(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the listing payload matching Amazon's expected structure.

        This is based on the known template structure from Amazon's own template.
        """
        name = product_data.get("name", "Unknown Product")
        description = product_data.get("description", name)
        brand = (product_data.get("brand") or "Generic").strip() or "Generic"
        ean = product_data.get("ean", "")
        sku = product_data.get("sku", "")
        price = float(product_data.get("price", 0))
        quantity = int(product_data.get("quantity", 0))
        condition = product_data.get("condition", "New")
        fulfillment = product_data.get("fulfillment_channel", "MFN")
        country_origin = product_data.get("country_of_origin", "CN")
        model_name = product_data.get("model_number", sku)
        manufacturer = (product_data.get("manufacturer") or brand).strip() or brand
        bullet_points = product_data.get("bullet_points", [])
        product_type = product_data.get("product_type", "HOME_ORGANIZERS_AND_STORAGE")

        condition_map = {"New": "new_new", "Used": "used_used", "Refurbished": "refurbished_refurbished"}
        condition_value = condition_map.get(condition, "new_new")
        fulfillment_value = "MFN" if fulfillment == "MFN" else "AFN"

        # Build attributePropertiesImsV3 (nested structure)
        attr_ims = {
            "item_name": [{"language_tag": "en_US", "value": name}],
            "product_type": [{"value": product_type}],
            "recommended_browse_nodes": [{"value": "21863799031"}],
            "brand": [{"language_tag": "en_US", "value": brand}],
            "product_description": [{"language_tag": "en_US", "value": description}],
            "model_name": [{"language_tag": "en_US", "value": model_name}],
            "manufacturer": [{"language_tag": "en_US", "value": manufacturer}],
            "country_of_origin": [{"value": country_origin.upper() if len(country_origin) == 2 else "CN"}],
            "condition_type": [{"value": condition_value}],
            "offerFulfillment": fulfillment_value,
            "automated_pricing_rule_type": [{"value": "disabled"}],
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "unit_count": [{"type": {"language_tag": "en_US", "value": "العد"}, "value": 1.0}],
            "included_components": [{"language_tag": "en_US", "value": name}],
            "purchasable_offer": [{
                "our_price": [{"schedule": [{"value_with_tax": price}]}],
                "maximum_retail_price": [{"schedule": [{"value_with_tax": price}]}],
                "currency": "EGP",
            }],
            "fulfillment_availability": [{"quantity": quantity}],
        }

        if ean:
            attr_ims["externally_assigned_product_identifier"] = [{
                "type": "upc/ean/gtin",
                "value": str(ean),
            }]

        if bullet_points and isinstance(bullet_points, list) and len(bullet_points) > 0:
            attr_ims["bullet_point"] = [{"language_tag": "en_US", "value": str(bullet_points[0])}]
        else:
            attr_ims["bullet_point"] = [{"language_tag": "en_US", "value": name}]

        # Build attributeProperties (FLAT keys)
        attr_flat = {
            "item_name#1.language_tag": "en_US",
            "item_name#1.value": name,
            "product_type#1.value": product_type,
            "recommended_browse_nodes#1.value": "21863799031",
            "brand#1.language_tag": "en_US",
            "brand#1.value": brand,
            "product_description#1.language_tag": "en_US",
            "product_description#1.value": description,
            "model_name#1.language_tag": "en_US",
            "model_name#1.value": model_name,
            "manufacturer#1.language_tag": "en_US",
            "manufacturer#1.value": manufacturer,
            "country_of_origin#1.value": country_origin.upper() if len(country_origin) == 2 else "CN",
            "condition_type#1.value": condition_value,
            "offerFulfillment": fulfillment_value,
            "automated_pricing_rule_type#1.value": "disabled",
            "supplier_declared_dg_hz_regulation#1.value": "not_applicable",
            "unit_count#1.type.language_tag": "en_US",
            "unit_count#1.type.value": "العد",
            "unit_count#1.value": 1.0,
            "included_components#1.language_tag": "en_US",
            "included_components#1.value": name,
            "purchasable_offer#1.our_price#1.schedule#1.value_with_tax": price,
            "purchasable_offer#1.maximum_retail_price#1.schedule#1.value_with_tax": price,
            "fulfillment_availability#1.quantity": quantity,
        }

        if ean:
            attr_flat["externally_assigned_product_identifier#1.type"] = "upc/ean/gtin"
            attr_flat["externally_assigned_product_identifier#1.value"] = str(ean)

        if bullet_points and isinstance(bullet_points, list) and len(bullet_points) > 0:
            attr_flat["bullet_point#1.language_tag"] = "en_US"
            attr_flat["bullet_point#1.value"] = str(bullet_points[0])
        else:
            attr_flat["bullet_point#1.language_tag"] = "en_US"
            attr_flat["bullet_point#1.value"] = name

        # Build the full listing structure
        return {
            "listing": {
                "listingDetails": {
                    "isDraft": True,
                    "skuState": "Draft",
                    "attributePropertiesImsV3": json.dumps(attr_ims, ensure_ascii=False),
                    "attributeProperties": attr_flat,
                    "listingLanguageCode": "en_US",
                },
                "metadata": {
                    "menus": [{"attributeGroups": []}],
                    "metadataNamespace": "UMP",
                },
                "offerOnly": {},
            },
        }

    async def _native_post(self, payload_json: str) -> Dict[str, Any]:
        """
        Execute a native POST from INSIDE the browser using page.evaluate().
        This bypasses Amazon's WAF because the request comes from a real browser.
        """
        csrf = self._csrf_token

        result = await self.page.evaluate("""
            async (params) => {
                const { payload, csrf } = params;

                const formData = new URLSearchParams();
                formData.append('data', payload);
                formData.append('anti-csrftoken-a2z', csrf);

                try {
                    const res = await fetch('/abis/ajax/create-listing', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
                            'X-Requested-With': 'XMLHttpRequest',
                            'anti-csrftoken-a2z': csrf,
                            'x-csrf-token': csrf,
                        },
                        body: formData.toString(),
                    });

                    const text = await res.text();
                    let json;
                    try {
                        json = JSON.parse(text);
                    } catch (e) {
                        return {
                            success: false,
                            status: 'PARSE_ERROR',
                            error: 'Response not JSON: ' + text.substring(0, 300),
                            raw: text.substring(0, 500),
                        };
                    }

                    return {
                        success: json.status === 'SUCCESS',
                        status: json.status || 'ERROR',
                        asin: json.asin || '',
                        listing_id: json.listingId || '',
                        message: json.message || json.error || '',
                        raw: json,
                    };
                } catch (e) {
                    return {
                        success: false,
                        status: 'FETCH_ERROR',
                        error: e.message,
                    };
                }
            }
        """, {"payload": payload_json, "csrf": csrf})

        logger.info(f"[ALister] POST result: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")

        if result.get("success"):
            logger.info(f"[ALister] SUCCESS! ASIN={result.get('asin')}, Listing ID={result.get('listing_id')}")
            return {
                "success": True,
                "status": "SUCCESS",
                "asin": result.get("asin", ""),
                "listing_id": result.get("listing_id", ""),
            }
        else:
            error = result.get("error", result.get("message", "Unknown"))
            logger.error(f"[ALister] FAILED: {error}")
            return {
                "success": False,
                "status": result.get("status", "ERROR"),
                "error": error,
                "response": result.get("raw"),
            }

    async def _extract_csrf_from_page(self) -> Optional[str]:
        """Extract CSRF token from the page using multiple strategies."""
        try:
            token = await self.page.evaluate("""
                () => {
                    // Strategy 1: window object
                    const windowToken = window['anti-csrftoken-a2z'] || window.a2zToken;
                    if (windowToken && windowToken.length > 20) return windowToken;

                    // Strategy 2: DOM meta tag
                    const metaToken = document.querySelector('[name="anti-csrftoken-a2z"]')?.content;
                    if (metaToken && metaToken.length > 20) return metaToken;

                    // Strategy 3: hidden input
                    const inputToken = document.querySelector('input[name="anti-csrftoken-a2z"]')?.value;
                    if (inputToken && inputToken.length > 20) return inputToken;

                    return "";
                }
            """)

            if token and len(token) > 20:
                return token

            # Fallback: scan page HTML
            content = await self.page.content()
            for pattern in [r'"anti-csrftoken-a2z"\s*:\s*"([^"]+)"', r'anti-csrftoken-a2z["\']\s*:\s*["\']([^"\']+)["\']']:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    t = match.group(1)
                    if len(t) > 20 and not t.startswith('mons_'):
                        return t

            return None

        except Exception as e:
            logger.error(f"[ALister] CSRF extraction failed: {e}")
            return None

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

                raw_ss = c.get("sameSite", "")
                if raw_ss:
                    ss_lower = str(raw_ss).lower()
                    if ss_lower == "strict":
                        pw_c["sameSite"] = "Strict"
                    elif ss_lower == "none":
                        pw_c["sameSite"] = "None"
                    else:
                        pw_c["sameSite"] = "Lax"

                pw_cookies.append(pw_c)

            return pw_cookies
        except Exception as e:
            logger.error(f"[ALister] Failed to load cookies: {e}")
            return []
        finally:
            db.close()

    async def _cleanup(self):
        """Clean up browser"""
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass

    async def close(self):
        """Public cleanup method"""
        await self._cleanup()
