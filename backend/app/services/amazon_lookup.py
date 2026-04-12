"""
Amazon Product Lookup Service
بيبحث في Amazon عن طريق ASIN/UPC/EAN قبل إضافة المنتج
لو المنتج موجود → بيرفض الحفظ ويبلغ المستخدم
"""
import json
from typing import Optional, Dict, Any
from loguru import logger

import niquests as requests

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}


class AmazonProductLookup:
    """بيبحث في Amazon عن طريق ASIN/UPC/EAN"""

    def __init__(self, email: str = "amazon_eg"):
        self.email = email
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)
        self._authenticated = False

    def _setup_session(self) -> bool:
        """يجهز الجلسة بالـ cookies"""
        db = SessionLocal()
        try:
            auth_session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.email == self.email,
                AuthSession.is_active == True,
                AuthSession.is_valid == True,
            ).first()

            if not auth_session or not auth_session.cookies_json:
                return False

            cookies = json.loads(decrypt_data(auth_session.cookies_json))
            country = auth_session.country_code or "eg"

            domain_map = {"eg": ".amazon.eg", "sa": ".amazon.sa", "ae": ".amazon.ae"}
            target_domain = domain_map.get(country, ".amazon.eg")

            for cookie in cookies:
                try:
                    cookie_domain = cookie.get("domain", ".amazon.com")
                    if cookie_domain == ".amazon.com" and country != "us":
                        cookie_domain = target_domain
                    self.session.cookies.set(
                        cookie["name"], cookie["value"],
                        domain=cookie_domain, path=cookie.get("path", "/"),
                    )
                except:
                    pass

            self._authenticated = True
            self.base_url = SELLER_CENTRAL_BASE.get(country, SELLER_CENTRAL_BASE["eg"])
            return True
        except:
            return False
        finally:
            db.close()

    async def lookup(self, product_id: str, id_type: str = "EAN") -> Dict[str, Any]:
        """
        يبحث في Amazon عن طريق ASIN/UPC/EAN.
        
        Returns:
            {"found": False}  → المنتج مش موجود (ممكن تضيفه)
            {"found": True, "asin": "...", "title": "..."}  → موجود (لازم ترفض)
        """
        if not self._authenticated:
            if not self._setup_session():
                return {"found": False, "error": "No session - skip lookup"}

        try:
            # Method 1: Try Amazon product page directly
            if id_type == "ASIN":
                url = f"https://www.amazon.eg/dp/{product_id}"
            else:
                # Search by UPC/EAN
                url = f"{self.base_url}/catalog/v3/search?keywords={product_id}"

            response = self.session.get(url, timeout=10, allow_redirects=True)

            # Check if we found a product
            if id_type == "ASIN":
                if response.status_code == 200 and "productTitle" in response.text:
                    import re
                    title_match = re.search(r'"productTitle"\s*:\s*"([^"]+)"', response.text)
                    return {
                        "found": True,
                        "asin": product_id,
                        "title": title_match.group(1) if title_match else "Unknown",
                    }
            else:
                # Search results
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results = data.get("results", [])
                        if results:
                            return {
                                "found": True,
                                "asin": results[0].get("asin", ""),
                                "title": results[0].get("title", "Unknown"),
                            }
                    except:
                        # HTML fallback
                        if "No results found" not in response.text and len(response.text) > 1000:
                            import re
                            asin_match = re.search(r'/dp/(B[0-9A-Z]{9})', response.text)
                            if asin_match:
                                return {"found": True, "asin": asin_match.group(1)}

            return {"found": False}

        except Exception as e:
            logger.debug(f"Amazon lookup failed for {product_id}: {e}")
            return {"found": False, "error": str(e)}
