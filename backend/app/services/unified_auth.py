"""
Unified Authentication Service
Real Amazon SP-API authentication only.
No mock/fake data - all operations verified against Amazon.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from loguru import logger


class UnifiedAuthResult:
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_OTP = "needs_otp"


class UnifiedAuthService:
    """Real Amazon SP-API authentication"""

    # =========================================================================
    # SP-API Authentication (REAL - Verified against Amazon)
    # =========================================================================

    @staticmethod
    async def verify_spapi_credentials(
        lwa_client_id: str,
        lwa_client_secret: str,
        refresh_token: str,
        marketplace_id: str,
    ) -> Dict[str, Any]:
        """
        Verify SP-API credentials against REAL Amazon SP-API.
        Returns proper error messages if credentials are empty or invalid.
        """
        # Validate inputs first
        if not lwa_client_id or not lwa_client_secret or not refresh_token:
            return {
                "success": False,
                "error": "يرجى ملء جميع بيانات SP-API",
                "details": "Client ID و Secret و Refresh Token مطلوبة",
            }

        try:
            from sp_api.api import Sellers
            from sp_api.base import SellingApiException, Marketplaces

            marketplace_map = {
                "ARBP9OOSHTCHU": Marketplaces.EG,
            }
            marketplace = marketplace_map.get(marketplace_id, Marketplaces.EG)

            creds = {
                "refresh_token": refresh_token,
                "lwa_app_id": lwa_client_id,
                "lwa_client_secret": lwa_client_secret,
            }

            sellers_api = Sellers(
                credentials=creds,
                marketplace=marketplace,
            )
            response = sellers_api.get_account()
            payload = response.payload

            seller_name = payload.get("businessName", "Unknown")
            account_status = payload.get("status", "UNKNOWN")

            logger.info(f"SP-API verified: {seller_name} ({account_status})")

            return {
                "success": True,
                "seller_name": seller_name,
                "marketplace_id": marketplace_id,
                "account_status": account_status,
                "account_type": payload.get("accountType", ""),
            }

        except SellingApiException as e:
            error_str = str(e).lower()
            logger.error(f"SP-API verification failed: {e}")

            if "401" in error_str or "unauthorized" in error_str:
                return {
                    "success": False,
                    "error": "بيانات غير صحيحة - Amazon رفض الدخول",
                    "details": "تأكد من Client ID و Secret و Refresh Token",
                }
            elif "403" in error_str or "forbidden" in error_str:
                return {
                    "success": False,
                    "error": "لا توجد صلاحيات - تأكد من IAM Role",
                    "details": "تأكد من ربط الحساب بـ IAM Role صحيح",
                }
            elif "400" in error_str or "bad request" in error_str:
                return {
                    "success": False,
                    "error": "بيانات غير صالحة",
                    "details": str(e),
                }
            else:
                return {
                    "success": False,
                    "error": f"خطأ من Amazon: {str(e)[:200]}",
                }

        except ImportError:
            logger.error("python-amazon-sp-api not installed")
            return {
                "success": False,
                "error": "مكتبة SP-API غير مثبتة",
                "details": "شغل: pip install python-amazon-sp-api",
            }

        except Exception as e:
            logger.error(f"SP-API verification error: {e}")
            return {
                "success": False,
                "error": f"خطأ غير متوقع: {str(e)[:200]}",
            }

    @staticmethod
    async def spapi_login(
        lwa_client_id: str,
        lwa_client_secret: str,
        refresh_token: str,
        marketplace_id: str,
        aws_access_key: str = "",
        aws_secret_key: str = "",
    ) -> Dict[str, Any]:
        """
        Full SP-API login flow:
        1. Verify credentials against REAL Amazon
        2. If valid, save encrypted session
        3. Return result
        """
        # Step 1: REAL verification
        result = await UnifiedAuthService.verify_spapi_credentials(
            lwa_client_id=lwa_client_id,
            lwa_client_secret=lwa_client_secret,
            refresh_token=refresh_token,
            marketplace_id=marketplace_id,
        )

        if not result.get("success"):
            return result

        # Step 2: Save verified session
        from app.services.session_store import save_spapi_session

        try:
            session = save_spapi_session(
                lwa_client_id=lwa_client_id,
                lwa_client_secret=lwa_client_secret,
                refresh_token=refresh_token,
                marketplace_id=marketplace_id,
                aws_access_key=aws_access_key,
                aws_secret_key=aws_secret_key,
                seller_name=result.get("seller_name", ""),
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            )

            logger.info(f"SP-API session saved: {session.id} for {result.get('seller_name')}")
            return {
                "success": True,
                "seller_name": result.get("seller_name"),
                "marketplace_id": marketplace_id,
                "session_id": session.id,
            }
        except Exception as e:
            logger.error(f"Failed to save SP-API session: {e}")
            return {
                "success": False,
                "error": "فشل حفظ الجلسة",
            }

    # =========================================================================
    # Browser Auto Authentication (REAL Amazon Seller Central)
    # =========================================================================

    @staticmethod
    async def browser_auto_login(
        email: str,
        password: str,
        country_code: str,
        otp: str = "",
    ) -> Dict[str, Any]:
        """
        Browser auto login to REAL Amazon Seller Central.
        Uses Playwright to navigate and login.
        """
        from app.services.browser_auth import BrowserAuth

        auth = BrowserAuth(
            email=email,
            password=password,
            country_code=country_code,
            otp=otp,
        )

        result = await auth.login(otp=otp)
        return result

    # =========================================================================
    # Browser Manual Authentication (REAL Amazon)
    # =========================================================================

    @staticmethod
    async def browser_manual_login(
        timeout_seconds: int = 180,
    ) -> Dict[str, Any]:
        """
        Opens REAL Amazon Seller Central (Egypt) for manual login.
        User enters credentials themselves.
        """
        from app.services.browser_manual_auth import BrowserManualAuth

        auth = BrowserManualAuth(
            timeout_seconds=timeout_seconds,
        )

        result = await auth.login()
        return result

    # =========================================================================
    # Supported Countries (Real Amazon Marketplaces)
    # =========================================================================

    @staticmethod
    def get_supported_countries() -> Dict[str, str]:
        """Get list of real Amazon marketplaces"""
        from app.services.browser_auth import SELLER_CENTRAL_BASE
        return SELLER_CENTRAL_BASE
