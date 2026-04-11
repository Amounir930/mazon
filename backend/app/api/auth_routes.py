"""
Authentication API Routes
Handles browser login, OTP submission, session management, and SP-API login.
Uses UnifiedAuthService for all auth methods.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from app.services.unified_auth import UnifiedAuthService
from app.services.browser_auth import BrowserAuth
from app.services.session_store import (
    save_browser_session,
    save_spapi_session,
    get_active_session,
    get_browser_cookies,
    deactivate_session,
    deactivate_all_sessions,
    update_session_validity,
    save_temp_session as _save_temp,
    get_temp_session as _get_temp,
    remove_temp_session as _remove_temp,
)
from loguru import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# Request/Response Schemas
# ============================================================

class BrowserLoginRequest(BaseModel):
    email: str = Field(..., description="Amazon account email")
    password: str = Field(..., description="Amazon account password")
    country_code: str = Field(default="us", description="Marketplace country code (us, uk, ae, sa, eg, ...)")


class BrowserLoginResponse(BaseModel):
    success: bool
    needs_otp: bool = False
    seller_name: Optional[str] = None
    country_code: Optional[str] = None
    session_id: Optional[str] = None  # For OTP flow
    error: Optional[str] = None
    message: Optional[str] = None


class OTPSubmitRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from browser-login response")
    otp: str = Field(..., description="OTP / verification code")


class SPAPILoginRequest(BaseModel):
    lwa_client_id: str = Field(..., description="LWA Client ID")
    lwa_client_secret: str = Field(..., description="LWA Client Secret")
    refresh_token: str = Field(..., description="LWA Refresh Token")
    marketplace_id: str = Field(default="ARBP9OOSHTCHU", description="Amazon Marketplace ID")
    aws_access_key: Optional[str] = Field(default="", description="AWS Access Key (optional)")
    aws_secret_key: Optional[str] = Field(default="", description="AWS Secret Key (optional)")


class SessionStatusResponse(BaseModel):
    is_connected: bool
    auth_method: Optional[str] = None  # 'browser' or 'sp_api'
    seller_name: Optional[str] = None
    email: Optional[str] = None
    country_code: Optional[str] = None
    marketplace_id: Optional[str] = None
    is_valid: bool = False
    last_verified_at: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool
    message: str


# ============================================================
# Active sessions store for OTP flow
# ============================================================

_active_login_sessions: Dict[str, Any] = {}


# ============================================================
# Routes
# ============================================================

@router.post("/browser-login", response_model=BrowserLoginResponse)
async def browser_login(req: BrowserLoginRequest):
    """
    Browser auto login - opens Playwright, navigates to Amazon Seller Central,
    fills credentials automatically, handles OTP if needed.
    """
    try:
        auth = BrowserAuth(
            email=req.email,
            password=req.password,
            country_code=req.country_code,
        )

        result = await auth.login()

        # OTP مطلوب
        if result.get("needs_otp"):
            session_id = _save_temp(req.email, auth)
            _active_login_sessions[session_id] = auth
            return BrowserLoginResponse(
                success=False,
                needs_otp=True,
                session_id=session_id,
                message="OTP مطلوب - يرجى إدخال رمز التحقق",
            )

        # نجاح
        if result.get("success"):
            session = save_browser_session(
                email=req.email,
                country_code=req.country_code,
                cookies=result["cookies"],
                seller_name=result.get("seller_name", req.email),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            return BrowserLoginResponse(
                success=True,
                seller_name=result.get("seller_name"),
                country_code=req.country_code,
            )

        # فشل
        return BrowserLoginResponse(
            success=False,
            error=result.get("error", "فشل تسجيل الدخول"),
        )

    except Exception as e:
        # Never raise 500 - always return error in response body
        logger.error(f"Browser login error: {e}")
        return BrowserLoginResponse(
            success=False,
            error=f"خطأ في المتصفح: {str(e)[:100]}",
        )


@router.post("/submit-otp", response_model=BrowserLoginResponse)
async def submit_otp(req: OTPSubmitRequest):
    """
    إرسال OTP لتكملة تسجيل الدخول.
    """
    auth = _active_login_sessions.get(req.session_id)
    if not auth:
        raise HTTPException(status_code=404, detail="Session expired or not found")

    try:
        result = await auth.submit_otp(req.otp)

        if result.get("success"):
            save_browser_session(
                email=auth.email,
                country_code=auth.country_code,
                cookies=result["cookies"],
                seller_name=result.get("seller_name", auth.email),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            _active_login_sessions.pop(req.session_id, None)

            return BrowserLoginResponse(
                success=True,
                seller_name=result.get("seller_name"),
                country_code=auth.country_code,
            )

        return BrowserLoginResponse(
            success=False,
            error=result.get("error", "OTP غير صحيح"),
        )

    except Exception as e:
        logger.error(f"OTP submission error: {e}")
        _active_login_sessions.pop(req.session_id, None)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spapi-login", response_model=BrowserLoginResponse)
async def spapi_login(req: SPAPILoginRequest):
    """
    تسجيل دخول عبر SP-API credentials (الطريقة الرسمية).
    يتحقق من البيانات قبل الحفظ.
    """
    try:
        result = await UnifiedAuthService.spapi_login(
            lwa_client_id=req.lwa_client_id,
            lwa_client_secret=req.lwa_client_secret,
            refresh_token=req.refresh_token,
            marketplace_id=req.marketplace_id,
            aws_access_key=req.aws_access_key or "",
            aws_secret_key=req.aws_secret_key or "",
        )

        # Always return 200 with success/error in body
        if result.get("success"):
            return BrowserLoginResponse(
                success=True,
                seller_name=result.get("seller_name"),
                message="تم الاتصال بنجاح",
            )
        else:
            return BrowserLoginResponse(
                success=False,
                error=result.get("error", "فشل التحقق من البيانات"),
            )

    except Exception as e:
        # Never raise 500 - always return error in response body
        logger.error(f"SP-API login error: {e}")
        return BrowserLoginResponse(
            success=False,
            error=f"خطأ في الخادم: {str(e)[:100]}",
        )


@router.get("/session", response_model=SessionStatusResponse)
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
        marketplace_id=session.marketplace_id,
        is_valid=session.is_valid,
        last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
    )


@router.post("/verify-session", response_model=SessionStatusResponse)
async def verify_session():
    """
    التحقق من صلاحية الجلسة الحالية.
    للـ browser: يتأكد إن الكوكيز لسه صالحة.
    """
    session = get_active_session()

    if not session:
        return SessionStatusResponse(is_connected=False)

    if session.auth_method == "browser":
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

        is_valid = await verify_browser_session(cookies, session.country_code or "us")
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


@router.post("/logout", response_model=LogoutResponse)
async def logout(session_id: Optional[str] = None):
    """
    تسجيل الخروج.
    لو session_id محدد: يسوي deactivate له.
    لو بدون: يسوي logout للكل.
    """
    if session_id:
        deactivate_session(session_id)
        return LogoutResponse(success=True, message="تم تسجيل الخروج")
    else:
        deactivate_all_sessions()
        return LogoutResponse(success=True, message="تم تسجيل الخروج من جميع الحسابات")


@router.get("/supported-countries")
async def get_supported_countries():
    """
    قائمة الدول المدعومة (Amazon Marketplaces الحقيقية).
    """
    return {
        "countries": UnifiedAuthService.get_supported_countries()
    }


@router.post("/browser-manual-login")
async def browser_manual_login():
    """
    فتح متصفح Amazon مصر الحقيقي للتسجيل اليدوي.
    المستخدم يدخل بياناته بنفسه.
    """
    try:
        result = await UnifiedAuthService.browser_manual_login(
            timeout_seconds=180,
        )

        if result.get("success"):
            session = save_browser_session(
                email="manual_eg",
                country_code="eg",
                cookies=result.get("cookies", []),
                seller_name=result.get("seller_name", "Manual User"),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            return BrowserLoginResponse(
                success=True,
                seller_name=result.get("seller_name"),
                country_code="eg",
            )

        return BrowserLoginResponse(
            success=False,
            error=result.get("error", "فشل تسجيل الدخول اليدوي"),
        )

    except Exception as e:
        logger.error(f"Manual browser login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
