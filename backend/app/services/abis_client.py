"""
ABIS Client (Amazon Business Information System)
Phase 4: Listing Submission with correct payload format

Directives:
- Content-Type: application/x-www-form-urlencoded (NOT application/json)
- JSON passed as STRING inside form field: data={"listing": {...}}
- CSRF Token mandatory in headers
- Matching ALL headers from real browser request
- Uses curl_cffi for TLS fingerprint impersonation (Chrome 131)
- Uses CookieJar for RFC 6265 compliant cookie management
"""
import json
import re
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
    Handles listing creation with proper payload format and CSRF protection.
    
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

    def create_listing(self, product_data: Dict[str, Any], csrf_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a listing via ABIS AJAX endpoint.

        The payload is sent as application/x-www-form-urlencoded with
        JSON string inside the 'data' field.

        Args:
            product_data: Product listing data (will be JSON-encoded)
            csrf_token: CSRF token (will fetch if not provided)

        Returns:
            {
                "success": bool,
                "status": str,
                "listing_id": str,
                "asin": str,
                "error": str or None
            }
        """
        token = csrf_token or self.csrf_token

        # =============================================
        # FAIL-FAST: Cannot POST without CSRF token!
        # =============================================
        if not token:
            logger.error("🚨 FAIL-FAST: No CSRF token available! Fetching fresh token before POST...")
            token = self.fetch_csrf_from_page()
            if not token:
                logger.error("❌ FATAL: Still no CSRF token after fetch attempt. Aborting POST to prevent session destruction!")
                return {
                    "success": False,
                    "error": "Missing CSRF Token — cannot submit listing without valid token",
                    "session_expired": False,
                }
            logger.info(f"✅ CSRF token fetched just-in-time: {token[:20]}...")

        # Build the ABIS payload — form-encoded with JSON string
        listing_payload = {
            "listing": {
                "listingDetails": {
                    "listingLanguageCode": "en_US",
                    "productType": product_data.get("product_type", ""),
                    "marketplaceId": self._get_marketplace_id(),
                    "sku": product_data.get("sku", ""),
                },
                "attributes": {
                    "item_name": {
                        "language_tag": "en_US",
                        "value": product_data.get("name", ""),
                        "markup": "<text>",
                    },
                    "product_description": {
                        "language_tag": "en_US",
                        "value": product_data.get("description", ""),
                        "markup": "<text>",
                    },
                    "standard_price": [
                        {
                            "currency": product_data.get("currency", "EGP"),
                            "value": float(product_data.get("price", 0)),
                        }
                    ],
                    "quantity": int(product_data.get("quantity", 0)),
                    "fulfillment_channel": product_data.get("fulfillment_channel", "MFN"),
                    "condition_type": product_data.get("condition", "New"),
                    "brand": product_data.get("brand", "Generic"),
                    "manufacturer": product_data.get("manufacturer", product_data.get("brand", "Generic")),
                },
            },
        }

        # Add optional fields
        attrs = listing_payload["listing"]["attributes"]
        if product_data.get("bullet_points"):
            attrs["bullet_point"] = product_data["bullet_points"]
        if product_data.get("upc"):
            attrs["upc"] = [{"value": product_data["upc"]}]
        if product_data.get("ean"):
            attrs["ean"] = [{"value": product_data["ean"]}]
        if product_data.get("model_number"):
            attrs["model_number"] = [{"value": product_data["model_number"]}]
        if product_data.get("country_of_origin"):
            attrs["country_of_origin"] = [{"value": product_data["country_of_origin"]}]
        if product_data.get("material"):
            attrs["material"] = [{"value": product_data["material"]}]

        # Client context
        client_context = {
            "marketplaceId": self._get_marketplace_id(),
            "languageCode": "en_US",
        }

        # Form-encoded payload (JSON strings inside form fields)
        form_data = {
            "data": json.dumps(listing_payload, ensure_ascii=False),
            "clientContext": json.dumps(client_context, ensure_ascii=False),
        }

        # Build headers with CSRF token — THE ABIS HEADER TRINITY
        # These 3 headers are MANDATORY for Amazon to treat this as AJAX:
        # 1. X-Requested-With: XMLHttpRequest (tells Amazon this is AJAX, not browsing)
        # 2. Content-Type: application/x-www-form-urlencoded (NOT application/json!)
        # 3. Accept: application/json, text/javascript, */*; q=0.01
        headers = {
            "User-Agent": AMAZON_USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/product-search/search",  # NOT add-product.html (404!)
            "X-Requested-With": "XMLHttpRequest",  # 🔴 THE AJAX HEADER
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # CSRF tokens (mandatory)
        if token:
            headers["anti-csrftoken-a2z"] = token
            headers["x-csrf-token"] = token

        url = "/abis/ajax/create-listing"

        logger.info(f"ABIS POST {url}")
        logger.debug(f"Form data keys: {list(form_data.keys())}")
        logger.debug(f"CSRF token: {token[:20] if token else 'MISSING'}...")

        try:
            client = self._get_client()

            # curl_cffi session — sends form-encoded data with AJAX headers
            response = client.session.post(
                f"{self.base_url}{url}",
                data=form_data,
                headers=headers,
                timeout=30,
            )

            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Final URL: {response.url}")
            logger.debug(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")

            # Check for redirect to login (session expired)
            if "/ap/signin" in str(response.url) or "/gp/signin" in str(response.url):
                return {
                    "success": False,
                    "status": "SESSION_EXPIRED",
                    "error": "Session expired — redirected to login page",
                }

            # Try to parse JSON response
            try:
                result = response.json()
            except Exception:
                # Check if response is HTML (error page)
                response_text = response.text
                is_html = "<html" in response_text[:200].lower() or "<!doctype" in response_text[:100].lower()

                if is_html:
                    # 🔴 FORENSIC DUMP — Print first 1000 chars to identify the page
                    logger.error("🔴 Received HTML instead of JSON. Dumping first 1000 chars for forensics:")
                    logger.error(response_text[:1000])

                    # Try to identify what kind of page it is
                    lower_text = response_text.lower()
                    if "/ap/signin" in lower_text or "login" in lower_text[:500]:
                        page_type = "LOGIN PAGE — session expired"
                    elif "captcha" in lower_text or "robot" in lower_text:
                        page_type = "CAPTCHA/Robot Check — WAF blocked us"
                    elif "error" in lower_text:
                        page_type = "Error page — likely malformed request"
                    else:
                        page_type = "Unknown HTML page"

                    return {
                        "success": False,
                        "status": "HTML_RESPONSE",
                        "error": f"Received HTML instead of JSON — {page_type}",
                        "html_preview": response_text[:500],
                    }

                # Not HTML but not JSON either (maybe empty or plain text)
                result = {"raw": response_text[:500]}

            # Check for success
            if result.get("status") == "SUCCESS":
                logger.info(f"✅ Listing created successfully")
                return {
                    "success": True,
                    "status": "SUCCESS",
                    "listing_id": result.get("listingId", ""),
                    "asin": result.get("asin", ""),
                    "message": result.get("message", ""),
                }
            else:
                error_msg = result.get("message", result.get("error", "Unknown error"))
                logger.warning(f"❌ Listing creation failed: {error_msg}")
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
                "error": "Session expired — redirected to login page",
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status": "UNEXPECTED_ERROR",
                "error": str(e),
            }

    def _get_marketplace_id(self) -> str:
        """Get marketplace ID for country."""
        marketplace_ids = {
            "eg": "ARBP9OOSHTCHU",
            "sa": "A17E79C6D8DWNP",
            "ae": "A2VIGQ35RCS4UG",
        }
        return marketplace_ids.get(self.country_code, "ARBP9OOSHTCHU")

    def close(self):
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
