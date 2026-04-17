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
from app.config import get_settings, get_env_path


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
    يفتح نافذة Amazon عبر Playwright (Stealth Mode) من الـ Backend مباشرة.
    المستخدم بيدخل في النافذة → الـ Backend بيقرا الـ cookies + CSRF Token + Seller Name تلقائياً.

    Phase 1: Playwright Stealth + Cookie Extraction
    Phase 2: CSRF Token Extraction
    Phase 3: Seller Name Extraction
    """
    logger.info(f"Playwright login initiated for country: {country_code}")

    try:
        # Try Playwright first (new method — async subprocess)
        from app.services.playwright_login import login_amazon_playwright
        result = await login_amazon_playwright(country_code)

        if result.get("success"):
            cookies = result.get("cookies", [])
            raw_seller_name = result.get("seller_name") or "Unknown Seller"
            csrf_token = result.get("csrf_token")

            # =============================================
            # CRITICAL: Detect false login (seller name = login page title)
            # =============================================
            invalid_seller_names = [
                "Amazon Sign In",
                "Amazon Sign-In",
                "Amazon Signin",
                "Sign In",
                "تسجيل الدخول",
                "Login | Amazon",
                "Amazon Login",
            ]
            if raw_seller_name.strip() in invalid_seller_names:
                logger.error(f"FALSE LOGIN DETECTED! seller_name='{raw_seller_name}' is a login page title, not a seller name")
                return {
                    "success": False,
                    "error": "لم يتم تسجيل الدخول بشكل صحيح. يبدو أن الصفحة لا تزال صفحة تسجيل الدخول.",
                    "error_details": f"تم اكتشاف اسم البائع '{raw_seller_name}' وهو عنوان صفحة تسجيل الدخول وليس اسم بائع حقيقي.",
                    "session_id": None,
                    "hint": "يرجى تسجيل الدخول بالكامل في المتصفح وانتظار صفحة Dashboard.",
                }

            seller_name = raw_seller_name

            logger.info(f"Cookies extracted ({len(cookies)} total), seller_name: {seller_name}")
            for c in cookies[:5]:
                logger.info(f"  - {c.get('name')}: {c.get('value', '')[:30]}...")
            if len(cookies) > 5:
                logger.info(f"  ... and {len(cookies) - 5} more")

            if csrf_token:
                logger.info(f"CSRF Token extracted: {csrf_token[:20]}... ({len(csrf_token)} chars)")
            else:
                logger.warning("⚠️ CSRF Token not extracted — listing submission may fail")

            # Save with the actual seller name from Amazon
            from app.services.cookie_auth import CookieAuth
            session = CookieAuth.save_cookies(
                email=seller_name,
                cookies=cookies,
                country_code=country_code,
                seller_name=seller_name,
                csrf_token=csrf_token,
            )

            return {
                "success": True,
                "seller_name": seller_name,
                "country_code": country_code,
                "session_id": session.id,
                "cookie_count": len(cookies),
                "csrf_token_extracted": bool(csrf_token),
                "message": f"تم الاتصال بنجاح! ({seller_name})",
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "فشل تسجيل الدخول"),
                "session_id": None,
            }

    except ImportError:
        # Fallback to old pywebview method
        logger.warning("Playwright not available, falling back to pywebview")
        return await _pywebview_login_fallback(country_code)

    except Exception as e:
        logger.error(f"Playwright login error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"خطأ غير متوقع: {str(e)[:150]}",
        }


async def _pywebview_login_fallback(country_code: str):
    """Fallback to old pywebview method"""
    from app.services.pywebview_login import start_amazon_login

    try:
        result = await start_amazon_login(country_code)

        if result.get("success"):
            cookies = result.get("cookies", [])
            raw_seller_name = result.get("seller_name") or "Unknown Seller"

            # Same false login detection for fallback
            invalid_seller_names = [
                "Amazon Sign In",
                "Amazon Sign-In",
                "Amazon Signin",
                "Sign In",
                "تسجيل الدخول",
                "Login | Amazon",
                "Amazon Login",
            ]
            if raw_seller_name.strip() in invalid_seller_names:
                logger.error(f"FALSE LOGIN (fallback)! seller_name='{raw_seller_name}'")
                return {
                    "success": False,
                    "error": "لم يتم تسجيل الدخول بشكل صحيح. يبدو أن الصفحة لا تزال صفحة تسجيل الدخول.",
                    "session_id": None,
                }

            seller_name = raw_seller_name
            email = seller_name

            from app.services.cookie_auth import CookieAuth
            session = CookieAuth.save_cookies(
                email=email,
                cookies=cookies,
                country_code=country_code,
                seller_name=seller_name,
            )

            return {
                "success": True,
                "seller_name": seller_name,
                "country_code": country_code,
                "session_id": session.id,
                "cookie_count": len(cookies),
                "message": f"تم الاتصال بنجاح! ({seller_name})",
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "فشل تسجيل الدخول"),
            }
    except Exception as e:
        logger.error(f"Pywebview fallback error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


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
    يشيك على:
    1. Session في قاعدة البيانات (Browser login)
    2. SP-API credentials في .env (Direct login) - لو SP_API_ENABLED=True
    """
    # أولاً: شوف لو فيه session في DB
    session = get_active_session()

    if session:
        return SessionStatusResponse(
            is_connected=True,
            auth_method=session.auth_method,
            seller_name=session.seller_name,
            email=session.email,
            country_code=session.country_code,
            is_valid=session.is_valid,
            last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
        )

    # ثانياً: لو مفيش session، شوف لو SP-API credentials موجودة ومفعلة في settings
    try:
        settings = get_settings()
        
        # Check if SP-API is enabled
        sp_enabled = getattr(settings, "SP_API_ENABLED", True)
        
        if not sp_enabled:
            return SessionStatusResponse(is_connected=False)
        
        # Check if we have the essential credentials
        seller_id = getattr(settings, "SP_API_SELLER_ID", None)
        client_id = getattr(settings, "SP_API_CLIENT_ID", None)
        refresh_token = getattr(settings, "SP_API_REFRESH_TOKEN", None)
        country = getattr(settings, "SP_API_COUNTRY", "eg")

        if all([seller_id, client_id, refresh_token]):
            return SessionStatusResponse(
                is_connected=True,
                auth_method="sp_api",
                seller_name=seller_id,
                email=None,
                country_code=country,
                is_valid=True,
                last_verified_at=None,
            )
    except Exception as e:
        logger.warning(f"Failed to check settings credentials: {e}")

    # لا session ولا credentials
    return SessionStatusResponse(is_connected=False)


@router.get("/debug-session")
async def debug_session():
    """
    عرض تفاصيل الجلسة المحفوظة (للتصحيح فقط).
    """
    from app.database import SessionLocal
    from app.models.session import Session
    from app.services.session_store import decrypt_data
    import json

    db = SessionLocal()
    try:
        sessions = db.query(Session).filter(
            Session.auth_method == "browser",
            Session.cookies_json.isnot(None)
        ).order_by(Session.created_at.desc()).all()

        result = []
        for s in sessions:
            # Decrypt and count cookies (don't show values for security)
            try:
                cookies = json.loads(decrypt_data(s.cookies_json))
                cookie_names = [c.get("name", "unknown") for c in cookies]
            except Exception:
                cookie_names = ["decryption_failed"]

            result.append({
                "id": s.id,
                "email": s.email,
                "seller_name": s.seller_name,
                "country_code": s.country_code,
                "is_active": s.is_active,
                "is_valid": s.is_valid,
                "created_at": str(s.created_at),
                "last_verified_at": str(s.last_verified_at) if s.last_verified_at else None,
                "cookie_count": len(cookie_names),
                "cookie_names": cookie_names,
            })

        return {
            "sessions_found": len(result),
            "sessions": result,
        }
    finally:
        db.close()


@router.get("/test-session")
async def test_session():
    """
    اختبار الـ cookies المحفوظة بعمل request حقيقي لـ Amazon.
    """
    from app.database import SessionLocal
    from app.models.session import Session
    from app.services.session_store import decrypt_data
    from app.services.amazon_direct_api import AmazonDirectAPI
    import json
    import httpx

    db = SessionLocal()
    try:
        auth_session = db.query(Session).filter(
            Session.auth_method == "browser",
            Session.cookies_json.isnot(None),
        ).order_by(Session.created_at.desc()).first()

        if not auth_session:
            return {"status": "error", "message": "No session found"}

        cookies = json.loads(decrypt_data(auth_session.cookies_json))
        country_code = auth_session.country_code or "eg"
        base_url = f"https://sellercentral.amazon.{country_code}"

        # Test 1: Try accessing Seller Central home
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies if c.get("name") and c.get("value")])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie_string,
        }

        # Make test request
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(f"{base_url}/home", headers=headers)

        # Check if redirected to login
        is_login_page = "/ap/signin" in str(response.url) or "<!doctype html" in response.text[:200].lower()

        return {
            "session_found": True,
            "session_email": auth_session.email,
            "cookie_count": len(cookies),
            "test_url": f"{base_url}/home",
            "response_status": response.status_code,
            "response_url": str(response.url),
            "is_login_page": is_login_page,
            "is_valid": not is_login_page,
            "cookie_names": [c.get("name") for c in cookies],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@router.post("/verify-session", response_model=SessionStatusResponse)
async def verify_session():
    """
    التحقق من صلاحية الجلسة الحالية.
    يشيك على:
    1. Browser session (cookies)
    2. SP-API credentials (.env)
    """
    from app.services.session_store import get_active_session, update_session_validity
    from app.services.cookie_auth import CookieAuth

    # أولاً: شوف لو فيه browser session
    session = get_active_session()

    if session and session.auth_method == "browser":
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

    # ثانياً: شوف لو فيه SP-API credentials في settings
    try:
        settings = get_settings()
        
        # Check if SP-API is enabled
        sp_enabled = getattr(settings, "SP_API_ENABLED", True)
        
        if not sp_enabled:
            return SessionStatusResponse(is_connected=False)
        
        seller_id = settings.SP_API_SELLER_ID
        client_id = settings.SP_API_CLIENT_ID
        client_secret = settings.SP_API_CLIENT_SECRET
        refresh_token = settings.SP_API_REFRESH_TOKEN
        country = getattr(settings, "SP_API_COUNTRY", "eg")

        has_credentials = all([seller_id, client_id, client_secret, refresh_token])

        if has_credentials:
            # حاول اتصال فعلي بـ Amazon
            from app.services.sp_api_client import SPAPIClient
            
            try:
                client = SPAPIClient(country_code=country)
                access_token = client._get_access_token()
                
                if access_token:
                    logger.info("✅ SP-API verification successful - got access token")
                    return SessionStatusResponse(
                        is_connected=True,
                        auth_method="sp_api",
                        seller_name=seller_id,
                        email=None,
                        country_code=country,
                        is_valid=True,
                        last_verified_at=datetime.now(timezone.utc).isoformat(),
                    )
                else:
                    logger.warning("❌ SP-API verification failed - no access token")
            except Exception as sp_error:
                logger.warning(f"⚠️ SP-API verification error: {str(sp_error)[:100]}")
                # لو فشل الاتصال الفعلي، بس خلّيه connected (البيانات موجودة)
            
            return SessionStatusResponse(
                is_connected=True,
                auth_method="sp_api",
                seller_name=seller_id,
                email=None,
                country_code=country,
                is_valid=True,
                last_verified_at=datetime.now(timezone.utc).isoformat(),
            )
    except Exception as e:
        logger.warning(f"Failed to verify SP-API credentials: {e}")

    # لا session ولا credentials
    return SessionStatusResponse(is_connected=False)


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
    للـ SP-API: يعطّل الاتصال مؤقتاً (SP_API_ENABLED=False)
    """
    try:
        import os
        from dotenv import load_dotenv
        
        # 1. Deactivate browser sessions
        deactivate_all_sessions()
        
        # 2. Disable SP-API credentials temporarily
        env_path = get_env_path()
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        env_vars[key.strip()] = value.strip()
        
        # Disable SP-API
        env_vars['SP_API_ENABLED'] = 'False'
        
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in env_vars.items():
                f.write(f'{key}={value}\n')
        
        from dotenv import load_dotenv
        load_dotenv(str(env_path), override=True)
        logger.info("🚪 Logout: SP-API disabled")
        
        return DisconnectResponse(
            success=True,
            message="تم تسجيل الخروج بنجاح",
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
    DEPRECATED: CookieScraper removed (Amazon ToS violation).
    """
    raise HTTPException(
        status_code=410,
        detail="Cookie-based scraping has been removed. Use SP-API endpoints instead."
    )


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
