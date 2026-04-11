"""
SP-API Authentication Service
Uses python-amazon-sp-api library for real Amazon SP-API authentication.
"""
import asyncio
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from loguru import logger


def _sp_api_call_wrapper(
    lwa_client_id: str,
    lwa_client_secret: str,
    refresh_token: str,
    marketplace_id: str,
    aws_access_key: str = "",
    aws_secret_key: str = "",
    aws_region: str = "eu-west-1",
) -> Dict[str, Any]:
    """
    SP-API verification against Amazon.
    Uses python-amazon-sp-api library.
    """
    if not lwa_client_id or not lwa_client_secret or not refresh_token:
        return {"success": False, "error": "يرجى ملء جميع بيانات SP-API"}

    try:
        from sp_api.api import Sellers
        from sp_api.base import SellingApiException, Marketplaces, Credentials

        # Map marketplace IDs
        marketplace_map = {
            "ARBP9OOSHTCHU": Marketplaces.EG,  # Egypt
            "A1F83G8C2ARO7P": Marketplaces.GB,  # UK
            "ATVPDKIKX0DER": Marketplaces.US,   # US
            "A1PA6795UKMFR9": Marketplaces.DE,   # Germany
            "A13V1IB3VIYZZH": Marketplaces.FR,   # France
            "A1RKKUPIHCS9HS": Marketplaces.ES,   # Spain
            "APJ6JRA9NG5V4": Marketplaces.IT,    # Italy
            "A1VC38T7YXB528": Marketplaces.JP,   # Japan
            "A39IBJ37TRP1C6": Marketplaces.AU,   # Australia
            "A2EUQ1WTGCTBG2": Marketplaces.CA,   # Canada
            "A1AM78C64UM0Y8": Marketplaces.MX,   # Mexico
            "AE08WJ6YKNBMC": Marketplaces.SA,    # Saudi Arabia
            "A2VIGQ35RCS4UG": Marketplaces.AE,   # UAE
        }
        marketplace = marketplace_map.get(marketplace_id, Marketplaces.EG)

        # Build credentials
        creds_kwargs = {
            "refresh_token": refresh_token,
            "lwa_app_id": lwa_client_id,
            "lwa_client_secret": lwa_client_secret,
        }

        # Add AWS credentials if provided
        if aws_access_key and aws_secret_key:
            creds_kwargs.update({
                "aws_access_key": aws_access_key,
                "aws_secret_key": aws_secret_key,
            })

        # Create Sellers API instance
        sellers_api = Sellers(
            credentials=creds_kwargs,
            marketplace=marketplace,
        )

        # Call SP-API to verify
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
            "payload": payload,
        }

    except SellingApiException as e:
        error_str = str(e).lower()
        logger.error(f"SP-API verification failed: {e}")

        if "401" in error_str or "unauthorized" in error_str:
            return {"success": False, "error": "بيانات غير صحيحة - Amazon رفض الدخول"}
        elif "403" in error_str or "forbidden" in error_str:
            return {"success": False, "error": "لا توجد صلاحيات - تأكد من IAM Role"}
        elif "400" in error_str or "bad request" in error_str:
            return {"success": False, "error": "بيانات غير صالحة"}
        else:
            return {"success": False, "error": f"خطأ من Amazon: {str(e)[:200]}"}

    except ImportError as e:
        logger.error(f"SP-API library not installed: {e}")
        return {
            "success": False,
            "error": "مكتبة SP-API غير مثبتة",
            "details": "شغل: pip install python-amazon-sp-api",
        }

    except Exception as e:
        logger.error(f"SP-API verification error: {e}", exc_info=True)
        return {"success": False, "error": f"خطأ غير متوقع: {str(e)[:200]}"}


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
        aws_access_key: str = "",
        aws_secret_key: str = "",
        aws_region: str = "eu-west-1",
    ) -> Dict[str, Any]:
        """
        Verify SP-API credentials against REAL Amazon SP-API.
        """
        if not lwa_client_id or not lwa_client_secret or not refresh_token:
            return {
                "success": False,
                "error": "يرجى ملء جميع بيانات SP-API",
                "details": "Client ID و Secret و Refresh Token مطلوبة",
            }

        try:
            result = _sp_api_call_wrapper(
                lwa_client_id=lwa_client_id,
                lwa_client_secret=lwa_client_secret,
                refresh_token=refresh_token,
                marketplace_id=marketplace_id,
                aws_access_key=aws_access_key,
                aws_secret_key=aws_secret_key,
                aws_region=aws_region,
            )
            return result

        except asyncio.TimeoutError:
            logger.error("SP-API verification timed out (15s)")
            return {
                "success": False,
                "error": "انتهت مهلة الاتصال بـ Amazon - تحقق من الإنترنت وحاول مرة أخرى",
            }
        except Exception as e:
            logger.error(f"SP-API verification error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"خطأ غير متوقع: {str(e)[:150]}",
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
        try:
            # Step 1: REAL verification
            result = await UnifiedAuthService.verify_spapi_credentials(
                lwa_client_id=lwa_client_id,
                lwa_client_secret=lwa_client_secret,
                refresh_token=refresh_token,
                marketplace_id=marketplace_id,
                aws_access_key=aws_access_key,
                aws_secret_key=aws_secret_key,
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
                    "error": "فشل حفظ الجلسة - حاول مرة أخرى",
                }

        except Exception as e:
            logger.error(f"SP-API login error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"خطأ غير متوقع: {str(e)[:100]}",
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
        Uses BrowserWorker (dedicated event loop thread) to avoid Windows asyncio issues.
        """
        from app.services.browser_worker import browser_login as worker_browser_login

        result = await worker_browser_login(
            email=email,
            password=password,
            country_code=country_code,
            otp=otp or None,
        )
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
        from app.services.browser_worker import SELLER_CENTRAL_BASE
        return SELLER_CENTRAL_BASE
