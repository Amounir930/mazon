"""
Authentication API Routes - PyWebView Login + Cookie-based
بيدعم تسجيل الدخول عبر:
1. PyWebView Login (الطريقة الأساسية)
2. Cookie Connect (اختياري)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.services.unified_auth import UnifiedAuthService
from app.services.pywebview_login import start_amazon_login, get_login_status
from app.services.session_store import (
    get_active_session,
    deactivate_session,
    deactivate_all_sessions,
)
from loguru import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# Request/Response Schemas
# ============================================================

class LoginUrlRequest(BaseModel):
    country_code: str = Field(default="eg", description="Marketplace country code")


class LoginUrlResponse(BaseModel):
    success: bool
    login_url: str
    country_code: str


class CookieConnectRequest(BaseModel):
    email: str = Field(..., description="Amazon account email")
    cookies: List[Dict[str, Any]] = Field(..., description="Browser cookies from PyWebView")
    country_code: str = Field(default="eg", description="Marketplace country code")
    seller_name: Optional[str] = Field(default=None, description="Seller display name")


class CookieConnectResponse(BaseModel):
    success: bool
    seller_name: Optional[str] = None
    country_code: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


class SessionStatusResponse(BaseModel):
    is_connected: bool
    auth_method: Optional[str] = None
    seller_name: Optional[str] = None
    email: Optional[str] = None
    country_code: Optional[str] = None
    is_valid: bool = False
    last_verified_at: Optional[str] = None


class DisconnectRequest(BaseModel):
    email: str = Field(..., description="Amazon account email to disconnect")


class DisconnectResponse(BaseModel):
    success: bool
    message: str


class PyWebViewLoginRequest(BaseModel):
    email: str = Field(..., description="Amazon account email")
    country_code: str = Field(default="eg", description="Marketplace country code")


class PyWebViewLoginResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ============================================================
# Routes
# ============================================================

@router.post("/pywebview-login")
async def pywebview_login(country_code: str = "eg"):
    """
    يفتح نافذة Amazon عبر PyWebView من الـ Backend مباشرة.
    المستخدم بيدخل في النافذة → الـ Backend بيقرا الـ cookies تلقائياً.
    
    ده بيشتغل 100% لأن الـ Backend هو اللي بيفتح النافذة وبيقرا الـ cookies.
    """
    logger.info(f"PyWebView login initiated for country: {country_code}")
    
    try:
        result = await start_amazon_login(country_code)
        
        if result.get("success"):
            # Save cookies to database
            cookies = result.get("cookies", [])
            email = "unknown"  # نحتاج نعرفه من الـ cookies أو نطلبه من الـ Frontend
            
            # Extract email from cookies if possible
            for c in cookies:
                if c.get("name") in ["ubid-main", "session-id"]:
                    # We have valid Amazon cookies
                    email = f"amazon_{country_code}"
                    break
            
            # For now, save with a generic email - user can specify later
            from app.services.cookie_auth import CookieAuth
            session = CookieAuth.save_cookies(
                email=email,
                cookies=cookies,
                country_code=country_code,
                seller_name=email,
            )
            
            return {
                "success": True,
                "seller_name": email,
                "country_code": country_code,
                "session_id": session.id,
                "cookie_count": len(cookies),
                "message": "تم الاتصال بنجاح!",
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "فشل تسجيل الدخول"),
                "session_id": result.get("session_id"),
            }
            
    except Exception as e:
        logger.error(f"PyWebView login error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"خطأ غير متوقع: {str(e)[:150]}",
        }


@router.get("/pywebview-status/{session_id}")
async def pywebview_login_status(session_id: str):
    """
    يتتبع حالة تسجيل الدخول عبر PyWebView.
    """
    status = await get_login_status(session_id)
    return status


@router.get("/login-url", response_model=LoginUrlResponse)
async def get_login_url(country_code: str = "eg"):
    """
    Get Amazon Seller Central login URL for a specific country.
    الـ Frontend هيستخدم الرابط ده لفتح PyWebView.
    """
    try:
        login_url = UnifiedAuthService.generate_login_url(country_code)
        
        return LoginUrlResponse(
            success=True,
            login_url=login_url,
            country_code=country_code,
        )
    except Exception as e:
        logger.error(f"Failed to generate login URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect", response_model=CookieConnectResponse)
async def connect_with_cookies(req: CookieConnectRequest):
    """
    Connect using cookies from PyWebView.
    الـ Frontend بيبعت الـ cookies بعد ما المستخدم يسجل دخول.
    """
    logger.info(f"Cookie connection request for {req.email} ({req.country_code})")
    logger.info(f"Cookies received: {len(req.cookies)} cookies")
    
    # Log cookie names to see what we got
    if req.cookies:
        cookie_names = [c.get("name", "unknown") for c in req.cookies[:10]]
        logger.info(f"Cookie names: {cookie_names}")
    else:
        logger.warning("⚠️ NO COOKIES RECEIVED from frontend!")
        logger.warning("This means the frontend couldn't read cookies from the popup window.")
        logger.warning("Root cause: Cross-origin policy prevents JS from reading Amazon cookies.")

    try:
        result = await UnifiedAuthService.connect_with_cookies(
            email=req.email,
            cookies=req.cookies,
            country_code=req.country_code,
            seller_name=req.seller_name,
        )

        if result.get("success"):
            return CookieConnectResponse(
                success=True,
                seller_name=result.get("seller_name"),
                country_code=result.get("country_code"),
                session_id=result.get("session_id"),
                message="تم الاتصال بنجاح",
            )
        else:
            return CookieConnectResponse(
                success=False,
                error=result.get("error", "فشل تسجيل الدخول"),
            )

    except Exception as e:
        logger.error(f"Cookie connection error: {e}", exc_info=True)
        return CookieConnectResponse(
            success=False,
            error=f"خطأ غير متوقع: {str(e)[:150]}",
        )


@router.get("/status", response_model=SessionStatusResponse)
async def get_session_status():
    """
    حالة الجلسة الحالية.
    """
    session = get_active_session()

    if not session:
        return SessionStatusResponse(is_connected=False)

    return SessionStatusResponse(
        is_connected=True,
        auth_method=session.auth_method,
        seller_name=session.seller_name,
        email=session.email,
        country_code=session.country_code,
        is_valid=session.is_valid,
        last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
    )


@router.post("/verify-session", response_model=SessionStatusResponse)
async def verify_session():
    """
    التحقق من صلاحية الجلسة الحالية.
    """
    from app.services.session_store import get_active_session, update_session_validity
    from app.services.cookie_auth import CookieAuth
    
    session = get_active_session()

    if not session:
        return SessionStatusResponse(is_connected=False)

    if session.auth_method == "browser":
        # Get decrypted cookies
        from app.services.session_store import decrypt_data, get_browser_cookies
        import json
        
        cookies = get_browser_cookies(session.id)
        if not cookies:
            update_session_validity(session.id, False)
            return SessionStatusResponse(
                is_connected=True,
                auth_method="browser",
                seller_name=session.seller_name,
                email=session.email,
                country_code=session.country_code,
                is_valid=False,
                last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
            )

        # Verify cookies are still valid
        is_valid = CookieAuth.verify_cookies(cookies, session.country_code or "eg")
        update_session_validity(session.id, is_valid)

        return SessionStatusResponse(
            is_connected=True,
            auth_method="browser",
            seller_name=session.seller_name,
            email=session.email,
            country_code=session.country_code,
            is_valid=is_valid,
            last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
        )

    # SP-API - basic check
    return SessionStatusResponse(
        is_connected=True,
        auth_method="sp_api",
        marketplace_id=session.marketplace_id,
        is_valid=session.is_valid,
        last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
    )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect(req: DisconnectRequest):
    """
    تسجيل خروج لحساب معين.
    """
    try:
        success = UnifiedAuthService.disconnect(email=req.email)
        
        if success:
            return DisconnectResponse(
                success=True,
                message="تم تسجيل الخروج بنجاح",
            )
        else:
            return DisconnectResponse(
                success=False,
                message="لم يتم العثور على جلسة نشطة",
            )
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", response_model=DisconnectResponse)
async def logout():
    """
    تسجيل خروج من كل الحسابات.
    """
    try:
        deactivate_all_sessions()
        return DisconnectResponse(
            success=True,
            message="تم تسجيل الخروج من جميع الحسابات",
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-countries")
async def get_supported_countries():
    """
    قائمة الدول المدعومة (Amazon Marketplaces).
    """
    return {
        "countries": UnifiedAuthService.get_supported_countries()
    }


@router.get("/sync/products")
async def sync_products(email: str):
    """
    Sync المنتجات من Amazon باستخدام cookies.
    """
    try:
        from app.services.cookie_scraper import CookieScraper
        
        scraper = CookieScraper()
        result = await scraper.sync_products(email)
        scraper.close()
        
        return result
    except Exception as e:
        logger.error(f"Failed to sync products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/orders")
async def sync_orders(email: str):
    """
    Sync الطلبات من Amazon باستخدام cookies.
    """
    try:
        result = await UnifiedAuthService.sync_orders(email=email)
        return result
    except Exception as e:
        logger.error(f"Failed to sync orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
