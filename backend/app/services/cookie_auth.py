"""
Cookie-based Amazon Authentication
الـ cookies بتتسجل من الـ Frontend (PyWebView)
وبتتستخدم للـ API calls بدلاً من SP-API
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from loguru import logger

from app.services.session_store import (
    encrypt_data,
    decrypt_data,
    get_fernet,
)
from app.database import SessionLocal
from app.models.session import Session


# ============================================================
# Amazon Seller Central URLs
# ============================================================

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
    "uk": "https://sellercentral.amazon.co.uk",
    "us": "https://sellercentral.amazon.com",
    "de": "https://sellercentral.amazon.de",
    "fr": "https://sellercentral.amazon.fr",
    "it": "https://sellercentral.amazon.it",
    "es": "https://sellercentral.amazon.es",
}

# Login URL paths (relative to base)
LOGIN_PATHS = {
    "eg": "/gp/homepage.html",  # Egypt uses /gp/homepage.html
    "default": "/ap/signin",  # Fallback for other countries
}


# ============================================================
# CookieAuth Service
# ============================================================

class CookieAuth:
    """
    Handles cookie-based authentication for Amazon Seller Central.
    
    Flow:
    1. Generate login URL for a specific country
    2. User logs in via PyWebView (frontend)
    3. Frontend extracts cookies and sends to backend
    4. Backend saves encrypted cookies and verifies them
    """

    @staticmethod
    def generate_login_url(country_code: str = "eg") -> str:
        """
        Generate Amazon Seller Central login URL for a specific country.
        
        Args:
            country_code: Country code (eg, sa, ae, uk, us, ...)
            
        Returns:
            Full URL to Amazon Seller Central login page
        """
        base_url = SELLER_CENTRAL_BASE.get(country_code.lower())
        if not base_url:
            logger.warning(f"Unsupported country code: {country_code}, defaulting to Egypt")
            base_url = SELLER_CENTRAL_BASE["eg"]
            country_code = "eg"
        
        # Get login path for this country
        login_path = LOGIN_PATHS.get(country_code.lower(), LOGIN_PATHS["default"])
        login_url = f"{base_url}{login_path}"
        
        logger.info(f"Generated login URL for {country_code.upper()}: {login_url}")
        return login_url

    @staticmethod
    def save_cookies(
        email: str,
        cookies: List[Dict[str, Any]],
        country_code: str = "eg",
        seller_name: Optional[str] = None,
    ) -> Session:
        """
        Save browser cookies to database (encrypted).
        
        Args:
            email: Amazon account email
            cookies: List of cookie dictionaries from browser
            country_code: Marketplace country code
            seller_name: Optional seller name (will be extracted from cookies if not provided)
            
        Returns:
            Saved Session object
        """
        db = SessionLocal()
        try:
            # Deactivate any existing active browser sessions for this email
            existing = db.query(Session).filter(
                Session.auth_method == "browser",
                Session.email == email,
                Session.is_active == True,  # noqa: E712
            ).first()
            if existing:
                existing.is_active = False
                existing.is_valid = False
                db.flush()

            # Encrypt cookies
            cookies_json = json.dumps(cookies)
            encrypted_cookies = encrypt_data(cookies_json)

            # Estimate expiry (Amazon cookies typically last 30 days)
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            session = Session(
                auth_method="browser",
                email=email,
                country_code=country_code.lower(),
                cookies_json=encrypted_cookies,
                seller_name=seller_name or email,
                is_active=True,
                is_valid=True,
                last_verified_at=datetime.now(timezone.utc),
                expires_at=expires_at,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            logger.info(f"Browser cookies saved: {email} ({country_code.upper()})")
            return session

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save cookies: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def verify_cookies(cookies: List[Dict[str, Any]], country_code: str = "eg") -> bool:
        """
        Verify that cookies are still valid by making a test API call.
        """
        try:
            if not cookies:
                logger.warning("Cookies verification: FAILED - empty cookies list")
                return False

            # Build cookie string for request
            cookie_string = "; ".join([
                f"{c['name']}={c['value']}"
                for c in cookies
                if c.get("name") and c.get("value")
            ])

            if not cookie_string:
                logger.warning("Cookies verification: FAILED - no valid cookies in string")
                return False

            # Test by accessing seller profile page
            base_url = SELLER_CENTRAL_BASE.get(country_code.lower(), SELLER_CENTRAL_BASE["eg"])
            test_url = f"{base_url}/home"

            import niquests as requests

            response = requests.get(
                test_url,
                headers={
                    "Cookie": cookie_string,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                timeout=15,
                allow_redirects=True,
            )

            final_url = str(response.url)
            status_code = response.status_code

            logger.info(f"Cookie verification: URL={final_url}, Status={status_code}")
            logger.info(f"Redirected to signin: {'/ap/signin' in final_url}")
            logger.info(f"Cookie string length: {len(cookie_string)} chars")

            # If we're redirected to login page, cookies are invalid
            is_valid = "/ap/signin" not in final_url and "/gp/signin" not in final_url

            if is_valid:
                logger.info(f"Cookies verification: PASSED ({len(cookies)} cookies)")
            else:
                logger.warning(f"Cookies verification: FAILED - redirected to login ({final_url})")

            return is_valid

        except Exception as e:
            logger.error(f"Cookie verification failed: {e}", exc_info=True)
            return False

    @staticmethod
    def get_active_cookies(email: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get active (valid, non-expired) cookies for an email.
        
        Args:
            email: Amazon account email
            
        Returns:
            List of cookie dictionaries or None if not found/expired
        """
        db = SessionLocal()
        try:
            session = db.query(Session).filter(
                Session.auth_method == "browser",
                Session.email == email,
                Session.is_active == True,  # noqa: E712
                Session.is_valid == True,  # noqa: E712
            ).first()

            if not session or not session.cookies_json:
                logger.debug(f"No active cookies found for {email}")
                return None

            # Decrypt cookies
            decrypted = decrypt_data(session.cookies_json)
            cookies = json.loads(decrypted)

            logger.info(f"Retrieved active cookies for {email}")
            return cookies

        except ValueError as e:
            logger.error(f"Cookie decryption failed for {email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get cookies for {email}: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    async def sync_products(
        cookies: List[Dict[str, Any]],
        country_code: str = "eg",
    ) -> Dict[str, Any]:
        """
        Sync products from Amazon Seller Central using cookies.
        
        Args:
            cookies: List of cookie dictionaries
            country_code: Marketplace country code
            
        Returns:
            Dictionary with products list and metadata
        """
        try:
            # Build cookie string
            cookie_string = "; ".join([
                f"{c['name']}={c['value']}"
                for c in cookies
                if c.get("name") and c.get("value")
            ])

            # Fetch products from Amazon Inventory page
            base_url = SELLER_CENTRAL_BASE.get(country_code.lower(), SELLER_CENTRAL_BASE["eg"])
            inventory_url = f"{base_url}/inventory"

            import niquests as requests
            
            response = requests.get(
                inventory_url,
                headers={
                    "Cookie": cookie_string,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                },
                timeout=30,
                allow_redirects=True,
            )

            if "/ap/signin" in response.url:
                return {
                    "success": False,
                    "error": "Session expired - please login again",
                    "products": [],
                }

            # Parse products from HTML response
            # This is a placeholder - actual parsing depends on Amazon's HTML structure
            products = []  # TODO: Parse products from HTML

            return {
                "success": True,
                "products": products,
                "total": len(products),
            }

        except Exception as e:
            logger.error(f"Failed to sync products: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": [],
            }

    @staticmethod
    async def sync_orders(
        cookies: List[Dict[str, Any]],
        country_code: str = "eg",
    ) -> Dict[str, Any]:
        """
        Sync orders from Amazon Seller Central using cookies.
        
        Args:
            cookies: List of cookie dictionaries
            country_code: Marketplace country code
            
        Returns:
            Dictionary with orders list and metadata
        """
        try:
            # Build cookie string
            cookie_string = "; ".join([
                f"{c['name']}={c['value']}"
                for c in cookies
                if c.get("name") and c.get("value")
            ])

            # Fetch orders from Amazon Orders page
            base_url = SELLER_CENTRAL_BASE.get(country_code.lower(), SELLER_CENTRAL_BASE["eg"])
            orders_url = f"{base_url}/orders"

            import niquests as requests
            
            response = requests.get(
                orders_url,
                headers={
                    "Cookie": cookie_string,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                },
                timeout=30,
                allow_redirects=True,
            )

            if "/ap/signin" in response.url:
                return {
                    "success": False,
                    "error": "Session expired - please login again",
                    "orders": [],
                }

            # Parse orders from HTML response
            # This is a placeholder - actual parsing depends on Amazon's HTML structure
            orders = []  # TODO: Parse orders from HTML

            return {
                "success": True,
                "orders": orders,
                "total": len(orders),
            }

        except Exception as e:
            logger.error(f"Failed to sync orders: {e}")
            return {
                "success": False,
                "error": str(e),
                "orders": [],
            }

    @staticmethod
    def disconnect(email: str) -> bool:
        """
        Disconnect and invalidate cookies for an email.
        
        Args:
            email: Amazon account email
            
        Returns:
            True if session was found and deactivated, False otherwise
        """
        db = SessionLocal()
        try:
            session = db.query(Session).filter(
                Session.auth_method == "browser",
                Session.email == email,
                Session.is_active == True,  # noqa: E712
            ).first()

            if not session:
                logger.warning(f"No active session found for {email}")
                return False

            session.is_active = False
            session.is_valid = False
            db.commit()

            logger.info(f"Disconnected session for {email}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to disconnect session: {e}")
            return False
        finally:
            db.close()
