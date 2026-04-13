"""
Cookie-based Amazon Authentication
الـ cookies بتتسجل من الـ Frontend (PyWebView/Playwright login)
وبتتستخدم للـ API calls بدلاً من SP-API

Updated: Now uses curl_cffi (TLS impersonation) + CookieJar (RFC 6265)
instead of niquests + raw cookie strings.
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
from app.services.user_agent_config import AMAZON_USER_AGENT
from app.services.amazon_http_client import AmazonHTTPClient, SessionExpiredError
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
        csrf_token: Optional[str] = None,
    ) -> Session:
        """
        Save browser cookies to database (encrypted).

        Args:
            email: Amazon account email
            cookies: List of cookie dictionaries from browser
            country_code: Marketplace country code
            seller_name: Optional seller name (will be extracted from cookies if not provided)
            csrf_token: Amazon anti-CSRF token for ABIS requests

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
                csrf_token=csrf_token,
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
        Now uses curl_cffi + CookieJar for undetectable requests.
        """
        try:
            if not cookies:
                logger.warning("Cookies verification: FAILED - empty cookies list")
                return False

            # Use AmazonHTTPClient (curl_cffi + CookieJar)
            client = AmazonHTTPClient(cookies, country_code)
            try:
                is_valid = client.is_session_valid()
                if is_valid:
                    logger.info(f"Cookies verification: PASSED ({client.cookie_jar.count()} cookies, TLS: chrome131)")
                else:
                    logger.warning("Cookies verification: FAILED - redirected to login")
                return is_valid
            finally:
                client.close()

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
        email: str,
        country_code: str = "eg",
    ) -> Dict[str, Any]:
        """
        Sync products from Amazon Seller Central.
        Delegates to CookieScraper (Playwright DOM extraction).
        """
        from app.services.cookie_scraper import CookieScraper

        scraper = CookieScraper()
        try:
            result = await scraper.sync_products(email)
            return result
        finally:
            await scraper.close()

    @staticmethod
    async def sync_orders(
        email: str,
        days: int = 30,
        country_code: str = "eg",
    ) -> Dict[str, Any]:
        """
        Sync orders from Amazon Seller Central.
        Delegates to CookieScraper (Playwright DOM extraction).
        """
        from app.services.cookie_scraper import CookieScraper

        scraper = CookieScraper()
        try:
            result = await scraper.sync_orders(email, days=days)
            return result
        finally:
            await scraper.close()

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
