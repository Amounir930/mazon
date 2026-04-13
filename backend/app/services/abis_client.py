"""
ABIS Client (Amazon Business Information System)
Phase 5: Clone & Inject pattern (reverse-engineered from ALister)

Flow:
1. GET /abis/ajax/create-listing?productType=X → fetches live template with formId, formVersion, etc.
2. Inject product data into the template (SKU, price, quantity, name, etc.)
3. POST the modified template as URL-encoded form data

This avoids 403 selection_required because we use Amazon's own template with all required session fields.
"""
import json
import re
from urllib.parse import urlencode
from typing import Dict, Any, Optional, List
from loguru import logger

from app.services.amazon_http_client import AmazonHTTPClient, SessionExpiredError
from app.services.user_agent_config import AMAZON_USER_AGENT

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}


class ABISClient:
    """
    Client for Amazon ABIS AJAX endpoints.
    Uses Clone & Inject pattern: GET live template → Inject data → POST.

    Uses curl_cffi (TLS impersonation) + CookieJar (RFC 6265).
    """

    def __init__(self, cookies: List[Dict[str, Any]], country_code: str = "eg"):
        self.country_code = country_code.lower()
        self.base_url = SELLER_CENTRAL_BASE.get(self.country_code, SELLER_CENTRAL_BASE["eg"])
        self.cookies = cookies
        self.csrf_token: Optional[str] = None
        self._client: Optional[AmazonHTTPClient] = None

    def _get_client(self) -> AmazonHTTPClient:
        """Get or create HTTP client with cookies (curl_cffi + CookieJar)."""
        if self._client is None:
            self._client = AmazonHTTPClient(self.cookies, self.country_code)
        return self._client

    def fetch_csrf_from_page(self) -> Optional[str]:
        """Fetch a page and extract CSRF token using curl_cffi (HTTP client, not browser)."""
        client = self._get_client()

        # Try multiple URLs to fetch CSRF token
        urls_to_try = [
            f"{self.base_url}/product-search/search",
            f"{self.base_url}/product-search",
            f"{self.base_url}/home",
        ]

        for url in urls_to_try:
            try:
                logger.info(f"Fetching CSRF from: {url}")
                response = client.session.get(url, allow_redirects=True, timeout=15)

                if response.status_code == 200:
                    token = client.extract_csrf_from_response(response.text)
                    if token:
                        self.csrf_token = token
                        logger.info(f"✅ CSRF token fetched successfully: {token[:20]}... ({len(token)} chars)")
                        return token
                    else:
                        logger.debug(f"No CSRF token found on {url}")
            except SessionExpiredError:
                raise
            except Exception as e:
                logger.debug(f"Failed to fetch CSRF from {url}: {e}")

        logger.error("❌ Failed to fetch CSRF token from any page!")
        return None

    def fetch_live_template(self, product_type: str = "HOME_ORGANIZERS_AND_STORAGE", language: str = "ar_AE") -> Optional[Dict]:
        """
        Phase 1: Fetch the LIVE listing template from Amazon via GET request.
        This returns the full JSON template with formId, formVersion, experience, etc.

        Args:
            product_type: Amazon product type (e.g. HOME_ORGANIZERS_AND_STORAGE)
            language: Listing language (e.g. ar_AE, en_US)

        Returns:
            JSON template dict or None
        """
        client = self._get_client()

        url = f"{self.base_url}/abis/ajax/create-listing"
        params = {
            "productType": product_type,
            "listingLanguageCode": language,
        }

        headers = {
            "User-Agent": AMAZON_USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/product-search/search",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        logger.info(f"📥 GET live template: {url}?productType={product_type}&listingLanguageCode={language}")

        try:
            response = client.session.get(url, params=params, headers=headers, timeout=30, allow_redirects=True)
            logger.info(f"  Response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"  ❌ Failed to fetch template: HTTP {response.status_code}")
                logger.error(f"  Response body (first 500): {response.text[:500]}")
                return None

            template = response.json()
            logger.info(f"  ✅ Template fetched! Keys: {list(template.keys())[:10]}")

            # Log the listingDetails structure
            if "listing" in template:
                listing = template["listing"]
                if "listingDetails" in listing:
                    details = listing["listingDetails"]
                    logger.info(f"  listingDetails keys: {list(details.keys())[:15]}")
                    if "attributePropertiesImsV3" in details:
                        ims = details["attributePropertiesImsV3"]
                        # It might be a JSON string
                        if isinstance(ims, str):
                            try:
                                ims_parsed = json.loads(ims)
                                logger.info(f"  attributePropertiesImsV3 keys: {list(ims_parsed.keys())[:20]}")
                            except:
                                logger.info(f"  attributePropertiesImsV3 (string, {len(ims)} chars)")
                        else:
                            logger.info(f"  attributePropertiesImsV3 keys: {list(ims.keys())[:20]}")

            return template

        except SessionExpiredError:
            logger.error("  ❌ Session expired while fetching template")
            return None
        except Exception as e:
            logger.error(f"  ❌ Failed to fetch template: {e}")
            return None

    def inject_product_data(self, template: Dict, product_data: Dict[str, Any]) -> Dict:
        """
        Phase 2: Inject product data into the live template.

        Args:
            template: The live template from fetch_live_template()
            product_data: Product data dict (sku, name, price, quantity, etc.)

        Returns:
            Modified template dict ready for POST
        """
        logger.info("💉 Injecting product data into template...")

        listing = template.get("listing", {})
        details = listing.get("listingDetails", {})

        # Set SKU at the listing level
        template["listing"]["sku"] = product_data.get("sku", "")

        # Handle attributePropertiesImsV3 (may be a JSON string or dict)
        ims_v3 = details.get("attributePropertiesImsV3", {})
        if isinstance(ims_v3, str):
            try:
                ims_v3 = json.loads(ims_v3)
            except:
                logger.warning("  ⚠️ Could not parse attributePropertiesImsV3 as JSON")
                ims_v3 = {}

        if not isinstance(ims_v3, dict):
            ims_v3 = {}

        # Inject item_name (title)
        ims_v3["item_name"] = [{
            "value": product_data.get("name", ""),
            "language_tag": "en_US",
            "markup": "<text>",
        }]

        # Inject product_description
        ims_v3["product_description"] = [{
            "value": product_data.get("description", product_data.get("name", "")),
            "language_tag": "en_US",
            "markup": "<text>",
        }]

        # Inject brand
        brand = product_data.get("brand", "Generic").strip()
        if not brand:
            brand = "Generic"
        ims_v3["brand"] = [{"value": brand}]
        ims_v3["manufacturer"] = [{"value": product_data.get("manufacturer", brand)}]

        # Inject purchasable_offer (price + quantity)
        currency = product_data.get("currency", "EGP")
        price = float(product_data.get("price", 0))
        quantity = int(product_data.get("quantity", 0))

        ims_v3["purchasable_offer"] = [{
            "our_price": [{
                "schedule": [{
                    "value_with_tax": price,
                }]
            }],
            "quantity": [{
                "amount": quantity,
            }],
            "fulfillment_channel": [{
                "value": product_data.get("fulfillment_channel", "MFN"),
            }],
            "condition_type": [{
                "value": product_data.get("condition", "New"),
            }],
        }]

        # Inject standard_price (alternative format)
        ims_v3["standard_price"] = [{
            "currency": currency,
            "value": price,
        }]

        # Inject optional fields
        if product_data.get("bullet_points"):
            ims_v3["bullet_point"] = product_data["bullet_points"]
        if product_data.get("upc"):
            ims_v3["externally_assigned_product_identifier"] = [{
                "type": "UPC",
                "value": product_data["upc"],
            }]
        if product_data.get("ean"):
            ims_v3["externally_assigned_product_identifier"] = [{
                "type": "EAN",
                "value": product_data["ean"],
            }]
        if product_data.get("country_of_origin"):
            ims_v3["country_of_origin"] = [{"value": product_data["country_of_origin"]}]
        if product_data.get("model_number"):
            ims_v3["model_number"] = [{"value": product_data["model_number"]}]
        if product_data.get("material"):
            ims_v3["material"] = [{"value": product_data["material"]}]

        # Write back the modified IMSv3 as JSON string
        details["attributePropertiesImsV3"] = json.dumps(ims_v3, ensure_ascii=False)
        listing["listingDetails"] = details
        template["listing"] = listing

        logger.info(f"  ✅ Product data injected: SKU={product_data.get('sku')}, Price={price}, Qty={quantity}")
        return template

    def create_listing(self, product_data: Dict[str, Any], csrf_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a listing via ABIS using Clone & Inject pattern:
        1. GET live template from Amazon
        2. Inject product data into template
        3. POST the modified template

        Args:
            product_data: Product listing data
            csrf_token: CSRF token

        Returns:
            { "success": bool, "status": str, "listing_id": str, "asin": str, "error": str }
        """
        token = csrf_token or self.csrf_token

        # FAIL-FAST: Cannot POST without CSRF token
        if not token:
            logger.error("🚨 FAIL-FAST: No CSRF token available! Fetching fresh token...")
            token = self.fetch_csrf_from_page()
            if not token:
                logger.error("❌ FATAL: Still no CSRF token after fetch attempt!")
                return {
                    "success": False,
                    "error": "Missing CSRF Token — cannot submit listing without valid token",
                    "session_expired": False,
                }
            logger.info(f"✅ CSRF token fetched: {token[:20]}...")

        # =============================================
        # Phase 1: Fetch live template (GET)
        # =============================================
        product_type = "HOME_ORGANIZERS_AND_STORAGE"
        template = self.fetch_live_template(product_type=product_type, language="ar_AE")

        if not template:
            logger.error("❌ Failed to fetch live template — cannot proceed")
            return {
                "success": False,
                "error": "Failed to fetch listing template from Amazon",
                "session_expired": True,
            }

        # =============================================
        # Phase 2: Inject product data
        # =============================================
        injected = self.inject_product_data(template, product_data)

        # =============================================
        # Phase 3: POST the modified template
        # =============================================
        client = self._get_client()
        url = f"{self.base_url}/abis/ajax/create-listing"

        # URL-encoded form data — the template JSON goes in the 'data' field
        form_data = {
            "data": json.dumps(injected, ensure_ascii=False),
        }

        # Add CSRF token in form data (some ABIS endpoints check this)
        if token:
            form_data["anti-csrftoken-a2z"] = token

        headers = {
            "User-Agent": AMAZON_USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/product-search/search",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        if token:
            headers["anti-csrftoken-a2z"] = token
            headers["x-csrf-token"] = token

        logger.info(f"📤 POST {url}")
        logger.info(f"  Form data size: {len(form_data['data'])} chars")
        logger.info(f"  CSRF token: {token[:20]}... ({len(token)} chars)")
        logger.info(f"  Cookies: {len([c for c in self.cookies if c.get('name') and c.get('value') is not None])}")

        try:
            response = client.session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=30,
            )

            logger.info(f"  Response status: {response.status_code}")

            # 403 forensic analysis
            if response.status_code == 403:
                logger.error("🔴 403 FORBIDDEN!")
                logger.error(f"  URL: {response.url}")
                logger.error(f"  Body (first 1500): {response.text[:1500]}")
                try:
                    logger.error(f"  JSON: {json.dumps(response.json(), indent=2)}")
                except:
                    pass

                lower_text = response.text.lower()
                if "captcha" in lower_text or "robot" in lower_text:
                    page_type = "CAPTCHA/WAF blocked"
                elif "csrf" in lower_text or "token" in lower_text or "invalid" in lower_text:
                    page_type = "CSRF Token invalid"
                elif "session" in lower_text or "expired" in lower_text:
                    page_type = "Session expired"
                else:
                    page_type = "Unknown 403"

                return {
                    "success": False,
                    "status": "403_FORBIDDEN",
                    "error": f"Amazon 403: {page_type}",
                    "response_preview": response.text[:500],
                }

            # Session expired check
            if "/ap/signin" in str(response.url) or "/gp/signin" in str(response.url):
                return {
                    "success": False,
                    "status": "SESSION_EXPIRED",
                    "error": "Session expired — redirected to login",
                }

            # Parse JSON response
            try:
                result = response.json()
                if response.status_code >= 400 or result.get("status") != "SUCCESS":
                    logger.error(f"🔴 JSON RESPONSE (status {response.status_code}):")
                    logger.error(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
            except Exception:
                response_text = response.text
                is_html = "<html" in response_text[:200].lower() or "<!doctype" in response_text[:100].lower()
                if is_html:
                    logger.error(f"🔴 HTML response (first 1000): {response_text[:1000]}")
                    return {
                        "success": False,
                        "status": "HTML_RESPONSE",
                        "error": "Received HTML instead of JSON",
                        "html_preview": response_text[:500],
                    }
                result = {"raw": response_text[:500]}

            # Check success
            if result.get("status") == "SUCCESS":
                logger.info(f"✅ Listing created successfully!")
                return {
                    "success": True,
                    "status": "SUCCESS",
                    "listing_id": result.get("listingId", ""),
                    "asin": result.get("asin", ""),
                    "message": result.get("message", ""),
                }
            else:
                error_msg = result.get("message", result.get("error", "Unknown error"))
                logger.warning(f"❌ Listing failed: {error_msg}")
                return {
                    "success": False,
                    "status": result.get("status", "ERROR"),
                    "error": error_msg,
                    "response": result,
                }

        except SessionExpiredError:
            return {
                "success": False,
                "status": "SESSION_EXPIRED",
                "error": "Session expired",
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "status": "UNEXPECTED_ERROR",
                "error": str(e),
            }
