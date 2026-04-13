"""
Amazon Session Manager — The Central Cookie Hub
================================================

Unified interface for all Amazon cookie-based operations.

This manager:
1. Retrieves cookies from the database
2. Creates curl_cffi HTTP clients with TLS impersonation
3. Creates Playwright contexts for DOM extraction
4. Validates sessions (fast curl_cffi check BEFORE opening browser)
5. Handles session expiration and re-auth flows

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                  AmazonSessionManager                       │
│                                                              │
│  ┌──────────────────┐     ┌──────────────────────┐          │
│  │  Database (DB)   │     │  curl_cffi Client    │          │
│  │  (encrypted)     │────►│  (TLS: chrome131)    │          │
│  │                  │     │  + CookieJar          │          │
│  └──────────────────┘     │  (API requests)       │          │
│                           └──────────────────────┘          │
│                                    │                         │
│                                    ▼ (if DOM needed)         │
│                           ┌──────────────────────┐          │
│                           │  Playwright Context  │          │
│                           │  (DOM extraction)    │          │
│                           └──────────────────────┘          │
└─────────────────────────────────────────────────────────────┘

IMPORTANT:
- curl_cffi is for API requests (listing creation, validation)
- Playwright is for DOM scraping ONLY (products, orders, inventory)
- Login MUST always use Playwright (or PyWebView)
"""
import json
from typing import Optional, List, Dict, Any, Tuple
from loguru import logger

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data
from app.services.amazon_http_client import AmazonHTTPClient, AmazonCookieJar


class AmazonSessionManager:
    """
    Central manager for Amazon session handling.

    Provides:
    - Cookie retrieval from DB
    - curl_cffi HTTP client creation
    - Session validation (fast, no browser)
    - Session info (cookies count, expiry, country)
    """

    @staticmethod
    def get_cookies_for_email(email: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Get cookies and country for an email from the database.

        Returns:
            (cookies, country) or (None, None) if no session
        """
        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.email == email,
                AuthSession.is_active == True,
                AuthSession.is_valid == True,
            ).first()

            if not session or not session.cookies_json:
                logger.warning(f"No active session for {email}")
                return None, None

            cookies = json.loads(decrypt_data(session.cookies_json))
            country = session.country_code or "eg"

            logger.info(f"Session retrieved for {email} ({country.upper()}, {len(cookies)} cookies)")
            return cookies, country

        except Exception as e:
            logger.error(f"Session retrieval failed for {email}: {e}")
            return None, None
        finally:
            db.close()

    @staticmethod
    def get_active_cookies() -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Get cookies from ANY active session (not email-specific).

        Returns:
            (cookies, country) or (None, None)
        """
        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.is_active == True,
                AuthSession.is_valid == True,
            ).first()

            if not session or not session.cookies_json:
                return None, None

            cookies = json.loads(decrypt_data(session.cookies_json))
            country = session.country_code or "eg"
            email = session.email

            logger.info(f"Active session: {email} ({country.upper()}, {len(cookies)} cookies)")
            return cookies, country

        except Exception as e:
            logger.error(f"Active session retrieval failed: {e}")
            return None, None
        finally:
            db.close()

    @staticmethod
    def create_http_client(email: str) -> Optional[AmazonHTTPClient]:
        """
        Create an AmazonHTTPClient (curl_cffi + CookieJar) for an email.

        Returns:
            AmazonHTTPClient ready for API requests, or None if no session
        """
        cookies, country = AmazonSessionManager.get_cookies_for_email(email)
        if not cookies:
            logger.warning(f"Cannot create HTTP client — no session for {email}")
            return None

        client = AmazonHTTPClient(cookies, country)
        logger.info(f"HTTP client created for {email} ({country.upper()}, TLS: chrome131)")
        return client

    @staticmethod
    def create_http_client_from_active() -> Optional[AmazonHTTPClient]:
        """
        Create an AmazonHTTPClient from ANY active session.

        Returns:
            AmazonHTTPClient or None
        """
        cookies, country = AmazonSessionManager.get_active_cookies()
        if not cookies:
            logger.warning("Cannot create HTTP client — no active session")
            return None

        client = AmazonHTTPClient(cookies, country)
        logger.info(f"HTTP client created from active session ({country.upper()}, {client.cookie_jar.count()} cookies)")
        return client

    @staticmethod
    async def validate_session(email: str) -> bool:
        """
        Fast session validation using curl_cffi (no browser).

        Returns:
            True if session is valid, False otherwise
        """
        cookies, country = AmazonSessionManager.get_cookies_for_email(email)
        if not cookies:
            return False

        try:
            client = AmazonHTTPClient(cookies, country)
            try:
                valid = client.is_session_valid()
                if valid:
                    logger.info(f"✅ Session valid for {email} ({client.cookie_jar.count()} cookies)")
                else:
                    logger.warning(f"⚠️ Session expired for {email}")
                    # Mark session as invalid in DB
                    AmazonSessionManager.invalidate_session(email)
                return valid
            finally:
                client.close()
        except Exception as e:
            logger.error(f"Session validation error for {email}: {e}")
            return False

    @staticmethod
    def invalidate_session(email: str) -> bool:
        """
        Mark a session as invalid in the database.

        Returns:
            True if session was found and invalidated
        """
        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.email == email,
                AuthSession.is_active == True,
            ).first()

            if not session:
                return False

            session.is_active = False
            session.is_valid = False
            db.commit()

            logger.warning(f"Session invalidated for {email}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to invalidate session for {email}: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_session_info(email: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata (email, country, cookie count, expiry).

        Returns:
            Dict with session info or None
        """
        db = SessionLocal()
        try:
            session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.email == email,
                AuthSession.is_active == True,
            ).first()

            if not session:
                return None

            cookies_count = 0
            if session.cookies_json:
                try:
                    cookies = json.loads(decrypt_data(session.cookies_json))
                    cookies_count = len(cookies)
                except Exception:
                    pass

            return {
                "email": session.email,
                "country": session.country_code or "eg",
                "cookies_count": cookies_count,
                "is_valid": session.is_valid,
                "last_verified_at": session.last_verified_at.isoformat() if session.last_verified_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "seller_name": session.seller_name,
            }

        except Exception as e:
            logger.error(f"Failed to get session info for {email}: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def list_active_sessions() -> List[Dict[str, Any]]:
        """
        List all active browser sessions.

        Returns:
            List of session info dicts
        """
        db = SessionLocal()
        try:
            sessions = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.is_active == True,
                AuthSession.is_valid == True,
            ).all()

            result = []
            for session in sessions:
                cookies_count = 0
                if session.cookies_json:
                    try:
                        cookies = json.loads(decrypt_data(session.cookies_json))
                        cookies_count = len(cookies)
                    except Exception:
                        pass

                result.append({
                    "email": session.email,
                    "country": session.country_code or "eg",
                    "cookies_count": cookies_count,
                    "last_verified_at": session.last_verified_at.isoformat() if session.last_verified_at else None,
                    "seller_name": session.seller_name,
                })

            logger.info(f"Active sessions: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Failed to list active sessions: {e}")
            return []
        finally:
            db.close()
