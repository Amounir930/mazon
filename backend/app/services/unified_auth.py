"""
Unified Authentication Service
يدعم كل طرق المصادقة: Cookie-based (الأساسية) + SP-API (اختياري)
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger

from app.services.cookie_auth import CookieAuth


# ============================================================
# Auth Result Types
# ============================================================

class UnifiedAuthResult:
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_LOGIN = "needs_login"


# ============================================================
# UnifiedAuthService
# ============================================================

class UnifiedAuthService:
    """
    Unified authentication service supporting:
    1. Cookie-based auth (primary - via PyWebView)
    2. SP-API auth (optional - for advanced users)
    """

    # =========================================================================
    # Cookie-based Authentication (Primary)
    # =========================================================================

    @staticmethod
    def generate_login_url(country_code: str = "eg") -> str:
        """
        Generate Amazon Seller Central login URL.
        
        Args:
            country_code: Country code (eg, sa, ae, uk, us, ...)
            
        Returns:
            Full URL to Amazon Seller Central login page
        """
        return CookieAuth.generate_login_url(country_code)

    @staticmethod
    async def connect_with_cookies(
        email: str,
        cookies: List[Dict[str, Any]],
        country_code: str = "eg",
        seller_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Connect using cookies from PyWebView.
        
        Flow:
        1. Verify cookies are valid
        2. Save encrypted cookies to database
        3. Return success with seller info
        
        Args:
            email: Amazon account email
            cookies: List of cookie dictionaries from browser
            country_code: Marketplace country code
            seller_name: Optional seller name
            
        Returns:
            Dictionary with success status and session info
        """
        try:
            # Step 1: Verify cookies
            is_valid = CookieAuth.verify_cookies(cookies, country_code)
            if not is_valid:
                return {
                    "success": False,
                    "error": "Cookies غير صالحة - يرجى تسجيل الدخول مرة أخرى",
                }

            # Step 2: Save cookies
            session = CookieAuth.save_cookies(
                email=email,
                cookies=cookies,
                country_code=country_code,
                seller_name=seller_name,
            )

            logger.info(f"Cookie connection successful: {email}")
            return {
                "success": True,
                "seller_name": seller_name or email,
                "country_code": country_code,
                "session_id": session.id,
            }

        except Exception as e:
            logger.error(f"Cookie connection error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"خطأ غير متوقع: {str(e)[:150]}",
            }

    @staticmethod
    def get_active_session(email: str) -> Optional[Dict[str, Any]]:
        """
        Get active session info for an email.
        
        Args:
            email: Amazon account email
            
        Returns:
            Dictionary with session info or None
        """
        cookies = CookieAuth.get_active_cookies(email)
        if not cookies:
            return None

        return {
            "email": email,
            "has_cookies": True,
            "cookie_count": len(cookies),
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
        return CookieAuth.disconnect(email)

    # =========================================================================
    # Data Sync Operations (Cookie-based)
    # =========================================================================

    @staticmethod
    async def sync_products(email: str) -> Dict[str, Any]:
        """
        Sync products using active cookies.
        
        Args:
            email: Amazon account email
            
        Returns:
            Dictionary with products list and metadata
        """
        cookies = CookieAuth.get_active_cookies(email)
        if not cookies:
            return {
                "success": False,
                "error": "No active session - please login first",
                "products": [],
            }

        # Get country code from session (need to query DB)
        from app.database import SessionLocal
        from app.models.session import Session
        
        db = SessionLocal()
        try:
            session = db.query(Session).filter(
                Session.auth_method == "browser",
                Session.email == email,
                Session.is_active == True,
            ).first()
            
            country_code = session.country_code if session else "eg"
        finally:
            db.close()

        return await CookieAuth.sync_products(cookies, country_code)

    @staticmethod
    async def sync_orders(email: str) -> Dict[str, Any]:
        """
        Sync orders using active cookies.
        
        Args:
            email: Amazon account email
            
        Returns:
            Dictionary with orders list and metadata
        """
        cookies = CookieAuth.get_active_cookies(email)
        if not cookies:
            return {
                "success": False,
                "error": "No active session - please login first",
                "orders": [],
            }

        # Get country code from session
        from app.database import SessionLocal
        from app.models.session import Session
        
        db = SessionLocal()
        try:
            session = db.query(Session).filter(
                Session.auth_method == "browser",
                Session.email == email,
                Session.is_active == True,
            ).first()
            
            country_code = session.country_code if session else "eg"
        finally:
            db.close()

        return await CookieAuth.sync_orders(cookies, country_code)

    # =========================================================================
    # Supported Countries
    # =========================================================================

    @staticmethod
    def get_supported_countries() -> Dict[str, str]:
        """
        Get list of supported Amazon marketplaces.
        
        Returns:
            Dictionary mapping country codes to display names
        """
        from app.services.cookie_auth import SELLER_CENTRAL_BASE
        
        country_names = {
            "eg": "Egypt",
            "sa": "Saudi Arabia",
            "ae": "UAE",
            "uk": "United Kingdom",
            "us": "United States",
            "de": "Germany",
            "fr": "France",
            "it": "Italy",
            "es": "Spain",
        }
        
        return {
            code: country_names.get(code, code.upper())
            for code in SELLER_CENTRAL_BASE.keys()
        }
