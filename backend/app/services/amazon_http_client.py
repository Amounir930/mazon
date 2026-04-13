"""
Amazon HTTP Client with TLS Fingerprint Impersonation
====================================================

This module provides a production-ready HTTP client for Amazon Seller Central
API requests with:

1. **TLS Fingerprint Impersonation** via `curl_cffi` (impersonates Chrome 131)
2. **Proper CookieJar management** (RFC 6265 compliant)
3. **Session persistence** (connection reuse, cookie auto-management)
4. **Domain rewriting** (.amazon.com → .amazon.{country})

Why not niquests?
- niquests has a detectable TLS fingerprint → Amazon WAF blocks it
- curl_cffi uses BoringSSL (same as Chrome) → undetectable

Why CookieJar?
- Raw cookie strings break RFC 6265 semantics (domain/path matching)
- CookieJar handles cookies correctly per URL, like a real browser

IMPORTANT: This client is for API requests ONLY. Login must still use Playwright.
"""
import json
from http.cookiejar import CookieJar, Cookie
from typing import List, Dict, Any, Optional
from loguru import logger

from curl_cffi import requests as cffi_requests

# =============================================
# Centralized User-Agent (MUST match everywhere)
# =============================================
AMAZON_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# =============================================
# Browser Headers Template (for curl_cffi/requests)
# =============================================
BROWSER_HEADERS_TEMPLATE = {
    "User-Agent": AMAZON_USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def get_browser_headers(origin: str, referer: str) -> dict:
    """
    Get browser headers with dynamic Origin and Referer.

    Args:
        origin: e.g. "https://sellercentral.amazon.eg"
        referer: e.g. "https://sellercentral.amazon.eg/hz/merchant-listings/add-product.html"

    Returns:
        Headers dict ready for curl_cffi/requests
    """
    headers = BROWSER_HEADERS_TEMPLATE.copy()
    headers["Origin"] = origin
    headers["Referer"] = referer
    return headers


class AmazonCookieJar:
    """
    RFC 6265 compliant cookie jar for Amazon Seller Central cookies.

    Converts a list of cookie dicts (from DB) into proper Cookie objects
    with correct domain, path, secure, and HttpOnly attributes.
    """

    def __init__(self, cookies: List[Dict[str, Any]], country_code: str = "eg"):
        self.cookies_list = cookies
        self.country_code = country_code.lower()
        self.jar = CookieJar()
        self._populate()

    def _populate(self):
        """Convert cookie list into CookieJar with proper attributes."""
        if not self.cookies_list:
            logger.warning("No cookies provided to AmazonCookieJar")
            return

        # Domain mapping for country-specific rewrites
        domain_map = {
            "eg": ".amazon.eg",
            "sa": ".amazon.sa",
            "ae": ".amazon.ae",
            "uk": ".amazon.co.uk",
            "us": ".amazon.com",
            "de": ".amazon.de",
            "fr": ".amazon.fr",
            "it": ".amazon.it",
            "es": ".amazon.es",
        }
        target_domain = domain_map.get(self.country_code, ".amazon.eg")

        injected = 0
        skipped = 0

        for c in self.cookies_list:
            try:
                name = c.get("name", "")
                value = c.get("value", "")

                if not name:
                    skipped += 1
                    logger.warning(f"SKIP (no name): {c}")
                    continue

                if value is None:
                    skipped += 1
                    logger.warning(f"SKIP (value is None): {name}")
                    continue

                # Force empty string values to be valid
                if value == "":
                    value = ""

                # Rewrite domain from .amazon.com to country-specific
                cookie_domain = c.get("domain", f".amazon.{self.country_code}")
                original_domain = cookie_domain

                if cookie_domain == ".amazon.com" and self.country_code != "us":
                    cookie_domain = target_domain

                # Ensure domain starts with .
                if not cookie_domain.startswith("."):
                    cookie_domain = f".{cookie_domain}"

                http_cookie = Cookie(
                    version=0,
                    name=name,
                    value=str(value),
                    port=None,
                    port_specified=False,
                    domain=cookie_domain,
                    domain_specified=True,
                    domain_initial_dot=True,
                    path=c.get("path", "/") or "/",
                    path_specified=True,
                    secure=bool(c.get("secure", False)),
                    expires=None,       # ← was missing!
                    discard=True,
                    comment=None,       # ← was missing!
                    comment_url=None,   # ← was missing!
                    rest={"HttpOnly": c.get("httpOnly", c.get("httpOnly", None))},
                    rfc2109=False,
                )
                self.jar.set_cookie(http_cookie)
                injected += 1

            except Exception as e:
                skipped += 1
                # Use WARNING level so we can see WHY cookies are skipped
                import traceback
                logger.warning(f"SKIP (exception) '{c.get('name', '?')}': {type(e).__name__}: {e}")

        logger.info(f"AmazonCookieJar: {injected} cookies loaded, {skipped} skipped (country: {self.country_code})")

    def get_jar(self) -> CookieJar:
        """Return the populated CookieJar."""
        return self.jar

    def count(self) -> int:
        """Return number of cookies in the jar."""
        return len(list(self.jar))


class AmazonHTTPClient:
    """
    Production HTTP client for Amazon Seller Central API requests.

    Features:
    - TLS fingerprint impersonation (Chrome 131 via curl_cffi)
    - CookieJar-based cookie management (RFC 6265)
    - Session persistence (connection reuse)
    - Automatic CSRF token extraction

    Usage:
        client = AmazonHTTPClient(cookies, country_code="eg")
        response = client.get("/inventory")
        response = client.post("/abis/ajax/create-listing", data=...)
    """

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

    def __init__(self, cookies: List[Dict[str, Any]], country_code: str = "eg"):
        self.country_code = country_code.lower()
        self.base_url = self.SELLER_CENTRAL_BASE.get(
            self.country_code, self.SELLER_CENTRAL_BASE["eg"]
        )

        # Build CookieJar
        self.cookie_jar = AmazonCookieJar(cookies, self.country_code)

        # Create curl_cffi session with TLS impersonation
        self.session = cffi_requests.Session(
            impersonate="chrome131",  # MUST match the User-Agent Chrome version
            timeout=30.0,
        )

        # Set cookies on the session
        self.session.cookies = self.cookie_jar.get_jar()

        # Set default headers
        self.session.headers.update({
            "User-Agent": AMAZON_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })

        logger.info(f"AmazonHTTPClient initialized: {self.base_url} ({self.cookie_jar.count()} cookies, TLS: chrome131)")

    def get(self, url: str, **kwargs) -> cffi_requests.Response:
        """Make a GET request with proper base URL."""
        full_url = self._build_url(url)
        logger.debug(f"GET {full_url}")
        response = self.session.get(full_url, **kwargs)
        self._check_response(response)
        return response

    def post(self, url: str, **kwargs) -> cffi_requests.Response:
        """Make a POST request with proper base URL."""
        full_url = self._build_url(url)
        logger.debug(f"POST {full_url}")
        response = self.session.post(full_url, **kwargs)
        self._check_response(response)
        return response

    def _build_url(self, url: str) -> str:
        """Build full URL from relative path."""
        if url.startswith("http"):
            return url
        return f"{self.base_url}{url}"

    def _check_response(self, response: cffi_requests.Response):
        """Check for session expiration (redirect to login)."""
        final_url = str(response.url)
        if "/ap/signin" in final_url or "/gp/signin" in final_url:
            logger.warning(f"⚠️ Session expired — redirected to login: {final_url[:80]}")
            raise SessionExpiredError(f"Session expired: redirected to {final_url[:80]}")

    def is_session_valid(self) -> bool:
        """Quick check if session is still valid by hitting home page."""
        try:
            response = self.session.get(f"{self.base_url}/home", allow_redirects=True, timeout=10)
            final_url = str(response.url)
            return "/ap/signin" not in final_url and "/gp/signin" not in final_url
        except Exception as e:
            logger.debug(f"Session validity check failed: {e}")
            return False

    def extract_csrf_from_response(self, html: str) -> Optional[str]:
        """Extract CSRF token from HTML response."""
        from app.services.playwright_login import extract_csrf_token
        return extract_csrf_token(html)

    def fetch_csrf_token(self) -> Optional[str]:
        """Fetch a fresh CSRF token from a safe page."""
        urls_to_try = [
            f"{self.base_url}/product-search/search",
            f"{self.base_url}/product-search",
            f"{self.base_url}/home",
        ]

        for url in urls_to_try:
            try:
                logger.debug(f"Fetching CSRF from: {url}")
                response = self.session.get(url, allow_redirects=True, timeout=15)

                if response.status_code == 200:
                    token = self.extract_csrf_from_response(response.text)
                    if token:
                        logger.info(f"✅ CSRF token fetched: {token[:20]}... ({len(token)} chars)")
                        return token
            except SessionExpiredError:
                raise
            except Exception as e:
                logger.debug(f"CSRF fetch failed from {url}: {e}")

        logger.error("❌ Failed to fetch CSRF token from any page")
        return None

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.debug("AmazonHTTPClient session closed")


class SessionExpiredError(Exception):
    """Raised when Amazon redirects to login page (session expired)."""
    pass
