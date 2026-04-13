"""
Amazon Direct API Service
يرفع المنتجات لـ Amazon مباشرة عبر الـ ABIS AJAX API
بنفس الطريقة اللي ALister بيستخدمها

Endpoints:
- /abis/ajax/create-listing  (إنشاء Listing)
- /abis/product/ajax/CreationValidation (التحقق)
- /abis/ajax/create-offer (إضافة عرض لمنتج موجود)

Updated: Now uses curl_cffi (TLS impersonation) + CookieJar (RFC 6265)
instead of niquests + manual cookie handling.
"""
import json
import re
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from loguru import logger

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.models.product import Product
from app.services.session_store import decrypt_data
from app.services.amazon_http_client import AmazonHTTPClient, SessionExpiredError
from app.services.user_agent_config import get_browser_headers
from app.services.amazon_session_manager import AmazonSessionManager

# Amazon Seller Central URLs
SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}


class AmazonDirectAPI:
    """
    يرسل بيانات المنتجات مباشرة لـ Amazon عبر ABIS AJAX API.
    Uses curl_cffi (TLS impersonation) + CookieJar (RFC 6265).
    """

    def __init__(self, email: str = "amazon_eg"):
        self.email = email
        self.client: Optional[AmazonHTTPClient] = None
        self.country_code = "eg"
        self.base_url = SELLER_CENTRAL_BASE["eg"]
        self.csrf_token = None
        self._authenticated = False

    def _setup_session(self) -> bool:
        """يجهز الجلسة بالـ cookies المحفوظة — الآن يستخدم AmazonHTTPClient"""
        db = SessionLocal()
        try:
            auth_session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.cookies_json.isnot(None),
            ).order_by(AuthSession.created_at.desc()).first()

            if not auth_session or not auth_session.cookies_json:
                logger.warning(f"No active browser session with cookies found")
                return False

            cookies = json.loads(decrypt_data(auth_session.cookies_json))
            self.country_code = auth_session.country_code or "eg"
            self.base_url = SELLER_CENTRAL_BASE.get(self.country_code, SELLER_CENTRAL_BASE["eg"])
            self.email = auth_session.email or auth_session.seller_name or self.email
            self.csrf_token = auth_session.csrf_token

            logger.info(f"Session setup for {self.email} ({self.country_code.upper()}) — {len(cookies)} cookies, CSRF: {'YES' if self.csrf_token else 'NO'}")

            # Create curl_cffi client with CookieJar + TLS impersonation
            self.client = AmazonHTTPClient(cookies, self.country_code)
            self._authenticated = True
            return True

        except Exception as e:
            logger.error(f"Session setup failed: {e}")
            return False
        finally:
            db.close()

    def _invalidate_session(self):
        """Auto-invalidate session in DB when we detect expired cookies"""
        try:
            db = SessionLocal()
            try:
                # Invalidate ANY active browser session (matches _setup_session logic)
                auth_session = db.query(AuthSession).filter(
                    AuthSession.auth_method == "browser",
                    AuthSession.is_active == True,
                ).order_by(AuthSession.created_at.desc()).first()

                if auth_session:
                    auth_session.is_active = False
                    auth_session.is_valid = False
                    auth_session.last_verified_at = None
                    db.commit()
                    logger.warning(f"🔒 Auto-invalidated expired session for {auth_session.email}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")

    def _make_request(self, url: str, data: Dict, method: str = "POST") -> Optional[Dict]:
        """يعمل request لـ Amazon API مع ABIS headers الكاملة — باستخدام curl_cffi"""
        if not self.client or not self._authenticated:
            if not self._setup_session():
                return None

        try:
            # Build complete ABIS headers
            abis_headers = {
                "User-Agent": self.client.session.headers.get("User-Agent"),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": f"https://sellercentral.amazon.{self.country_code}",
                "Referer": f"https://sellercentral.amazon.{self.country_code}/product-search/search",  # NOT add-product.html
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }

            # Add CSRF token if available
            if self.csrf_token:
                abis_headers["anti-csrftoken-a2z"] = self.csrf_token
                abis_headers["x-csrf-token"] = self.csrf_token

            # curl_cffi uses the session directly
            if method == "POST":
                response = self.client.session.post(
                    url,
                    data=data,
                    headers=abis_headers,
                    timeout=30,
                    allow_redirects=True,
                )
            else:
                response = self.client.session.get(
                    url,
                    headers=abis_headers,
                    timeout=30,
                    allow_redirects=True,
                )

            logger.debug(f"Request to {url}: Status {response.status_code}")

            if response.status_code == 200:
                try:
                    return response.json()
                except Exception:
                    # 🔴 FORENSIC DUMP — Print first 1000 chars of HTML
                    response_text = response.text
                    is_html = "<html" in response_text[:200].lower() or "<!doctype" in response_text[:100].lower()

                    if is_html:
                        logger.error("🔴 Received HTML instead of JSON. Dumping first 1000 chars:")
                        logger.error(response_text[:1000])

                        lower_text = response_text.lower()
                        if "/ap/signin" in lower_text or "login" in lower_text[:500]:
                            page_type = "LOGIN PAGE — session expired"
                        elif "captcha" in lower_text or "robot" in lower_text:
                            page_type = "CAPTCHA/Robot Check"
                        else:
                            page_type = "Unknown HTML page"

                        self._authenticated = False
                        self._invalidate_session()
                        return {
                            "status": "ERROR",
                            "message": f"🔴 Amazon returned {page_type}. Please re-login.",
                            "session_expired": True,
                            "page_type": page_type,
                        }

                    logger.debug(f"Non-JSON response from {url}")
                    return {"raw_html": response_text[:500]}
            elif response.status_code == 401 or "/ap/signin" in str(response.url):
                self._authenticated = False
                self._invalidate_session()
                logger.warning("🔴 Session expired — Amazon redirected to login.")
                return {
                    "status": "ERROR",
                    "message": "🔴 Session expired. Please re-login.",
                    "session_expired": True
                }
            else:
                logger.error(f"Request failed: {response.status_code}")
                return {
                    "status": "ERROR",
                    "message": f"HTTP {response.status_code} from Amazon"
                }

        except SessionExpiredError:
            self._authenticated = False
            self._invalidate_session()
            logger.warning("🔴 Session expired detected")
            return {
                "status": "ERROR",
                "message": "🔴 Session expired. Please re-login.",
                "session_expired": True
            }
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def _build_create_listing_payload(self, product: Product) -> Dict[str, Any]:
        """يبني JSON payload لإنشاء Listing"""
        return {
            "listing": {
                "listingDetails": {
                    "listingLanguageCode": "en_US",
                    "productType": "",
                    "marketplaceId": "ARBP9OOSHTCHU",  # Egypt
                    "sku": product.sku,
                },
                "attributes": {
                    "item_name": {
                        "language_tag": "en_US",
                        "value": product.name,
                        "markup": "<text>",
                    },
                    "product_description": {
                        "language_tag": "en_US",
                        "value": product.description or product.name,
                        "markup": "<text>",
                    },
                    "standard_price": [
                        {
                            "currency": "EGP",
                            "value": float(product.price) if product.price else 0,
                        }
                    ],
                    "quantity": int(product.quantity) if product.quantity else 0,
                    "fulfillment_channel": product.fulfillment_channel or "MFN",
                    "condition_type": product.condition or "New",
                    "brand": product.brand or "Generic",
                    "manufacturer": product.manufacturer or product.brand or "Generic",
                },
            },
        }

    async def create_listing(self, product_id: str) -> Dict[str, Any]:
        """
        ينشئ Listing جديد على Amazon.
        
        Args:
            product_id: معرف المنتج في قاعدة البيانات
            
        Returns:
            {
                "success": bool,
                "message": str,
                "listing_id": str (لو نجح)
            }
        """
        try:
            if not self._authenticated:
                if not self._setup_session():
                    return {
                        "success": False,
                        "error": "No active session - please login again",
                    }

            # Get product from DB
            db = SessionLocal()
            try:
                product = db.query(Product).filter(Product.id == product_id).first()
                if not product:
                    return {
                        "success": False,
                        "error": f"Product {product_id} not found",
                    }
            finally:
                db.close()

            logger.info(f"Creating listing for product: {product.sku}")

            # Step 1: Validation
            validation_result = await self._validate_listing(product)
            if validation_result and validation_result.get("status") == "ERROR":
                return {
                    "success": False,
                    "error": f"Validation failed: {validation_result.get('message', 'Unknown error')}",
                }

            # Step 2: Create listing
            result = await self._post_create_listing(product)

            logger.info(f"_post_create_listing result: {json.dumps(result, indent=2, ensure_ascii=False) if result else 'None'}")

            if result and result.get("status") == "SUCCESS":
                logger.info(f"Listing created successfully for {product.sku}")
                return {
                    "success": True,
                    "message": f"Listing created for {product.sku}",
                    "listing_id": result.get("listingId", ""),
                    "asin": result.get("asin", ""),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error during listing creation"),
                }

        except Exception as e:
            logger.error(f"Create listing failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _validate_listing(self, product: Product) -> Optional[Dict]:
        """يتحقق من بيانات الـ Listing قبل الإرسال"""
        try:
            url = f"{self.base_url}/abis/product/ajax/CreationValidation"
            payload = self._build_create_listing_payload(product)

            data = {
                "data": json.dumps(payload),
                "clientContext": self._get_client_context(),
            }

            result = self._make_request(url, data)
            return result

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return None

    async def _post_create_listing(self, product: Product) -> Optional[Dict]:
        """يرسل طلب إنشاء الـ Listing"""
        try:
            url = f"{self.base_url}/abis/ajax/create-listing"
            payload = self._build_create_listing_payload(product)

            data = {
                "data": json.dumps(payload),
                "clientContext": self._get_client_context(),
            }

            result = self._make_request(url, data)
            return result

        except Exception as e:
            logger.error(f"Create listing POST failed: {e}")
            return None

    async def create_offer(self, asin: str, sku: str, price: float, quantity: int) -> Dict[str, Any]:
        """
        ينشئ عرض (Offer) على ASIN موجود.
        
        Args:
            asin: Amazon ASIN
            sku: Product SKU
            price: Price
            quantity: Quantity
            
        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        try:
            if not self._authenticated:
                if not self._setup_session():
                    return {
                        "success": False,
                        "error": "No active session - please login again",
                    }

            url = f"{self.base_url}/abis/ajax/create-offer"
            payload = {
                "asin": asin,
                "sku": sku,
                "price": {
                    "currency": "EGP",
                    "value": float(price),
                },
                "quantity": int(quantity),
                "condition_type": "New",
                "fulfillment_channel": "MFN",
            }

            data = {
                "data": json.dumps(payload),
                "clientContext": self._get_client_context(),
            }

            result = self._make_request(url, data)

            if result and result.get("status") == "SUCCESS":
                logger.info(f"Offer created for ASIN {asin}")
                return {
                    "success": True,
                    "message": f"Offer created for {asin}",
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Failed to create offer"),
                }

        except Exception as e:
            logger.error(f"Create offer failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def update_inventory(self, sku: str, quantity: int, price: Optional[float] = None) -> Dict[str, Any]:
        """
        يحدث المخزون والسعر لمنتج موجود.
        
        Args:
            sku: Product SKU
            quantity: New quantity
            price: New price (optional)
            
        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        try:
            if not self._authenticated:
                if not self._setup_session():
                    return {
                        "success": False,
                        "error": "No active session - please login again",
                    }

            url = f"{self.base_url}/myinventory/gql"
            
            # GraphQL mutation
            query = """
                mutation UpdateInventory($input: InventoryUpdateInput!) {
                    inventoryUpdate(input: $input) {
                        results {
                            contributorToken
                            resultingQuantity
                            sku
                            result {
                                successful
                                message
                                internalMessage
                            }
                        }
                    }
                }
            """

            variables = {
                "input": {
                    "sku": sku,
                    "quantity": quantity,
                }
            }

            if price is not None:
                query = """
                    mutation UpdatePrice($input: PriceUpdateInput!) {
                        priceUpdate(input: $input) {
                            results {
                                sku
                                result {
                                    successful
                                    message
                                }
                            }
                        }
                    }
                """
                variables = {
                    "input": {
                        "sku": sku,
                        "price": {
                            "currency": "EGP",
                            "value": float(price),
                        },
                    }
                }

            payload = {
                "query": query,
                "variables": json.dumps(variables),
            }

            data = {
                "data": json.dumps(payload),
                "clientContext": self._get_client_context(),
            }

            result = self._make_request(url, data)

            if result:
                logger.info(f"Inventory updated for {sku}")
                return {
                    "success": True,
                    "message": f"Inventory updated for {sku}",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update inventory",
                }

        except Exception as e:
            logger.error(f"Update inventory failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _get_client_context(self) -> str:
        """يجيب client context للـ requests"""
        # This is a simplified version - ALister extracts this from webpack
        return json.dumps({
            "clientContext": {
                "marketplaceId": "ARBP9OOSHTCHU",
                "languageCode": "en_US",
            }
        })
