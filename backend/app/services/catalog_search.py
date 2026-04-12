"""
Amazon Catalog Search API Client
يستخدم niquests + BeautifulSoup للبحث في كتالوج Amazon
"""
import json
import re
from typing import List, Dict, Any, Optional
from loguru import logger

import niquests
from bs4 import BeautifulSoup

from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data


class AmazonCatalogSearchClient:
    """
    عميل للبحث في كتالوج Amazon باستخدام niquests + BeautifulSoup.
    بيستخدم الـ Cookies المحفوظة لطلب صفحات Amazon مباشرة.
    """

    BASE_URLS = {
        "eg": "https://sellercentral.amazon.eg",
        "sa": "https://sellercentral.amazon.sa",
        "ae": "https://sellercentral.amazon.ae",
        "uk": "https://sellercentral.amazon.co.uk",
        "us": "https://sellercentral.amazon.com",
    }

    def __init__(self, country_code: str = "eg"):
        self.country_code = country_code
        self.base_url = self.BASE_URLS.get(country_code, self.BASE_URLS["eg"])
        self.session = niquests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
        })

    def setup_cookies(self, cookies: List[Dict[str, Any]]):
        """يضيف الـ Cookies للـ Session"""
        for cookie in cookies:
            self.session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain", f".amazon.{self.country_code}"),
                path=cookie.get("path", "/"),
            )
        logger.info(f"Setup {len(cookies)} cookies for catalog search")

    def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        البحث في الكتالوج بكلمة مفتاحية.
        بيطلب صفحة البحث وبيحلل الـ HTML لاستخراج المنتجات.
        """
        try:
            search_url = f"{self.base_url}/product-search/keywords/search"
            params = {"q": keyword}

            logger.info(f"Searching: {search_url}?q={keyword}")
            response = self.session.get(search_url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Search failed: {response.status_code}")
                return []

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple strategies to extract products
            products = self._extract_products_v1(soup)

            if not products:
                products = self._extract_products_v2(soup)

            if not products:
                products = self._extract_products_v3(soup)

            logger.info(f"Extracted {len(products)} products from search results")
            return products[:20]  # Limit to 20 results

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return []

    def _extract_products_v1(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Strategy 1: Look for product cards with data-testid"""
        products = []

        # Try to find product containers
        selectors = [
            '[data-testid*="product"]',
            '.product-item',
            '[class*="product-card"]',
            '[class*="result-item"]',
            '[class*="search-result"]',
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"Found {len(items)} items with selector: {selector}")
                for item in items[:20]:
                    product = self._parse_product_item(item)
                    if product:
                        products.append(product)
                break

        return products

    def _extract_products_v2(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Strategy 2: Look for list items in a table or list"""
        products = []

        # Try to find rows in a table
        rows = soup.select('table tbody tr, [role="row"], .data-grid-row')
        if rows:
            logger.info(f"Found {len(rows)} table rows")
            for row in rows[:20]:
                cells = row.find_all(['td', 'th', '[role="gridcell"]'])
                if len(cells) >= 3:
                    product = self._parse_table_row(cells)
                    if product:
                        products.append(product)

        return products

    def _extract_products_v3(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Strategy 3: Look for embedded JSON data in the page"""
        products = []

        # Try to find JSON data embedded in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for JSON patterns
                json_patterns = [
                    r'(\{[^}]*"products"[^}]*\})',
                    r'(\{[^}]*"results"[^}]*\})',
                    r'(\{[^}]*"items"[^}]*\})',
                    r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
                ]

                for pattern in json_patterns:
                    matches = re.findall(pattern, script.string, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict):
                                items = data.get('products', data.get('results', data.get('items', [])))
                                if isinstance(items, list):
                                    products.extend(items)
                        except json.JSONDecodeError:
                            continue

        return products

    def _parse_product_item(self, item) -> Optional[Dict[str, Any]]:
        """Parse a single product item element"""
        try:
            title_elem = item.select_one('h3, [class*="title"], [class*="name"], a')
            asin_elem = item.select_one('[data-asin]')
            price_elem = item.select_one('[class*="price"]')
            img_elem = item.select_one('img')
            brand_elem = item.select_one('[class*="brand"]')

            title = title_elem.get_text(strip=True) if title_elem else ''
            asin = asin_elem.get('data-asin', '') if asin_elem else ''
            price = price_elem.get_text(strip=True) if price_elem else ''
            image = img_elem.get('src', '') if img_elem else ''
            brand = brand_elem.get_text(strip=True) if brand_elem else ''

            if title or asin:
                return {
                    'title': title,
                    'asin': asin,
                    'price': price,
                    'image': image,
                    'brand': brand,
                    'url': f"https://www.amazon.{self.country_code}/dp/{asin}" if asin else '',
                }
        except Exception as e:
            logger.debug(f"Error parsing product item: {e}")

        return None

    def _parse_table_row(self, cells) -> Optional[Dict[str, Any]]:
        """Parse a table row into product data"""
        try:
            product = {}

            for cell in cells:
                text = cell.get_text(strip=True)
                if not text:
                    continue

                # ASIN: B0XXXXXXXX
                if re.match(r'^B[0-9A-Z]{9}$', text):
                    product['asin'] = text
                # SKU pattern
                elif re.match(r'^[A-Z0-9]+-[A-Z0-9]+', text):
                    product['sku'] = text
                # Price
                elif re.search(r'[\d,]+\.?\d*', text) and not product.get('price'):
                    product['price'] = text
                # Title (long text)
                elif len(text) > 10 and len(text) < 200 and not product.get('title'):
                    product['title'] = text

            if product.get('title') or product.get('asin'):
                return product

        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")

        return None

    def search_by_asin(self, asin: str) -> Optional[Dict[str, Any]]:
        """
        البحث عن منتج محدد بواسطة ASIN.
        """
        results = self.search_by_keyword(asin)
        # Filter for exact ASIN match
        for product in results:
            if product.get('asin') == asin:
                return product
        return results[0] if results else None


def get_active_session():
    """يجيب الـ Session النشطة من الـ Database"""
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

        logger.info(f"Retrieved session for catalog search (country: {country}, cookies: {len(cookies)})")
        return cookies, country

    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        return None, None
    finally:
        db.close()
